import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

try:
    from tabpfn import TabPFNClassifier
except ImportError:
    TabPFNClassifier = None

from config import settings

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "bbsr_weather_comfort.csv"
FEATURE_COLS = ["hour", "temp_c", "humidity_pct", "uv_index"]
TARGET_COL = "comfort_class"

# Global model state
_tabpfn_model: Optional[Any] = None
_model_mode: str = "Uninitialized"
_weather_df: Optional[pd.DataFrame] = None


def _heuristic_classifier(temp: float, uv: float) -> str:
    """
    Fallback heuristic classifier in case PyTorch or TabPFN
    runs into container memory constraints or missing dependencies:
      - If temp > 31.5 or uv >= 7: "Avoid"
      - Else if temp > 29.0: "Moderate"
      - Else: "Optimal"
    """
    if temp > 31.5 or uv >= 7.0:
        return "Avoid"
    elif temp > 29.0:
        return "Moderate"
    else:
        return "Optimal"


def _generate_advisory_text(comfort_class: str, hour: int, temp: float, uv: float) -> str:
    """Generate localized, context-aware trail safety advisory."""
    if comfort_class == "Optimal":
        if 5 <= hour <= 9:
            return "Pleasant early morning breeze with mild solar radiation. Safe for open trails and Khandagiri ridge climbs."
        elif 16 <= hour <= 19:
            return "Comfortable evening sea-breeze setting in. Safe for open trails before campus curfew."
        else:
            return "Mild ambient conditions. Safe for open trails and botanical walks."
    elif comfort_class == "Moderate":
        return f"Moderate thermal load ({temp:.1f}°C) and coastal humidity. Recommend tree-shaded trails like Ekamra Kanan with hydration."
    else:  # Avoid
        return f"Harsh coastal heat ({temp:.1f}°C) and peak solar radiation (UV {uv:.1f}). Outdoor trail scouting unsafe; stay indoors."


def _init_tabpfn():
    """Load Bhubaneswar climate dataset and fit TabPFNClassifier(device='cpu') on application boot."""
    global _tabpfn_model, _model_mode, _weather_df

    try:
        if DATA_PATH.exists():
            _weather_df = pd.read_csv(DATA_PATH)
            logger.info(f"Loaded {len(_weather_df)} records from {DATA_PATH}")
        else:
            logger.warning(f"Data file not found at {DATA_PATH}")
    except Exception as ex:
        logger.error(f"Error loading CSV data: {ex}")

    if TabPFNClassifier is not None and _weather_df is not None and not _weather_df.empty:
        try:
            logger.info("Initializing TabPFNClassifier(device='cpu')...")
            X = _weather_df[FEATURE_COLS].values
            y = _weather_df[TARGET_COL].values
            
            clf = TabPFNClassifier(device="cpu", N_ensemble_configurations=settings.TABPFN_N_ENSEMBLE)
            clf.fit(X, y)
            _tabpfn_model = clf
            _model_mode = "TabPFN (CPU)"
            logger.info("TabPFNClassifier successfully trained on BBSR weather dataset.")
            return
        except Exception as e:
            logger.warning(f"TabPFN fit failed ({e}). Reverting to heuristic fallback classifier.")
    
    _model_mode = "Heuristic Rule Fallback"
    logger.info("Using lightweight Heuristic Classifier for zero-overhead inference.")


# Fit model on module import / boot
_init_tabpfn()


def predict_comfort_window(hour: int, temp: float, humidity: float, uv: float) -> dict:
    """
    Exported comfort classification function.
    
    Returns:
    {
      "comfort_class": prediction, # "Optimal", "Moderate", or "Avoid"
      "is_outdoor_safe": bool,
      "advisory": str # e.g. "Pleasant early morning breeze. Safe for open trails."
    }
    """
    prediction = None

    # Try TabPFN model inference if fitted
    if _tabpfn_model is not None:
        try:
            features = np.array([[float(hour), float(temp), float(humidity), float(uv)]])
            pred = _tabpfn_model.predict(features)[0]
            prediction = str(pred)
        except Exception as err:
            logger.warning(f"TabPFN prediction error: {err}. Falling back to heuristic classifier.")

    # Fallback heuristic classifier
    if prediction is None:
        prediction = _heuristic_classifier(temp=temp, uv=uv)

    is_outdoor_safe = (prediction != "Avoid")
    advisory = _generate_advisory_text(prediction, hour, temp, uv)

    return {
        "comfort_class": prediction,
        "is_outdoor_safe": is_outdoor_safe,
        "advisory": advisory
    }


class TabPFNWeatherComfortService:
    """
    Service wrapper for backward-compatibility with routers and inspection utilities.
    """
    @property
    def model_name(self) -> str:
        return _model_mode

    @property
    def df(self) -> Optional[pd.DataFrame]:
        return _weather_df

    def predict_comfort(
        self,
        hour: int,
        temp_c: Optional[float] = None,
        humidity_pct: Optional[float] = None,
        uv_index: Optional[float] = None
    ) -> Dict[str, Any]:
        # Lookup baseline from dataset if values not provided
        t = temp_c
        h = humidity_pct
        u = uv_index
        if (t is None or h is None or u is None) and _weather_df is not None:
            matched = _weather_df[_weather_df["hour"] == max(0, min(23, hour))]
            if not matched.empty:
                row = matched.iloc[0]
                t = t if t is not None else float(row["temp_c"])
                h = h if h is not None else float(row["humidity_pct"])
                u = u if u is not None else float(row["uv_index"])

        t = t if t is not None else 28.0
        h = h if h is not None else 75.0
        u = u if u is not None else 2.0

        res = predict_comfort_window(hour, t, h, u)

        return {
            "comfort_class": res["comfort_class"],
            "confidence": 1.0,
            "is_outdoor_safe": res["is_outdoor_safe"],
            "environmental_metrics": {
                "hour": hour,
                "temp_c": t,
                "humidity_pct": h,
                "uv_index": u
            },
            "model_metadata": {
                "model_name": self.model_name,
                "trained_samples": len(_weather_df) if _weather_df is not None else 0
            },
            "advisory": {
                "headline": f"{res['comfort_class']} Trail Conditions",
                "tagline": res["advisory"],
                "touch_grass_friendly": res["is_outdoor_safe"],
                "suggested_action": res["advisory"]
            }
        }

    def get_full_day_matrix(self) -> List[Dict[str, Any]]:
        matrix = []
        for h in range(24):
            pred = self.predict_comfort(h)
            matrix.append({
                "hour": h,
                "time_label": f"{h:02d}:00",
                "temp_c": pred["environmental_metrics"]["temp_c"],
                "humidity_pct": pred["environmental_metrics"]["humidity_pct"],
                "uv_index": pred["environmental_metrics"]["uv_index"],
                "comfort_class": pred["comfort_class"],
                "is_outdoor_safe": pred["is_outdoor_safe"],
                "touch_grass_friendly": pred["is_outdoor_safe"],
                "advisory": pred["advisory"]["tagline"]
            })
        return matrix


# Service singleton
tabpfn_service = TabPFNWeatherComfortService()
