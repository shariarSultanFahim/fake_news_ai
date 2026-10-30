"""Model loading and inference module matching AGENT.md section 2."""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import torch
import torch.nn.functional as F
from transformers import AutoConfig, AutoTokenizer, AutoModelForSequenceClassification
from backend.app.preprocess import preprocess_inputs


class BanglaFakeNewsModel:
    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.config_path = self.model_dir / "config.json"
        self.inference_config_path = self.model_dir / "inference_config.json"

        if not self.config_path.exists():
            raise FileNotFoundError(f"Model config not found at {self.config_path}")
        if not self.inference_config_path.exists():
            raise FileNotFoundError(f"Inference config not found at {self.inference_config_path}")

        # Read inference config keys dynamically
        with open(self.inference_config_path, "r", encoding="utf-8") as f:
            self.inference_config = json.load(f)

        self.threshold_fake: float = float(self.inference_config.get("threshold_fake", 0.40))
        self.max_length: int = int(self.inference_config.get("max_length", 256))
        self.uses_normalizer: bool = bool(self.inference_config.get("uses_normalizer", True))
        self.model_version: str = str(self.inference_config.get("model_version", "v1"))

        # Load HF config & assert id2label order
        self.hf_config = AutoConfig.from_pretrained(str(self.model_dir))
        expected_id2label = {0: "fake", 1: "authentic"}
        current_id2label = {int(k): v for k, v in self.hf_config.id2label.items()}
        if current_id2label != expected_id2label:
            raise ValueError(
                f"Invalid label order in model config: {current_id2label}. Expected: {expected_id2label}"
            )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))

        # Load model weights
        self.model = AutoModelForSequenceClassification.from_pretrained(str(self.model_dir))
        self.model.eval()

    def predict(self, headline: str, content: str) -> Tuple[float, bool]:
        """
        Runs prediction for headline and content.
        Returns:
            p_fake: float probability of fake class (index 0)
            truncated: whether the headline was truncated due to >100 words edge case
        """
        proc_headline, proc_content, truncated = preprocess_inputs(
            headline=headline,
            content=content,
            uses_normalizer=self.uses_normalizer
        )

        # Tokenize as a sentence pair: headline is first sentence, content is second sentence.
        # Only content is truncated (truncation="only_second").
        inputs = self.tokenizer(
            proc_headline,
            proc_content,
            truncation="only_second",
            max_length=self.max_length,
            return_tensors="pt"
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1)
            # p_fake is at index 0
            p_fake = probs[0, 0].item()

        return p_fake, truncated

