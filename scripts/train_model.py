"""Train the trade target/SL/TP predictor using cached price history.

Usage:
    python scripts/train_model.py
"""
from pathlib import Path
import json
from src.market_analyser.ml import train_model


def main():
    print("Starting training — this may take a few minutes...")
    result = train_model(horizon=5, n_estimators=50)
    print("Training completed:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
