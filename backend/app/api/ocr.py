"""
OCR API Endpoints

Provides endpoints for document processing and text extraction from
financial PDFs and images.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from app.utils.ocr_processor import get_ocr_processor


router = APIRouter()


class OCRResult(BaseModel):
    """OCR extraction result"""
    filename: str
    total_pages: int
    full_text: str
    pages: List[dict]
    metadata: dict
    financial_metrics: Optional[dict] = None


class ImageOCRResult(BaseModel):
    """Single image OCR result"""
    text: str
    confidence: float


@router.post("/extract/pdf", response_model=OCRResult)
async def extract_text_from_pdf(
    file: UploadFile = File(...),
    use_ocr: bool = Query(False, description="Force OCR even if PDF has embedded text"),
    parse_financials: bool = Query(True, description="Parse financial metrics from text"),
    dpi: int = Query(300, description="DPI for OCR (higher = better quality, slower)")
):
    """
    Extract text from a PDF document

    **Process:**
    1. Attempts native text extraction first (fast)
    2. Falls back to OCR if native extraction fails
    3. Optionally parses financial metrics from extracted text

    **Supported:**
    - Native PDFs with embedded text
    - Scanned PDFs (images)
    - Multi-page documents
    - Financial reports, earnings statements, etc.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        # Read file contents
        contents = await file.read()

        # Process PDF
        ocr_processor = get_ocr_processor()
        result = await ocr_processor.extract_from_pdf(
            contents,
            use_ocr=use_ocr,
            dpi=dpi
        )

        # Parse financial metrics if requested
        financial_metrics = None
        if parse_financials:
            financial_metrics = ocr_processor.parse_financial_data(result.full_text)

        # Convert to response model
        return OCRResult(
            filename=result.filename,
            total_pages=result.total_pages,
            full_text=result.full_text,
            pages=[
                {
                    "page_number": page.page_number,
                    "text": page.text,
                    "confidence": page.confidence
                }
                for page in result.pages
            ],
            metadata=result.metadata,
            financial_metrics=financial_metrics
        )

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@router.post("/extract/image", response_model=ImageOCRResult)
async def extract_text_from_image(
    file: UploadFile = File(...)
):
    """
    Extract text from an image

    **Supported formats:**
    - PNG, JPG, JPEG, GIF, BMP, TIFF
    - Screenshots of financial data
    - Charts and graphs with text

    **Use cases:**
    - Extract data from chart screenshots
    - Process images of financial documents
    - Quick text extraction from single images
    """
    # Validate image format
    allowed_formats = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif']
    if not any(file.filename.lower().endswith(fmt) for fmt in allowed_formats):
        raise HTTPException(
            status_code=400,
            detail=f"File must be an image ({', '.join(allowed_formats)})"
        )

    try:
        # Read file contents
        contents = await file.read()

        # Process image
        ocr_processor = get_ocr_processor()
        result = await ocr_processor.extract_from_image(contents)

        return ImageOCRResult(
            text=result["text"],
            confidence=result["confidence"]
        )

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@router.post("/extract/batch", response_model=List[OCRResult])
async def extract_text_from_multiple_pdfs(
    files: List[UploadFile] = File(...),
    use_ocr: bool = Query(False, description="Force OCR for all documents"),
    parse_financials: bool = Query(True, description="Parse financial metrics")
):
    """
    Extract text from multiple PDF documents concurrently

    **Benefits:**
    - Processes multiple documents in parallel
    - Faster than sequential processing
    - Ideal for batch quarterly report processing

    **Limits:**
    - Maximum 10 files per request
    - Each file must be under 10MB
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files allowed per batch request"
        )

    results = []
    ocr_processor = get_ocr_processor()

    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Skipping non-PDF file: {file.filename}")
            continue

        try:
            contents = await file.read()

            result = await ocr_processor.extract_from_pdf(
                contents,
                use_ocr=use_ocr
            )

            financial_metrics = None
            if parse_financials:
                financial_metrics = ocr_processor.parse_financial_data(result.full_text)

            results.append(OCRResult(
                filename=result.filename,
                total_pages=result.total_pages,
                full_text=result.full_text,
                pages=[
                    {
                        "page_number": page.page_number,
                        "text": page.text,
                        "confidence": page.confidence
                    }
                    for page in result.pages
                ],
                metadata=result.metadata,
                financial_metrics=financial_metrics
            ))

        except Exception as e:
            logger.error(f"Error processing {file.filename}: {e}")
            # Continue processing other files

    if not results:
        raise HTTPException(
            status_code=400,
            detail="No valid PDF files were processed"
        )

    return results


@router.get("/health")
async def ocr_health_check():
    """Check if OCR service is operational"""
    try:
        ocr_processor = get_ocr_processor()
        return {
            "status": "healthy",
            "temp_dir": str(ocr_processor.temp_dir),
            "tesseract_available": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
