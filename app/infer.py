# app/infer.py
import os
import typing as t
import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification

MODEL_DIR = os.getenv("MODEL_DIR", "models/distilbert/global_tf")

class SentimentModel:
    def __init__(self, model_dir: str = MODEL_DIR):
        self.model_dir = model_dir
        self.tokenizer = None
        self.model = None
        self.id2label = {0: "Negative comment", 1: "Positive comment"}

    def load(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        self.model = TFAutoModelForSequenceClassification.from_pretrained(
            self.model_dir, from_pt=False
        )
        # **HARD OVERRIDE** – config ne derse desin kullanıcı-dostu etiketler
        self.id2label = {0: "Negative comment", 1: "Positive comment"}
        return self

    def predict(self, texts: t.List[str], max_len: int = 256):
        if not texts:
            return [], []
        enc = self.tokenizer(texts, padding=True, truncation=True, max_length=max_len, return_tensors="tf")
        logits = self.model(enc).logits
        probs = tf.nn.softmax(logits, axis=-1).numpy()
        preds = probs.argmax(axis=-1)
        return preds.tolist(), probs.tolist()

_model_singleton: t.Optional[SentimentModel] = None
def get_model():
    global _model_singleton
    if _model_singleton is None:
        _model_singleton = SentimentModel().load()
    return _model_singleton

