"""
Singleton model loader for deepfake detection.
Loads the TensorFlow model once on Django startup for optimal performance.
"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DeepfakeDetectorSingleton:
    """Singleton class to load and cache the deepfake detection model."""
    
    _instance: Optional['DeepfakeDetectorSingleton'] = None
    _model = None
    _model_loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self):
        """Load the TensorFlow model if not already loaded."""
        if self._model_loaded:
            return self._model
        
        try:
            import tensorflow as tf
            
            # Get model path
            model_dir = Path(__file__).parent
            model_path = model_dir / 'final_fake_detector_model.h5'
            
            if not model_path.exists():
                logger.error(f"Model file not found at {model_path}")
                raise FileNotFoundError(
                    f"Deepfake detection model not found at {model_path}. "
                    "Please place your trained model (.h5 file) in Backend/ml_models/"
                )
            
            logger.info(f"Loading deepfake detection model from {model_path}")
            self._model = tf.keras.models.load_model(str(model_path))
            self._model_loaded = True
            logger.info("Deepfake detection model loaded successfully")
            
            return self._model
            
        except ImportError as e:
            logger.error(f"TensorFlow not installed: {e}")
            self._model_loaded = False
            raise ImportError(
                "TensorFlow is required for deepfake detection. "
                "Install it with: pip install tensorflow>=2.12.0"
            )
        except Exception as e:
            logger.error(f"Failed to load deepfake detection model: {e}")
            self._model_loaded = False
            raise
    
    @property
    def model(self):
        """Get the loaded model, loading it if necessary."""
        if not self._model_loaded:
            return self.load_model()
        return self._model
    
    def is_loaded(self):
        """Check if model is loaded."""
        return self._model_loaded


# Global singleton instance
deepfake_detector = DeepfakeDetectorSingleton()
