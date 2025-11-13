"""
VLM (Vision Language Model) API Endpoints
For analyzing stock charts visually
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from PIL import Image
import io
from loguru import logger

from app.agents.vlm_agent import get_vlm_agent
from app.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class ChartAnalysisRequest(BaseModel):
    symbol: str
    chart_type: str = "candlestick"  # or "technical"
    prompt: Optional[str] = None
    model: str = "llava"  # llava, blip2, gpt4-vision


class ChartAnalysisResponse(BaseModel):
    symbol: str
    chart_type: str
    model: str
    interpretation: str
    timestamp: str
    data_points: Optional[int] = None


@router.post("/analyze-chart", response_model=ChartAnalysisResponse)
async def analyze_chart_from_data(
    request: ChartAnalysisRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate a chart from market data and analyze it with VLM.

    This endpoint:
    1. Fetches recent price data for the symbol
    2. Generates a chart image
    3. Analyzes the chart using a Vision Language Model
    4. Returns detailed interpretation

    Example request:
    ```json
    {
        "symbol": "AAPL",
        "chart_type": "candlestick",
        "model": "llava",
        "prompt": "What patterns do you see in this chart?"
    }
    ```
    """
    try:
        # Get VLM agent
        vlm_agent = get_vlm_agent(model_name=request.model)

        # Fetch price data
        from app.models.market import StockPrice
        from sqlalchemy import select

        query = select(StockPrice).where(
            StockPrice.symbol == request.symbol.upper()
        ).order_by(StockPrice.timestamp.desc()).limit(100)

        result = await db.execute(query)
        prices = result.scalars().all()

        if not prices:
            raise HTTPException(
                status_code=404,
                detail=f"No price data found for {request.symbol}"
            )

        # Convert to dict format
        price_data = [
            {
                "timestamp": p.timestamp,
                "open": float(p.open),
                "high": float(p.high),
                "low": float(p.low),
                "close": float(p.close),
                "volume": int(p.volume)
            }
            for p in reversed(prices)  # Chronological order
        ]

        # Analyze with VLM
        analysis = await vlm_agent.analyze_from_data(
            price_data=price_data,
            symbol=request.symbol,
            chart_type=request.chart_type,
            prompt=request.prompt
        )

        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])

        return ChartAnalysisResponse(
            symbol=request.symbol,
            chart_type=request.chart_type,
            model=analysis.get("model", request.model),
            interpretation=analysis.get("interpretation", ""),
            timestamp=analysis.get("timestamp", datetime.utcnow().isoformat()),
            data_points=analysis.get("data_points")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-uploaded-chart")
async def analyze_uploaded_chart(
    file: UploadFile = File(...),
    model: str = "llava",
    prompt: Optional[str] = None
):
    """
    Upload a chart image and analyze it with VLM.

    Upload any stock chart image (PNG, JPG) and get AI analysis.

    Example usage:
    ```bash
    curl -X POST http://localhost:8000/api/vlm/analyze-uploaded-chart \
      -F "file=@chart.png" \
      -F "model=llava" \
      -F "prompt=Analyze this chart"
    ```
    """
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Get VLM agent
        vlm_agent = get_vlm_agent(model_name=model)

        # Analyze
        analysis = await vlm_agent.analyze_chart(
            chart_image=image,
            prompt=prompt
        )

        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])

        return {
            "filename": file.filename,
            "model": analysis.get("model", model),
            "interpretation": analysis.get("interpretation", ""),
            "timestamp": analysis.get("timestamp", datetime.utcnow().isoformat())
        }

    except Exception as e:
        logger.error(f"Error analyzing uploaded chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_vlm_models():
    """
    List available VLM models.

    Returns information about which vision models can be used
    for chart analysis.
    """
    return {
        "available_models": [
            {
                "name": "llava",
                "description": "LLaVA 1.5 - Open-source VLM, runs locally",
                "size": "7B parameters (4-bit quantized)",
                "pros": ["Free", "Privacy", "Good quality"],
                "cons": ["Requires GPU", "Slower than API"],
                "recommended": True
            },
            {
                "name": "blip2",
                "description": "BLIP-2 - Lightweight vision model",
                "size": "2.7B parameters",
                "pros": ["Fast", "Low memory", "Free"],
                "cons": ["Less detailed analysis"],
                "recommended": False
            },
            {
                "name": "gpt4-vision",
                "description": "GPT-4 Vision - Best quality, requires API",
                "size": "Cloud API",
                "pros": ["Best quality", "Fast", "No local GPU needed"],
                "cons": ["Costs money", "Requires API key", "Privacy concerns"],
                "recommended": True
            }
        ],
        "default": "llava",
        "setup_instructions": {
            "llava": "Model downloads automatically on first use (~4GB)",
            "gpt4-vision": "Set OPENAI_API_KEY in .env file"
        }
    }


@router.get("/capabilities")
async def get_vlm_capabilities():
    """Get information about VLM capabilities."""
    return {
        "features": {
            "chart_analysis": "Interpret candlestick and technical charts",
            "pattern_recognition": "Identify chart patterns (head & shoulders, triangles, etc.)",
            "trend_analysis": "Determine bullish/bearish trends",
            "support_resistance": "Identify key levels",
            "volume_analysis": "Analyze volume patterns",
            "recommendations": "Provide trading recommendations based on visuals"
        },
        "supported_chart_types": [
            "candlestick",
            "technical (with indicators)",
            "uploaded images"
        ],
        "use_cases": [
            "Quick visual analysis of multiple charts",
            "Pattern detection for trading strategies",
            "Educational: Learn chart reading",
            "Automated chart screening"
        ]
    }
