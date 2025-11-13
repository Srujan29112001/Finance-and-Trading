"""
Offline LLM Engine for Finance Analytics
Runs locally without cloud dependencies

Supports:
- LLaMA 2 (7B, 13B, 70B)
- Mistral 7B
- Falcon
- Other GGUF models via llama.cpp
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger
import time

# Try importing offline LLM dependencies
try:
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
except ImportError:
    logger.warning("llama-cpp-python not installed")
    HAS_LLAMA_CPP = False

try:
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        pipeline,
        BitsAndBytesConfig
    )
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    logger.warning("transformers not installed")
    HAS_TRANSFORMERS = False

from app.config import settings


class OfflineLLMEngine:
    """
    Offline LLM Engine for running models locally.

    Supports multiple backends:
    1. llama.cpp (GGUF models) - Fast, low memory
    2. Transformers (HuggingFace) - More flexible
    """

    def __init__(
        self,
        model_name: str = "llama2-7b",
        backend: str = "llama-cpp",
        model_path: Optional[str] = None
    ):
        """
        Initialize offline LLM engine.

        Args:
            model_name: Name of the model to load
            backend: 'llama-cpp' or 'transformers'
            model_path: Path to local model file (for GGUF models)
        """
        self.model_name = model_name
        self.backend = backend
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.tokenizer = None

        self._load_model()

        logger.info(f"✓ Offline LLM Engine initialized: {model_name} ({backend})")

    def _get_default_model_path(self) -> str:
        """Get default model path based on model name."""
        models_dir = Path("/models") / "offline_llm"
        models_dir.mkdir(parents=True, exist_ok=True)

        # Common GGUF model filenames
        model_files = {
            "llama2-7b": "llama-2-7b-chat.Q4_K_M.gguf",
            "llama2-13b": "llama-2-13b-chat.Q4_K_M.gguf",
            "mistral-7b": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
            "falcon-7b": "falcon-7b-instruct.Q4_K_M.gguf",
        }

        filename = model_files.get(self.model_name, "model.gguf")
        return str(models_dir / filename)

    def _load_model(self):
        """Load the LLM model."""
        try:
            if self.backend == "llama-cpp":
                self._load_llama_cpp()
            elif self.backend == "transformers":
                self._load_transformers()
            else:
                raise ValueError(f"Unknown backend: {self.backend}")

        except Exception as e:
            logger.error(f"Error loading offline LLM: {e}")
            logger.warning("Falling back to mock responses")
            self.model = None

    def _load_llama_cpp(self):
        """Load model using llama.cpp (fast, quantized)."""
        if not HAS_LLAMA_CPP:
            raise ImportError("llama-cpp-python not installed")

        if not os.path.exists(self.model_path):
            logger.warning(
                f"Model file not found: {self.model_path}\n"
                f"Download GGUF models from: https://huggingface.co/TheBloke"
            )
            self.model = None
            return

        logger.info(f"Loading model from {self.model_path}...")

        self.model = Llama(
            model_path=self.model_path,
            n_ctx=4096,  # Context window
            n_threads=8,  # CPU threads
            n_gpu_layers=35 if torch.cuda.is_available() else 0,  # GPU acceleration
            verbose=False
        )

        logger.info("✓ Model loaded with llama.cpp")

    def _load_transformers(self):
        """Load model using HuggingFace Transformers."""
        if not HAS_TRANSFORMERS:
            raise ImportError("transformers not installed")

        # Model IDs
        model_ids = {
            "llama2-7b": "meta-llama/Llama-2-7b-chat-hf",
            "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.2",
            "falcon-7b": "tiiuae/falcon-7b-instruct"
        }

        model_id = model_ids.get(self.model_name)
        if not model_id:
            raise ValueError(f"Unknown model: {self.model_name}")

        logger.info(f"Loading {model_id} with Transformers...")

        # Quantization config for lower memory usage
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True
        )

        logger.info("✓ Model loaded with Transformers")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stop: Stop sequences

        Returns:
            Generated text
        """
        if self.model is None:
            return self._mock_generate(prompt)

        try:
            if self.backend == "llama-cpp":
                return self._generate_llama_cpp(prompt, max_tokens, temperature, top_p, stop)
            elif self.backend == "transformers":
                return self._generate_transformers(prompt, max_tokens, temperature, top_p)
            else:
                return self._mock_generate(prompt)

        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"Error generating response: {str(e)}"

    def _generate_llama_cpp(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop: Optional[List[str]]
    ) -> str:
        """Generate using llama.cpp."""
        output = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or [],
            echo=False
        )

        return output['choices'][0]['text'].strip()

    def _generate_transformers(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float
    ) -> str:
        """Generate using Transformers."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove the prompt from response
        if response.startswith(prompt):
            response = response[len(prompt):].strip()

        return response

    def _mock_generate(self, prompt: str) -> str:
        """Mock generation when model not available."""
        return (
            "Offline LLM not loaded. To use offline analytics:\n"
            "1. Install: pip install -r requirements-vlm.txt\n"
            "2. Download a GGUF model from https://huggingface.co/TheBloke\n"
            f"3. Place it at: {self.model_path}\n\n"
            "For now, using basic analysis based on prompt keywords."
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """
        Chat completion with conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Assistant response
        """
        # Build prompt from messages
        prompt = self._format_chat_prompt(messages)

        return self.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into a prompt."""
        if self.model_name.startswith("llama2"):
            # LLaMA 2 chat format
            prompt = "<s>[INST] "
            for i, msg in enumerate(messages):
                if msg['role'] == 'system':
                    prompt += f"<<SYS>>\n{msg['content']}\n<</SYS>>\n\n"
                elif msg['role'] == 'user':
                    if i > 0:
                        prompt += f"[INST] {msg['content']} [/INST] "
                    else:
                        prompt += f"{msg['content']} [/INST] "
                elif msg['role'] == 'assistant':
                    prompt += f"{msg['content']} </s><s>"
            return prompt

        elif self.model_name.startswith("mistral"):
            # Mistral format
            prompt = ""
            for msg in messages:
                if msg['role'] == 'user':
                    prompt += f"[INST] {msg['content']} [/INST]\n"
                elif msg['role'] == 'assistant':
                    prompt += f"{msg['content']}\n"
            return prompt

        else:
            # Generic format
            prompt = ""
            for msg in messages:
                role = msg['role'].capitalize()
                prompt += f"{role}: {msg['content']}\n"
            prompt += "Assistant: "
            return prompt


class OfflineFinanceAnalyzer:
    """
    Offline finance analyzer using local LLM.
    Provides market analysis without cloud dependencies.
    """

    def __init__(self, model_name: str = "mistral-7b"):
        """Initialize analyzer with offline LLM."""
        self.llm = OfflineLLMEngine(model_name=model_name, backend="llama-cpp")

        self.system_prompt = """You are an expert financial analyst specializing in stock market analysis.
You provide data-driven insights, technical analysis, and trading recommendations.
Always be objective and cite specific data points when making assessments.
Include risk warnings when appropriate."""

        logger.info("✓ Offline Finance Analyzer initialized")

    async def analyze_market_data(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        sentiment_data: Optional[Dict[str, Any]] = None,
        news_data: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Analyze market data and provide insights.

        Args:
            symbol: Stock symbol
            price_data: Current price and metrics
            sentiment_data: Sentiment scores
            news_data: Recent news articles

        Returns:
            Analysis report
        """
        # Build context
        context = self._build_market_context(symbol, price_data, sentiment_data, news_data)

        # Generate analysis
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Analyze this market data and provide insights:\n\n{context}"}
        ]

        analysis = self.llm.chat(messages, max_tokens=800, temperature=0.7)

        return analysis

    def _build_market_context(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        sentiment_data: Optional[Dict[str, Any]],
        news_data: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Build market context string."""
        context = f"Stock: {symbol}\n\n"

        # Price data
        context += "Price Data:\n"
        context += f"- Current Price: ${price_data.get('current_price', 'N/A')}\n"
        context += f"- Change: {price_data.get('change_pct', 0):.2f}%\n"
        context += f"- 24h High: ${price_data.get('high_24h', 'N/A')}\n"
        context += f"- 24h Low: ${price_data.get('low_24h', 'N/A')}\n"
        context += f"- Volume: {price_data.get('volume', 'N/A'):,}\n\n"

        # Sentiment
        if sentiment_data:
            context += "Sentiment Analysis:\n"
            context += f"- Overall: {sentiment_data.get('sentiment_label', 'N/A')}\n"
            context += f"- Score: {sentiment_data.get('avg_sentiment', 0):.3f}\n"
            context += f"- Data Points: {sentiment_data.get('sample_size', 0)}\n\n"

        # News
        if news_data:
            context += "Recent News:\n"
            for i, article in enumerate(news_data[:3], 1):
                context += f"{i}. {article.get('headline', 'N/A')}\n"
            context += "\n"

        context += "Provide: trend analysis, key observations, trading recommendation, and risk assessment."

        return context

    async def answer_question(
        self,
        question: str,
        context: Optional[str] = None
    ) -> str:
        """
        Answer a finance-related question.

        Args:
            question: User question
            context: Additional context (optional)

        Returns:
            Answer
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        if context:
            messages.append({
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            })
        else:
            messages.append({"role": "user", "content": question})

        answer = self.llm.chat(messages, max_tokens=600, temperature=0.7)

        return answer


# Singleton
_offline_analyzer_instance = None


def get_offline_analyzer(model_name: str = "mistral-7b") -> OfflineFinanceAnalyzer:
    """Get offline analyzer singleton."""
    global _offline_analyzer_instance

    if _offline_analyzer_instance is None:
        _offline_analyzer_instance = OfflineFinanceAnalyzer(model_name=model_name)

    return _offline_analyzer_instance
