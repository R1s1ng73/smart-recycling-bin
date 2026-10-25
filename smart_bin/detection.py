"""YOLO image inference. The ML dependency is loaded only when needed."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Prediction:
    labels: set[str]
    annotated_rgb: object  # NumPy array, with RGB channel ordering


class WasteDetector:
    def __init__(self, model_path: Path, confidence: float = 0.5) -> None:
        if not model_path.is_file():
            raise FileNotFoundError(f"Model not found: {model_path}")
        if not 0 < confidence <= 1:
            raise ValueError("Confidence must be in (0, 1]")
        from ultralytics import YOLO

        # Only load checkpoints you trust: PyTorch models can contain pickled data.
        self.model = YOLO(str(model_path))
        self.confidence = confidence

    def predict(self, frame_bgr: object) -> Prediction:
        import cv2

        results = self.model.predict(source=frame_bgr, conf=self.confidence, verbose=False)
        if not results:
            return Prediction(set(), cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        result = results[0]
        names = result.names
        labels = {names[int(box.cls[0])] for box in result.boxes}
        annotated_rgb = cv2.cvtColor(result.plot(), cv2.COLOR_BGR2RGB)
        return Prediction(labels, annotated_rgb)
