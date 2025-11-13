"""
Vision Language Model (VLM) Agent for Chart Interpretation
Supports multiple VLM models: LLaVA, BLIP-2, GPT-4 Vision
"""

import os
import io
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import numpy as np
from PIL import Image
from loguru import logger

# Chart generation
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure

# Try importing VLM dependencies
try:
    from transformers import (
        AutoProcessor,
        AutoModelForVision2Seq,
        BlipProcessor,
        BlipForConditionalGeneration,
        LlavaForConditionalGeneration,
        AutoTokenizer
    )
    import torch
    HAS_VLM = True
except ImportError:
    logger.warning("VLM dependencies not installed. Install with: pip install -r requirements-vlm.txt")
    HAS_VLM = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from app.config import settings


class ChartGenerator:
    """Generate stock charts as images for VLM analysis."""

    @staticmethod
    def create_candlestick_chart(
        data: List[Dict[str, Any]],
        symbol: str,
        title: Optional[str] = None
    ) -> Image.Image:
        """
        Create a candlestick chart from price data.

        Args:
            data: List of price records with OHLC data
            symbol: Stock symbol
            title: Chart title (optional)

        Returns:
            PIL Image of the chart
        """
        if not data:
            raise ValueError("No data provided for chart generation")

        # Extract data
        timestamps = [d['timestamp'] for d in data]
        opens = [float(d['open']) for d in data]
        highs = [float(d['high']) for d in data]
        lows = [float(d['low']) for d in data]
        closes = [float(d['close']) for d in data]
        volumes = [float(d['volume']) for d in data]

        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8),
                                        gridspec_kw={'height_ratios': [3, 1]})

        # Candlestick chart
        width = 0.6
        width2 = 0.05

        # Colors: green for up, red for down
        colors = ['green' if close >= open else 'red'
                  for close, open in zip(closes, opens)]

        # Plot candlesticks
        for i in range(len(data)):
            # High-low line
            ax1.plot([i, i], [lows[i], highs[i]], color='black', linewidth=1)
            # Body
            height = abs(closes[i] - opens[i])
            bottom = min(opens[i], closes[i])
            ax1.bar(i, height, width, bottom=bottom, color=colors[i], alpha=0.8)

        # Format price chart
        ax1.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
        ax1.set_title(title or f'{symbol} Stock Price Chart', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks([])

        # Volume chart
        ax2.bar(range(len(volumes)), volumes, width=0.8,
                color=['green' if c >= o else 'red' for c, o in zip(closes, opens)],
                alpha=0.6)
        ax2.set_ylabel('Volume', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Time', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        # Format x-axis with timestamps
        if len(timestamps) > 10:
            step = len(timestamps) // 10
            indices = list(range(0, len(timestamps), step))
            labels = [timestamps[i].strftime('%H:%M') if hasattr(timestamps[i], 'strftime')
                     else str(timestamps[i]) for i in indices]
            ax2.set_xticks(indices)
            ax2.set_xticklabels(labels, rotation=45)

        plt.tight_layout()

        # Convert to PIL Image
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        image = Image.open(buf)
        plt.close(fig)

        return image

    @staticmethod
    def create_technical_chart(
        data: List[Dict[str, Any]],
        symbol: str,
        indicators: Optional[List[str]] = None
    ) -> Image.Image:
        """
        Create a technical analysis chart with indicators.

        Args:
            data: Price data with indicators
            symbol: Stock symbol
            indicators: List of indicators to plot (e.g., ['sma_20', 'rsi_14'])

        Returns:
            PIL Image of the chart
        """
        fig, axes = plt.subplots(3, 1, figsize=(12, 10),
                                 gridspec_kw={'height_ratios': [3, 1, 1]})

        # Price and moving averages
        closes = [float(d['close']) for d in data]
        ax1 = axes[0]
        ax1.plot(closes, label='Close Price', linewidth=2, color='blue')

        if indicators and 'sma_20' in indicators:
            sma_20 = [float(d.get('sma_20', 0)) for d in data]
            if any(sma_20):
                ax1.plot(sma_20, label='SMA 20', linewidth=1.5,
                        color='orange', linestyle='--')

        if indicators and 'sma_50' in indicators:
            sma_50 = [float(d.get('sma_50', 0)) for d in data]
            if any(sma_50):
                ax1.plot(sma_50, label='SMA 50', linewidth=1.5,
                        color='red', linestyle='--')

        ax1.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
        ax1.set_title(f'{symbol} Technical Analysis', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)

        # Volume
        volumes = [float(d['volume']) for d in data]
        ax2 = axes[1]
        ax2.bar(range(len(volumes)), volumes, width=0.8, color='steelblue', alpha=0.6)
        ax2.set_ylabel('Volume', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        # RSI
        if indicators and 'rsi_14' in indicators:
            rsi = [float(d.get('rsi_14', 50)) for d in data]
            ax3 = axes[2]
            ax3.plot(rsi, color='purple', linewidth=2)
            ax3.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Overbought')
            ax3.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Oversold')
            ax3.fill_between(range(len(rsi)), 30, 70, alpha=0.1, color='gray')
            ax3.set_ylabel('RSI', fontsize=12, fontweight='bold')
            ax3.set_xlabel('Time', fontsize=12, fontweight='bold')
            ax3.set_ylim(0, 100)
            ax3.legend(loc='upper left')
            ax3.grid(True, alpha=0.3)

        plt.tight_layout()

        # Convert to image
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        image = Image.open(buf)
        plt.close(fig)

        return image


class VLMAgent:
    """
    Vision Language Model Agent for analyzing stock charts.

    Supports multiple VLM backends:
    - LLaVA (open-source, runs locally)
    - BLIP-2 (open-source, runs locally)
    - GPT-4 Vision (requires API key)
    """

    def __init__(self, model_name: str = "llava", device: str = "auto"):
        """
        Initialize VLM agent.

        Args:
            model_name: 'llava', 'blip2', or 'gpt4-vision'
            device: 'auto', 'cuda', 'cpu'
        """
        self.model_name = model_name
        self.device = self._setup_device(device)
        self.model = None
        self.processor = None
        self.chart_generator = ChartGenerator()

        if HAS_VLM:
            self._load_model()
        else:
            logger.warning("VLM capabilities disabled. Install requirements-vlm.txt")

        logger.info(f"✓ VLM Agent initialized with {model_name} on {self.device}")

    def _setup_device(self, device: str) -> str:
        """Setup compute device."""
        if device == "auto":
            if HAS_VLM and torch.cuda.is_available():
                return "cuda"
            return "cpu"
        return device

    def _load_model(self):
        """Load the VLM model."""
        try:
            if self.model_name == "llava":
                self._load_llava()
            elif self.model_name == "blip2":
                self._load_blip2()
            elif self.model_name == "gpt4-vision":
                self._setup_gpt4_vision()
            else:
                raise ValueError(f"Unknown model: {self.model_name}")

            logger.info(f"✓ {self.model_name} model loaded successfully")

        except Exception as e:
            logger.error(f"Error loading VLM model: {e}")
            self.model = None

    def _load_llava(self):
        """Load LLaVA model."""
        model_id = "llava-hf/llava-1.5-7b-hf"  # You can use 13b for better quality

        logger.info(f"Loading LLaVA model from {model_id}...")

        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = LlavaForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map=self.device,
            load_in_4bit=True if self.device == "cuda" else False  # 4-bit quantization
        )

    def _load_blip2(self):
        """Load BLIP-2 model."""
        model_id = "Salesforce/blip2-opt-2.7b"  # Lightweight

        logger.info(f"Loading BLIP-2 model from {model_id}...")

        self.processor = BlipProcessor.from_pretrained(model_id)
        self.model = BlipForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map=self.device
        )

    def _setup_gpt4_vision(self):
        """Setup GPT-4 Vision API."""
        if not HAS_OPENAI or not settings.OPENAI_API_KEY:
            raise ValueError("GPT-4 Vision requires OpenAI API key")

        openai.api_key = settings.OPENAI_API_KEY
        logger.info("✓ GPT-4 Vision API configured")

    async def analyze_chart(
        self,
        chart_image: Image.Image,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a stock chart image using VLM.

        Args:
            chart_image: PIL Image of the chart
            prompt: Custom prompt for analysis

        Returns:
            Analysis results with interpretation
        """
        if not prompt:
            prompt = """Analyze this stock chart and provide:
1. Overall trend (bullish/bearish/neutral)
2. Key patterns or formations visible
3. Support and resistance levels
4. Volume analysis
5. Trading recommendation based on technical patterns
6. Risk assessment

Be specific and reference what you see in the chart."""

        try:
            if self.model_name == "gpt4-vision":
                return await self._analyze_with_gpt4_vision(chart_image, prompt)
            elif self.model_name == "llava":
                return await self._analyze_with_llava(chart_image, prompt)
            elif self.model_name == "blip2":
                return await self._analyze_with_blip2(chart_image, prompt)
            else:
                return {
                    "error": "VLM not available",
                    "interpretation": "Vision model not loaded. Please check configuration."
                }

        except Exception as e:
            logger.error(f"Error analyzing chart: {e}")
            return {
                "error": str(e),
                "interpretation": f"Failed to analyze chart: {str(e)}"
            }

    async def _analyze_with_llava(
        self,
        image: Image.Image,
        prompt: str
    ) -> Dict[str, Any]:
        """Analyze with LLaVA model."""
        # Prepare inputs
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image"},
                ],
            },
        ]

        prompt_text = self.processor.apply_chat_template(
            conversation, add_generation_prompt=True
        )

        inputs = self.processor(
            images=image,
            text=prompt_text,
            return_tensors="pt"
        ).to(self.device)

        # Generate response
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )

        # Decode
        interpretation = self.processor.decode(
            output[0],
            skip_special_tokens=True
        )

        return {
            "model": "LLaVA-1.5",
            "interpretation": interpretation,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _analyze_with_blip2(
        self,
        image: Image.Image,
        prompt: str
    ) -> Dict[str, Any]:
        """Analyze with BLIP-2 model."""
        inputs = self.processor(image, prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            output = self.model.generate(**inputs, max_length=512)

        interpretation = self.processor.decode(output[0], skip_special_tokens=True)

        return {
            "model": "BLIP-2",
            "interpretation": interpretation,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _analyze_with_gpt4_vision(
        self,
        image: Image.Image,
        prompt: str
    ) -> Dict[str, Any]:
        """Analyze with GPT-4 Vision API."""
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Call GPT-4 Vision API
        response = openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        interpretation = response.choices[0].message.content

        return {
            "model": "GPT-4 Vision",
            "interpretation": interpretation,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def analyze_from_data(
        self,
        price_data: List[Dict[str, Any]],
        symbol: str,
        chart_type: str = "candlestick",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate chart from data and analyze it.

        Args:
            price_data: List of price records
            symbol: Stock symbol
            chart_type: 'candlestick' or 'technical'
            prompt: Custom analysis prompt

        Returns:
            Analysis with chart interpretation
        """
        try:
            # Generate chart
            if chart_type == "candlestick":
                chart_image = self.chart_generator.create_candlestick_chart(
                    price_data, symbol
                )
            else:
                chart_image = self.chart_generator.create_technical_chart(
                    price_data, symbol, indicators=['sma_20', 'sma_50', 'rsi_14']
                )

            # Analyze chart
            analysis = await self.analyze_chart(chart_image, prompt)

            # Add metadata
            analysis.update({
                "symbol": symbol,
                "chart_type": chart_type,
                "data_points": len(price_data),
                "time_range": {
                    "start": price_data[0]['timestamp'],
                    "end": price_data[-1]['timestamp']
                }
            })

            return analysis

        except Exception as e:
            logger.error(f"Error in analyze_from_data: {e}")
            return {
                "error": str(e),
                "symbol": symbol,
                "interpretation": "Failed to generate or analyze chart"
            }


# Singleton instance
_vlm_agent_instance = None


def get_vlm_agent(model_name: str = "llava") -> VLMAgent:
    """Get or create VLM agent singleton."""
    global _vlm_agent_instance

    if _vlm_agent_instance is None or _vlm_agent_instance.model_name != model_name:
        _vlm_agent_instance = VLMAgent(model_name=model_name)

    return _vlm_agent_instance
