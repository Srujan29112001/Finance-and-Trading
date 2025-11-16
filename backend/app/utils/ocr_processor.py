"""
OCR Processor for Financial Documents

Extracts text from PDFs and images of financial reports, earnings statements,
and other documents using Tesseract OCR and PDF processing libraries.
"""

import io
import os
from typing import Dict, List, Optional, Union
from pathlib import Path
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
import pypdf
from loguru import logger
import re
from dataclasses import dataclass
import asyncio


@dataclass
class DocumentPage:
    """Represents a page of an extracted document"""
    page_number: int
    text: str
    confidence: Optional[float] = None
    image_path: Optional[str] = None


@dataclass
class ExtractedDocument:
    """Complete extracted document with metadata"""
    filename: str
    total_pages: int
    pages: List[DocumentPage]
    full_text: str
    metadata: Dict[str, any]


class OCRProcessor:
    """
    Handles OCR processing for financial documents

    Supports:
    - PDF text extraction (native and OCR-based)
    - Image-to-text conversion
    - Financial data parsing
    - Multi-page document handling
    """

    def __init__(
        self,
        tesseract_path: Optional[str] = None,
        temp_dir: str = "/tmp/ocr_processing"
    ):
        """
        Initialize OCR processor

        Args:
            tesseract_path: Path to Tesseract executable (if not in PATH)
            temp_dir: Directory for temporary files
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True, parents=True)

        logger.info(f"OCR Processor initialized with temp dir: {self.temp_dir}")

    async def extract_from_pdf(
        self,
        pdf_path: Union[str, Path, bytes],
        use_ocr: bool = False,
        dpi: int = 300
    ) -> ExtractedDocument:
        """
        Extract text from PDF

        Args:
            pdf_path: Path to PDF file or PDF bytes
            use_ocr: Force OCR even if PDF has embedded text
            dpi: DPI for image conversion (higher = better quality, slower)

        Returns:
            ExtractedDocument with all extracted content
        """
        logger.info(f"Processing PDF: {pdf_path}")

        # Try native text extraction first (faster)
        if not use_ocr:
            try:
                native_result = await self._extract_native_pdf_text(pdf_path)
                if native_result and self._has_meaningful_content(native_result.full_text):
                    logger.info("Successfully extracted text natively from PDF")
                    return native_result
            except Exception as e:
                logger.warning(f"Native PDF extraction failed: {e}, falling back to OCR")

        # Fall back to OCR if native extraction fails or is forced
        return await self._extract_ocr_pdf_text(pdf_path, dpi)

    async def _extract_native_pdf_text(
        self,
        pdf_path: Union[str, Path, bytes]
    ) -> ExtractedDocument:
        """Extract text from PDF using built-in text (no OCR)"""
        if isinstance(pdf_path, bytes):
            pdf_file = io.BytesIO(pdf_path)
        else:
            pdf_file = open(pdf_path, 'rb')

        try:
            reader = pypdf.PdfReader(pdf_file)
            pages = []

            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                pages.append(DocumentPage(
                    page_number=page_num,
                    text=text,
                    confidence=1.0  # Native text has perfect confidence
                ))

            full_text = "\n\n".join(p.text for p in pages)

            # Extract metadata
            metadata = {}
            if reader.metadata:
                metadata = {
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                }

            filename = pdf_path if isinstance(pdf_path, str) else "uploaded_pdf"

            return ExtractedDocument(
                filename=filename,
                total_pages=len(pages),
                pages=pages,
                full_text=full_text,
                metadata=metadata
            )

        finally:
            if not isinstance(pdf_path, bytes):
                pdf_file.close()

    async def _extract_ocr_pdf_text(
        self,
        pdf_path: Union[str, Path, bytes],
        dpi: int = 300
    ) -> ExtractedDocument:
        """Extract text from PDF using OCR (for scanned documents)"""
        logger.info("Converting PDF to images for OCR processing")

        # Convert PDF to images
        if isinstance(pdf_path, bytes):
            images = convert_from_bytes(pdf_path, dpi=dpi)
            filename = "uploaded_pdf"
        else:
            images = convert_from_path(pdf_path, dpi=dpi)
            filename = str(pdf_path)

        # Process each page
        pages = []
        for page_num, image in enumerate(images, start=1):
            logger.info(f"OCR processing page {page_num}/{len(images)}")
            page_data = await self._ocr_image(image)
            pages.append(DocumentPage(
                page_number=page_num,
                text=page_data["text"],
                confidence=page_data["confidence"]
            ))

        full_text = "\n\n".join(p.text for p in pages)

        return ExtractedDocument(
            filename=filename,
            total_pages=len(pages),
            pages=pages,
            full_text=full_text,
            metadata={"extraction_method": "OCR", "dpi": dpi}
        )

    async def extract_from_image(
        self,
        image_path: Union[str, Path, bytes, Image.Image]
    ) -> Dict[str, any]:
        """
        Extract text from an image

        Args:
            image_path: Path to image, bytes, or PIL Image

        Returns:
            Dictionary with text and confidence score
        """
        if isinstance(image_path, (str, Path)):
            image = Image.open(image_path)
        elif isinstance(image_path, bytes):
            image = Image.open(io.BytesIO(image_path))
        else:
            image = image_path

        return await self._ocr_image(image)

    async def _ocr_image(self, image: Image.Image) -> Dict[str, any]:
        """
        Perform OCR on a PIL Image

        Returns:
            Dict with 'text' and 'confidence' keys
        """
        # Run OCR in thread pool to avoid blocking
        loop = asyncio.get_event_loop()

        # Get detailed OCR data with confidence scores
        ocr_data = await loop.run_in_executor(
            None,
            lambda: pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT
            )
        )

        # Extract text
        text = await loop.run_in_executor(
            None,
            lambda: pytesseract.image_to_string(image)
        )

        # Calculate average confidence
        confidences = [
            int(conf) for conf in ocr_data['conf']
            if conf != '-1'
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return {
            "text": text.strip(),
            "confidence": avg_confidence / 100.0  # Normalize to 0-1
        }

    def parse_financial_data(self, text: str) -> Dict[str, any]:
        """
        Parse financial metrics from extracted text

        Looks for common patterns like:
        - Revenue: $XXX million
        - EPS: $X.XX
        - P/E Ratio: XX.X
        - etc.

        Args:
            text: Extracted text from document

        Returns:
            Dictionary of parsed financial metrics
        """
        metrics = {}

        # Revenue patterns
        revenue_patterns = [
            r'revenue[:\s]+\$?([\d,\.]+)\s*(million|billion|M|B)?',
            r'sales[:\s]+\$?([\d,\.]+)\s*(million|billion|M|B)?',
        ]

        for pattern in revenue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(',', ''))
                unit = match.group(2).lower() if match.group(2) else ''
                if unit in ['billion', 'b']:
                    value *= 1000
                metrics['revenue_millions'] = value
                break

        # EPS pattern
        eps_match = re.search(r'eps[:\s]+\$?([\d\.]+)', text, re.IGNORECASE)
        if eps_match:
            metrics['eps'] = float(eps_match.group(1))

        # Net income
        ni_match = re.search(
            r'net\s+income[:\s]+\$?([\d,\.]+)\s*(million|billion|M|B)?',
            text,
            re.IGNORECASE
        )
        if ni_match:
            value = float(ni_match.group(1).replace(',', ''))
            unit = ni_match.group(2).lower() if ni_match.group(2) else ''
            if unit in ['billion', 'b']:
                value *= 1000
            metrics['net_income_millions'] = value

        # P/E Ratio
        pe_match = re.search(r'p/e\s+ratio[:\s]+([\d\.]+)', text, re.IGNORECASE)
        if pe_match:
            metrics['pe_ratio'] = float(pe_match.group(1))

        # Market Cap
        mc_match = re.search(
            r'market\s+cap(?:italization)?[:\s]+\$?([\d,\.]+)\s*(million|billion|trillion|M|B|T)?',
            text,
            re.IGNORECASE
        )
        if mc_match:
            value = float(mc_match.group(1).replace(',', ''))
            unit = mc_match.group(2).lower() if mc_match.group(2) else ''
            if unit in ['billion', 'b']:
                value *= 1000
            elif unit in ['trillion', 't']:
                value *= 1000000
            metrics['market_cap_millions'] = value

        # Extract quarter/year info
        quarter_match = re.search(r'Q([1-4])\s+(\d{4})', text)
        if quarter_match:
            metrics['quarter'] = int(quarter_match.group(1))
            metrics['year'] = int(quarter_match.group(2))

        return metrics

    def _has_meaningful_content(self, text: str, min_chars: int = 100) -> bool:
        """Check if extracted text has meaningful content"""
        if not text or len(text.strip()) < min_chars:
            return False

        # Check if text is mostly gibberish/symbols
        alpha_ratio = sum(c.isalpha() for c in text) / len(text)
        return alpha_ratio > 0.5

    async def batch_process_pdfs(
        self,
        pdf_paths: List[Union[str, Path]],
        use_ocr: bool = False
    ) -> List[ExtractedDocument]:
        """
        Process multiple PDFs concurrently

        Args:
            pdf_paths: List of PDF file paths
            use_ocr: Force OCR for all documents

        Returns:
            List of ExtractedDocument objects
        """
        tasks = [
            self.extract_from_pdf(pdf_path, use_ocr=use_ocr)
            for pdf_path in pdf_paths
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        documents = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing {pdf_paths[i]}: {result}")
            else:
                documents.append(result)

        return documents

    def cleanup_temp_files(self):
        """Remove temporary files created during processing"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(exist_ok=True, parents=True)
            logger.info("Cleaned up temporary OCR files")


# Singleton instance
_ocr_processor_instance: Optional[OCRProcessor] = None


def get_ocr_processor() -> OCRProcessor:
    """Get or create OCR processor singleton"""
    global _ocr_processor_instance
    if _ocr_processor_instance is None:
        _ocr_processor_instance = OCRProcessor()
    return _ocr_processor_instance
