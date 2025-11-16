#!/usr/bin/env python3
"""
Script to fine-tune LLMs with LoRA/QLoRA for financial domain

Usage:
    python scripts/train_lora_model.py --train-data data/financial_qa.json
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.ml.lora_finetuning import LoRAFineTuner, FineTuningConfig, create_sample_financial_dataset
from loguru import logger


def main():
    parser = argparse.ArgumentParser(description="Fine-tune LLM with LoRA for finance")
    parser.add_argument(
        "--train-data",
        type=str,
        help="Path to training data JSON file"
    )
    parser.add_argument(
        "--eval-data",
        type=str,
        default=None,
        help="Path to evaluation data JSON file (optional)"
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="meta-llama/Llama-2-7b-hf",
        help="Base model name from HuggingFace"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./models/lora_finetuned",
        help="Output directory for fine-tuned model"
    )
    parser.add_argument(
        "--create-sample-data",
        action="store_true",
        help="Create sample financial Q&A dataset"
    )
    parser.add_argument(
        "--sample-data-path",
        type=str,
        default="./data/financial_qa_sample.json",
        help="Path for sample dataset"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--lora-r",
        type=int,
        default=16,
        help="LoRA rank"
    )
    parser.add_argument(
        "--lora-alpha",
        type=int,
        default=32,
        help="LoRA alpha (scaling factor)"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-4,
        help="Learning rate"
    )
    parser.add_argument(
        "--mlflow-uri",
        type=str,
        default="http://mlflow:5000",
        help="MLflow tracking server URI"
    )

    args = parser.parse_args()

    # Create sample data if requested
    if args.create_sample_data:
        logger.info(f"Creating sample dataset at {args.sample_data_path}")
        Path(args.sample_data_path).parent.mkdir(parents=True, exist_ok=True)
        create_sample_financial_dataset(args.sample_data_path, num_samples=100)
        logger.info("Sample dataset created. You can now train with --train-data flag.")
        return

    if not args.train_data:
        logger.error("Please provide --train-data path or use --create-sample-data first")
        sys.exit(1)

    # Configure fine-tuning
    config = FineTuningConfig(
        base_model_name=args.base_model,
        model_output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        learning_rate=args.learning_rate,
        mlflow_tracking_uri=args.mlflow_uri
    )

    logger.info("Fine-tuning configuration:")
    logger.info(f"  Base model: {config.base_model_name}")
    logger.info(f"  LoRA rank: {config.lora_r}")
    logger.info(f"  LoRA alpha: {config.lora_alpha}")
    logger.info(f"  Learning rate: {config.learning_rate}")
    logger.info(f"  Epochs: {config.num_train_epochs}")
    logger.info(f"  4-bit quantization: {config.use_4bit}")

    # Initialize fine-tuner
    finetuner = LoRAFineTuner(config)

    # Prepare model
    logger.info("Preparing model...")
    finetuner.prepare_model()

    # Prepare datasets
    logger.info("Preparing datasets...")
    finetuner.prepare_dataset(
        train_data=args.train_data,
        eval_data=args.eval_data
    )

    # Train
    logger.info("Starting training...")
    finetuner.train()

    logger.info("=" * 60)
    logger.info("Fine-tuning completed successfully!")
    logger.info(f"Model saved to: {args.output_dir}")
    logger.info(f"View training metrics at: {args.mlflow_uri}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
