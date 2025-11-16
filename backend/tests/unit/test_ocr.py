"""
Unit tests for OCR functionality
"""

import pytest
from app.utils.ocr_processor import OCRProcessor, get_ocr_processor


class TestOCRProcessor:
    """Test OCR text extraction functionality"""

    @pytest.fixture
    def ocr_processor(self):
        """Create OCR processor instance"""
        return get_ocr_processor()

    def test_ocr_processor_initialization(self, ocr_processor):
        """Test OCR processor initializes correctly"""
        assert ocr_processor is not None
        assert ocr_processor.temp_dir.exists()

    def test_financial_data_parsing(self, ocr_processor):
        """Test parsing of financial metrics from text"""
        sample_text = """
        Apple Inc. Q3 2024 Earnings Report

        Revenue: $85.5 billion
        Net Income: $21.4 billion
        EPS: $1.30
        P/E Ratio: 28.5
        Market Cap: $2.8 trillion
        """

        metrics = ocr_processor.parse_financial_data(sample_text)

        assert "revenue_millions" in metrics
        assert metrics["revenue_millions"] == 85500.0

        assert "net_income_millions" in metrics
        assert metrics["net_income_millions"] == 21400.0

        assert "eps" in metrics
        assert metrics["eps"] == 1.30

        assert "pe_ratio" in metrics
        assert metrics["pe_ratio"] == 28.5

    def test_has_meaningful_content(self, ocr_processor):
        """Test content quality detection"""
        # Good content
        good_text = "This is a meaningful financial report with substantial text content."
        assert ocr_processor._has_meaningful_content(good_text)

        # Bad content (too short)
        bad_text = "abc"
        assert not ocr_processor._has_meaningful_content(bad_text)

        # Bad content (mostly symbols)
        bad_text = "!!!@@@###$$$%%%"
        assert not ocr_processor._has_meaningful_content(bad_text)

    def test_quarter_year_extraction(self, ocr_processor):
        """Test extraction of quarter and year from text"""
        text = "Financial results for Q3 2024"
        metrics = ocr_processor.parse_financial_data(text)

        assert "quarter" in metrics
        assert metrics["quarter"] == 3

        assert "year" in metrics
        assert metrics["year"] == 2024
