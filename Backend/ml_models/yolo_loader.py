"""
YOLO Pet Type Detection Model Loader
Singleton pattern to load YOLO model once and reuse for all requests
"""
import os
import logging
from pathlib import Path
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

class YOLOModelLoader:
    """Singleton class to load and manage YOLO model"""
    
    _instance = None
    _model = None
    
    # YOLO model classes - exact order matters!
    # These indices MUST match your model's training configuration
    CLASSES = [
        'dog',          # 0
        'cat',          # 1
        'horse',        # 2
        'cow',          # 3
        'sheep',        # 4
        'goat',         # 5
        'bird',         # 6
        'rabbit',       # 7
        'hamster',      # 8
        'iguana',       # 9
        'sugar_glider'  # 10
    ]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(YOLOModelLoader, cls).__new__(cls)
        return cls._instance
    
    def load_model(self):
        """Load YOLO model if not already loaded"""
        if self._model is not None:
            logger.info("YOLO model already loaded, reusing existing instance")
            return self._model
        
        try:
            # Import ultralytics YOLO
            from ultralytics import YOLO
            
            # Get model path
            current_dir = Path(__file__).parent
            model_path = current_dir / 'best.pt'
            
            if not model_path.exists():
                raise FileNotFoundError(
                    f"YOLO model file not found at {model_path}. "
                    f"Please place best.pt in {current_dir}"
                )
            
            logger.info(f"Loading YOLO model from {model_path}")
            self._model = YOLO(str(model_path))
            logger.info("✅ YOLO model loaded successfully")
            
            return self._model
            
        except ImportError as e:
            logger.error("ultralytics package not installed. Install with: pip install ultralytics")
            raise ImportError(
                "ultralytics package required for YOLO detection. "
                "Install with: pip install ultralytics"
            ) from e
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {str(e)}")
            raise
    
    def predict(self, image_file):
        """
        Run YOLO prediction on image
        
        Args:
            image_file: File object or path to image
            
        Returns:
            dict: {
                'detected_class': str,
                'confidence': float,
                'all_detections': list of dicts
            }
        """
        try:
            model = self.load_model()
            
            # Open image
            if hasattr(image_file, 'read'):
                # File object
                image = Image.open(image_file)
            else:
                # File path
                image = Image.open(image_file)
            
            # Run inference
            results = model(image, verbose=False)
            
            # Process results
            if len(results) == 0 or len(results[0].boxes) == 0:
                logger.warning("No objects detected in image")
                return {
                    'detected_class': None,
                    'confidence': 0.0,
                    'all_detections': []
                }
            
            # Get all detections
            all_detections = []
            for box in results[0].boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = self.CLASSES[class_id] if class_id < len(self.CLASSES) else 'unknown'
                
                all_detections.append({
                    'class': class_name,
                    'confidence': confidence
                })
            
            # Sort by confidence and get top detection
            all_detections.sort(key=lambda x: x['confidence'], reverse=True)
            top_detection = all_detections[0]
            
            logger.info(
                f"YOLO detected: {top_detection['class']} "
                f"(confidence: {top_detection['confidence']:.2f})"
            )
            
            return {
                'detected_class': top_detection['class'],
                'confidence': top_detection['confidence'],
                'all_detections': all_detections
            }
            
        except Exception as e:
            logger.error(f"YOLO prediction failed: {str(e)}")
            raise
    
    def normalize_pet_type(self, pet_type):
        """
        Normalize pet type for comparison
        Handles: case insensitivity, spaces vs underscores
        
        Args:
            pet_type: User input or detected class
            
        Returns:
            str: Normalized pet type
        """
        if not pet_type:
            return ""
        
        # Convert to lowercase and replace spaces with underscores
        normalized = pet_type.lower().strip().replace(' ', '_')
        return normalized
    
    def compare_pet_types(self, detected_type, user_input):
        """
        Compare detected pet type with user input
        
        Args:
            detected_type: YOLO detected class
            user_input: User entered pet type
            
        Returns:
            bool: True if match, False otherwise
        """
        if not detected_type or not user_input:
            return False
        
        normalized_detected = self.normalize_pet_type(detected_type)
        normalized_input = self.normalize_pet_type(user_input)
        
        is_match = normalized_detected == normalized_input
        
        logger.info(
            f"Pet type comparison: detected='{normalized_detected}' "
            f"vs input='{normalized_input}' -> match={is_match}"
        )
        
        return is_match


# Global instance
yolo_loader = YOLOModelLoader()
