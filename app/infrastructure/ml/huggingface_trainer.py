import json
from pathlib import Path
from typing import Dict

import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from datasets import Dataset as HFDataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

from app.domain.contracts import Dataset


class BinaryFocalLoss(nn.Module):
    """
    Función de pérdida matemática Focal Loss optimizada para escenarios
    con desequilibrio extremo de clases en la detección de fallos de seguridad.
    """
    def __init__(self, alpha=0.25, gamma=2.0, reduction='mean'):
        super(BinaryFocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, logits, targets):
        logits = logits.squeeze(-1)
        targets = targets.to(torch.float32)
        
        bce_loss = F.binary_cross_entropy_with_logits(logits, targets, reduction='none')
        
        probs = torch.sigmoid(logits)
        pt = targets * probs + (1 - targets) * (1 - probs)
        
        focal_weight = ((1 - pt) ** self.gamma)
        alpha_weight = targets * self.alpha + (1 - targets) * (1 - self.alpha)
        
        loss = alpha_weight * focal_weight * bce_loss
        
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss


class CustomVulnerabilityTrainer(Trainer):
    """
    Extensión del Trainer de Hugging Face optimizada para anular la pérdida estándar
    e inyectar la función de pérdida focalizada en modelos de lenguaje para código.
    """
    def __init__(self, *args, alpha_loss=0.25, gamma_loss=2.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.loss_fn = BinaryFocalLoss(alpha=alpha_loss, gamma=gamma_loss, reduction='mean')

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        
        if isinstance(outputs, dict):
            logits = outputs.get("logits")
        else:
            logits = outputs[0]
            
        loss = self.loss_fn(logits, labels)
        
        return (loss, outputs) if return_outputs else loss


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = (torch.sigmoid(torch.tensor(logits)) > 0.5).numpy().astype(int)
    
    accuracy = accuracy_score(labels, predictions)
    precision = precision_score(labels, predictions, zero_division=0)
    recall = recall_score(labels, predictions, zero_division=0)
    f1 = f1_score(labels, predictions, zero_division=0)
    
    try:
        roc_auc = roc_auc_score(labels, torch.sigmoid(torch.tensor(logits)).numpy())
    except ValueError:
        roc_auc = 0.0
        
    return {
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4)
    }


class HuggingFaceTrainer:
    TARGET_COLUMN = "is_vulnerable"
    
    def __init__(
        self, 
        model_path: Path, 
        report_path: Path, 
        model_name: str = "microsoft/codebert-base",
        epochs: int = 1,
        batch_size: int = 8,
        alpha_loss: float = 0.85,
        gamma_loss: float = 2.0
    ) -> None:
        self._model_path = model_path
        self._report_path = report_path
        self._model_name = model_name
        self._epochs = epochs
        self._batch_size = batch_size
        self._alpha_loss = alpha_loss
        self._gamma_loss = gamma_loss

    def train(self, dataset: Dataset) -> Dict[str, object]:
        dataset_frame = pd.DataFrame(dataset)
        
        if "raw_code" not in dataset_frame.columns:
            raise ValueError("HuggingFaceTrainer requires a 'raw_code' column for sequence classification.")
            
        dataset_frame = dataset_frame.dropna(subset=["raw_code", self.TARGET_COLUMN])
        dataset_frame[self.TARGET_COLUMN] = dataset_frame[self.TARGET_COLUMN].astype(float)
        
        train_df, eval_df = train_test_split(dataset_frame, test_size=0.1, stratify=dataset_frame[self.TARGET_COLUMN], random_state=42)
        
        tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        model = AutoModelForSequenceClassification.from_pretrained(self._model_name, num_labels=1)
        
        def tokenize_function(examples):
            return tokenizer(examples["raw_code"], padding="max_length", truncation=True, max_length=512)

        hf_train_dataset = HFDataset.from_pandas(train_df)
        hf_eval_dataset = HFDataset.from_pandas(eval_df)
        
        def format_labels(example):
            example["labels"] = float(example[self.TARGET_COLUMN])
            return example
            
        hf_train_dataset = hf_train_dataset.map(format_labels)
        hf_eval_dataset = hf_eval_dataset.map(format_labels)
        
        tokenized_train = hf_train_dataset.map(tokenize_function, batched=True)
        tokenized_eval = hf_eval_dataset.map(tokenize_function, batched=True)
        
        training_args = TrainingArguments(
            output_dir=str(self._model_path.parent / "checkpoints"),
            num_train_epochs=self._epochs,
            per_device_train_batch_size=self._batch_size,
            per_device_eval_batch_size=self._batch_size,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="f1_score",
            logging_dir=str(self._model_path.parent / "logs"),
            logging_steps=10,
        )

        trainer = CustomVulnerabilityTrainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_train,
            eval_dataset=tokenized_eval,
            compute_metrics=compute_metrics,
            alpha_loss=self._alpha_loss,
            gamma_loss=self._gamma_loss
        )

        trainer.train()
        eval_metrics = trainer.evaluate()
        
        model.save_pretrained(self._model_path)
        tokenizer.save_pretrained(self._model_path)
        
        formatted_metrics = {k.replace("eval_", ""): v for k, v in eval_metrics.items()}
        
        self._report_path.parent.mkdir(parents=True, exist_ok=True)
        self._report_path.write_text(json.dumps(formatted_metrics, indent=2), encoding="utf-8")
        
        return formatted_metrics
