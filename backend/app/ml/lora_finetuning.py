"""
LoRA/QLoRA Fine-Tuning Module

Implements parameter-efficient fine-tuning of Large Language Models
for financial domain using Low-Rank Adaptation (LoRA) and Quantized LoRA (QLoRA).

Key Features:
- 4-bit quantization for memory efficiency (QLoRA)
- LoRA adapters for parameter-efficient training
- Financial domain specialization
- MLflow experiment tracking
- Checkpoint management
"""

import os
from typing import Optional, Dict, List, Union
from dataclasses import dataclass
from pathlib import Path
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    PeftModel
)
from loguru import logger
import mlflow
import mlflow.pytorch
from datasets import load_dataset, Dataset as HFDataset
import json


@dataclass
class FineTuningConfig:
    """Configuration for LoRA fine-tuning"""
    # Model settings
    base_model_name: str = "meta-llama/Llama-2-7b-hf"  # or "mistralai/Mistral-7B-v0.1"
    model_output_dir: str = "./models/lora_finetuned"

    # LoRA settings
    lora_r: int = 16  # Rank of update matrices
    lora_alpha: int = 32  # Scaling factor
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = None  # Auto-detect if None
    lora_bias: str = "none"  # "none", "all", or "lora_only"

    # QLoRA 4-bit quantization
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"  # "nf4" or "fp4"
    use_nested_quant: bool = True

    # Training hyperparameters
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    warmup_steps: int = 100
    max_grad_norm: float = 0.3
    weight_decay: float = 0.001
    optim: str = "paged_adamw_32bit"
    lr_scheduler_type: str = "cosine"

    # Logging and checkpoints
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500
    save_total_limit: int = 3

    # Dataset
    max_seq_length: int = 2048
    dataset_text_field: str = "text"

    # MLflow
    mlflow_tracking_uri: Optional[str] = None
    mlflow_experiment_name: str = "finance-llm-finetuning"

    def __post_init__(self):
        if self.lora_target_modules is None:
            # Default target modules for Llama/Mistral
            self.lora_target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]


class FinancialQADataset(Dataset):
    """
    Dataset for financial Q&A pairs

    Formats data as instruction-following examples for fine-tuning
    """

    def __init__(
        self,
        data: Union[str, List[Dict]],
        tokenizer,
        max_length: int = 2048
    ):
        """
        Args:
            data: Path to JSON file or list of dicts with 'question' and 'answer' keys
            tokenizer: HuggingFace tokenizer
            max_length: Maximum sequence length
        """
        self.tokenizer = tokenizer
        self.max_length = max_length

        # Load data
        if isinstance(data, str):
            with open(data, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = data

        logger.info(f"Loaded {len(self.data)} examples for fine-tuning")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # Format as instruction-following
        prompt = self._format_prompt(item)

        # Tokenize
        encodings = self.tokenizer(
            prompt,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt"
        )

        return {
            "input_ids": encodings["input_ids"].squeeze(),
            "attention_mask": encodings["attention_mask"].squeeze(),
            "labels": encodings["input_ids"].squeeze()
        }

    def _format_prompt(self, item: Dict) -> str:
        """
        Format Q&A pair as instruction-following prompt

        Uses Alpaca-style formatting
        """
        question = item.get("question", "")
        answer = item.get("answer", "")
        context = item.get("context", "")

        if context:
            prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
You are a financial analyst. Answer the following question based on the provided context.

### Input:
Context: {context}

Question: {question}

### Response:
{answer}"""
        else:
            prompt = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
You are a financial analyst. Answer the following question.

### Input:
{question}

### Response:
{answer}"""

        return prompt


class LoRAFineTuner:
    """
    Handles LoRA/QLoRA fine-tuning of LLMs for financial domain
    """

    def __init__(self, config: FineTuningConfig):
        """
        Initialize fine-tuner

        Args:
            config: Fine-tuning configuration
        """
        self.config = config
        self.model = None
        self.tokenizer = None
        self.trainer = None

        # Setup MLflow
        if config.mlflow_tracking_uri:
            mlflow.set_tracking_uri(config.mlflow_tracking_uri)
        mlflow.set_experiment(config.mlflow_experiment_name)

        logger.info("LoRA Fine-Tuner initialized")

    def prepare_model(self):
        """
        Load and prepare model with QLoRA configuration
        """
        logger.info(f"Loading base model: {self.config.base_model_name}")

        # Configure 4-bit quantization
        bnb_config = None
        if self.config.use_4bit:
            compute_dtype = getattr(torch, self.config.bnb_4bit_compute_dtype)
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type=self.config.bnb_4bit_quant_type,
                bnb_4bit_compute_dtype=compute_dtype,
                bnb_4bit_use_double_quant=self.config.use_nested_quant
            )

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model_name,
            trust_remote_code=True
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"

        # Prepare model for k-bit training
        if self.config.use_4bit:
            self.model = prepare_model_for_kbit_training(self.model)

        # Configure LoRA
        lora_config = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            target_modules=self.config.lora_target_modules,
            lora_dropout=self.config.lora_dropout,
            bias=self.config.lora_bias,
            task_type="CAUSAL_LM"
        )

        # Apply LoRA
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()

        logger.info("Model prepared with QLoRA configuration")

    def prepare_dataset(
        self,
        train_data: Union[str, List[Dict]],
        eval_data: Optional[Union[str, List[Dict]]] = None
    ):
        """
        Prepare training and evaluation datasets

        Args:
            train_data: Training data (path or list of dicts)
            eval_data: Evaluation data (optional)
        """
        logger.info("Preparing datasets")

        self.train_dataset = FinancialQADataset(
            train_data,
            self.tokenizer,
            self.config.max_seq_length
        )

        self.eval_dataset = None
        if eval_data:
            self.eval_dataset = FinancialQADataset(
                eval_data,
                self.tokenizer,
                self.config.max_seq_length
            )

        logger.info(f"Train dataset size: {len(self.train_dataset)}")
        if self.eval_dataset:
            logger.info(f"Eval dataset size: {len(self.eval_dataset)}")

    def train(self):
        """
        Execute fine-tuning with MLflow tracking
        """
        if self.model is None:
            raise ValueError("Model not prepared. Call prepare_model() first.")

        logger.info("Starting fine-tuning")

        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.config.model_output_dir,
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            max_grad_norm=self.config.max_grad_norm,
            weight_decay=self.config.weight_decay,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps if self.eval_dataset else None,
            evaluation_strategy="steps" if self.eval_dataset else "no",
            save_total_limit=self.config.save_total_limit,
            fp16=True,
            optim=self.config.optim,
            lr_scheduler_type=self.config.lr_scheduler_type,
            report_to=["mlflow"],
            load_best_model_at_end=True if self.eval_dataset else False
        )

        # Initialize trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
            data_collator=DataCollatorForLanguageModeling(
                self.tokenizer,
                mlm=False
            )
        )

        # Start MLflow run
        with mlflow.start_run(run_name=f"lora-{self.config.base_model_name}"):
            # Log config
            mlflow.log_params({
                "base_model": self.config.base_model_name,
                "lora_r": self.config.lora_r,
                "lora_alpha": self.config.lora_alpha,
                "learning_rate": self.config.learning_rate,
                "num_epochs": self.config.num_train_epochs,
                "batch_size": self.config.per_device_train_batch_size,
                "use_4bit": self.config.use_4bit
            })

            # Train
            train_result = self.trainer.train()

            # Log metrics
            metrics = train_result.metrics
            mlflow.log_metrics({
                "train_loss": metrics.get("train_loss", 0),
                "train_runtime": metrics.get("train_runtime", 0),
                "train_samples_per_second": metrics.get("train_samples_per_second", 0)
            })

            # Save model
            self.save_model()

        logger.info("Fine-tuning completed")

    def save_model(self, output_dir: Optional[str] = None):
        """
        Save fine-tuned model and adapters

        Args:
            output_dir: Output directory (uses config default if None)
        """
        save_dir = output_dir or self.config.model_output_dir
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving model to {save_dir}")

        # Save LoRA adapters
        self.model.save_pretrained(save_dir)
        self.tokenizer.save_pretrained(save_dir)

        # Log to MLflow
        mlflow.pytorch.log_model(self.model, "model")

        logger.info("Model saved successfully")

    @staticmethod
    def load_finetuned_model(
        base_model_name: str,
        adapter_path: str,
        device_map: str = "auto"
    ):
        """
        Load a fine-tuned model with LoRA adapters

        Args:
            base_model_name: Name of base model
            adapter_path: Path to LoRA adapters
            device_map: Device mapping strategy

        Returns:
            Tuple of (model, tokenizer)
        """
        logger.info(f"Loading fine-tuned model from {adapter_path}")

        # Load base model
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            device_map=device_map,
            trust_remote_code=True
        )

        # Load LoRA adapters
        model = PeftModel.from_pretrained(model, adapter_path)

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(adapter_path)

        logger.info("Fine-tuned model loaded successfully")

        return model, tokenizer


def create_sample_financial_dataset(output_path: str, num_samples: int = 100):
    """
    Create a sample financial Q&A dataset for demonstration

    Args:
        output_path: Path to save JSON file
        num_samples: Number of samples to generate
    """
    samples = [
        {
            "question": "What is the Price-to-Earnings (P/E) ratio and how is it calculated?",
            "answer": "The P/E ratio is a valuation metric that measures a company's current share price relative to its earnings per share (EPS). It's calculated as: P/E Ratio = Market Price per Share / Earnings per Share. A higher P/E ratio suggests investors expect higher earnings growth in the future."
        },
        {
            "question": "Explain the concept of market capitalization.",
            "answer": "Market capitalization (market cap) is the total market value of a company's outstanding shares. It's calculated by multiplying the current stock price by the total number of outstanding shares. Companies are typically categorized as large-cap (over $10B), mid-cap ($2B-$10B), or small-cap (under $2B)."
        },
        {
            "question": "What is a bull market?",
            "answer": "A bull market is a financial market condition characterized by rising prices and investor optimism. Typically, a bull market is defined as a 20% or more rise in stock prices from recent lows, accompanied by positive investor sentiment and strong economic fundamentals."
        },
        # Add more samples as needed...
    ]

    # Repeat samples to reach desired count
    while len(samples) < num_samples:
        samples.append(samples[len(samples) % len(samples)])

    samples = samples[:num_samples]

    with open(output_path, 'w') as f:
        json.dump(samples, f, indent=2)

    logger.info(f"Created sample dataset with {len(samples)} examples at {output_path}")
