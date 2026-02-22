"""
Breed Classification Model Loader
Conditional loading based on pet type (dog, horse, rabbit, bird only)
"""
import os
import logging
from pathlib import Path
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class BreedClassifier:
    """Singleton class to load and manage breed classification models"""
    
    _instance = None
    _models = {}  # Cache loaded models by pet type
    
    # Supported pet types for breed classification
    SUPPORTED_TYPES = ['dog', 'horse', 'rabbit', 'bird']
    
    # Model filenames
    MODEL_FILES = {
        'dog': 'dog_breed_model.pth',
        'horse': 'horse_breed_model.pth',
        'rabbit': 'rabbit_breed_model.pth',
        'bird': 'bird_breed_model.pth',
    }
    
    # Breed classes for each pet type (fallback if not in checkpoint)
    BREED_CLASSES = {
        'dog': [
            'labrador_retriever', 'german_shepherd', 'golden_retriever', 
            'beagle', 'rottweiler', 'rajapalayam', 'chippiparai', 
            'doberman', 'pug', 'siberian_husky'
        ],
        'horse': [
            'arabian', 'friesian', 'appaloosa', 'akhal_teke', 
            'percheron', 'orlov_trotter', 'vladimir_heavy_draft'
        ],
        'rabbit': [
            'californian', 'holland_lop', 'lionhead', 'new_zealand'
        ],
        'bird': [
            'Chicken-Birds', 'Layers', 'crow', 'owl', 'parrot', 
            'pigeon', 'sparrow', 'swan'
        ],
    }
    
    # ImageNet normalization (standard preprocessing)
    NORMALIZE_MEAN = [0.485, 0.456, 0.406]
    NORMALIZE_STD = [0.229, 0.224, 0.225]
    IMAGE_SIZE = 224
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BreedClassifier, cls).__new__(cls)
        return cls._instance
    
    def is_supported(self, pet_type):
        """Check if pet type supports breed classification"""
        normalized = self.normalize_pet_type(pet_type)
        return normalized in self.SUPPORTED_TYPES
    
    def normalize_pet_type(self, pet_type):
        """Normalize pet type for comparison"""
        if not pet_type:
            return ""
        return pet_type.lower().strip().replace(' ', '_')
    
    def load_model(self, pet_type):
        """
        Load breed classification model for specific pet type
        
        Args:
            pet_type: Type of pet (dog, horse, rabbit, bird)
            
        Returns:
            tuple: (model, class_names) or (None, None) if not supported
        """
        normalized_type = self.normalize_pet_type(pet_type)
        
        # Check if supported
        if normalized_type not in self.SUPPORTED_TYPES:
            logger.info(f"Breed classification not supported for: {pet_type}")
            return None, None
        
        # Check if already loaded
        if normalized_type in self._models:
            logger.info(f"Reusing cached {normalized_type} breed model")
            return self._models[normalized_type]
        
        try:
            # Get model path
            current_dir = Path(__file__).parent
            model_filename = self.MODEL_FILES[normalized_type]
            model_path = current_dir / model_filename
            
            if not model_path.exists():
                logger.warning(
                    f"Breed model not found: {model_path}. "
                    f"Please upload {model_filename} to {current_dir}"
                )
                return None, None
            
            logger.info(f"Loading {normalized_type} breed model from {model_path}")
            
            # Load checkpoint
            checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
            
            # Get class names from checkpoint
            if 'class_names' in checkpoint:
                class_names = checkpoint['class_names']
            else:
                # Fallback to predefined classes
                class_names = self.BREED_CLASSES[normalized_type]
                logger.warning(f"Using predefined class names for {normalized_type}")
            
            num_classes = len(class_names)
            
            # Detect model architecture from checkpoint keys
            state_dict_keys = list(checkpoint['model_state_dict'].keys() if 'model_state_dict' in checkpoint else checkpoint.keys())
            
            # Determine architecture based on layer names
            if any('features.0.0.weight' in k for k in state_dict_keys):
                # MobileNetV2 architecture
                logger.info(f"Detected MobileNetV2 architecture for {normalized_type}")
                model = models.mobilenet_v2(pretrained=False)
                model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
            elif any('layer1.2' in k for k in state_dict_keys):
                # ResNet50 architecture (has 3 blocks in layer1)
                logger.info(f"Detected ResNet50 architecture for {normalized_type}")
                model = models.resnet50(pretrained=False)
                model.fc = nn.Linear(model.fc.in_features, num_classes)
            else:
                # Default to ResNet18
                logger.info(f"Using ResNet18 architecture for {normalized_type}")
                model = models.resnet18(pretrained=False)
                model.fc = nn.Linear(model.fc.in_features, num_classes)
            
            # Load weights
            if 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
            else:
                model.load_state_dict(checkpoint)
            
            model.eval()  # Set to evaluation mode
            
            # Cache the model
            self._models[normalized_type] = (model, class_names)
            
            logger.info(
                f"✅ {normalized_type.capitalize()} breed model loaded successfully. "
                f"Classes: {len(class_names)}"
            )
            
            return model, class_names
            
        except Exception as e:
            logger.error(f"Failed to load {normalized_type} breed model: {e}", exc_info=True)
            return None, None
    
    def preprocess_image(self, image_file):
        """
        Preprocess image for breed classification
        
        Args:
            image_file: File object or path to image
            
        Returns:
            torch.Tensor: Preprocessed image tensor
        """
        try:
            # Open image
            if hasattr(image_file, 'read'):
                image = Image.open(image_file).convert('RGB')
            else:
                image = Image.open(image_file).convert('RGB')
            
            # Define transforms
            transform = transforms.Compose([
                transforms.Resize((self.IMAGE_SIZE, self.IMAGE_SIZE)),
                transforms.ToTensor(),
                transforms.Normalize(mean=self.NORMALIZE_MEAN, std=self.NORMALIZE_STD)
            ])
            
            # Apply transforms
            image_tensor = transform(image)
            image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
            
            return image_tensor
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise
    
    def predict(self, image_file, pet_type):
        """
        Predict breed for given image and pet type
        
        Args:
            image_file: File object or path to image
            pet_type: Type of pet (dog, horse, rabbit, bird)
            
        Returns:
            dict: {
                'predicted_breed': str,
                'confidence': float,
                'all_predictions': list of dicts,
                'is_supported': bool,
                'low_confidence': bool
            }
        """
        normalized_type = self.normalize_pet_type(pet_type)
        
        # Check if supported
        if not self.is_supported(pet_type):
            return {
                'predicted_breed': None,
                'confidence': 0.0,
                'all_predictions': [],
                'is_supported': False,
                'low_confidence': False,
                'message': f'Breed classification not supported for {pet_type}'
            }
        
        try:
            # Load model
            model, class_names = self.load_model(pet_type)
            
            if model is None or class_names is None:
                return {
                    'predicted_breed': None,
                    'confidence': 0.0,
                    'all_predictions': [],
                    'is_supported': True,
                    'low_confidence': False,
                    'message': f'Breed model not available for {pet_type}'
                }
            
            # Preprocess image
            image_tensor = self.preprocess_image(image_file)
            
            # Run inference
            with torch.no_grad():
                outputs = model(image_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                probs = probabilities[0].cpu().numpy()
            
            # Get top predictions
            top_indices = np.argsort(probs)[::-1][:5]  # Top 5
            all_predictions = [
                {
                    'breed': class_names[idx],
                    'confidence': float(probs[idx])
                }
                for idx in top_indices
            ]
            
            # Get top prediction
            top_breed = class_names[top_indices[0]]
            top_confidence = float(probs[top_indices[0]])
            
            # Check if low confidence
            low_confidence = top_confidence < 0.50
            
            logger.info(
                f"Breed prediction for {pet_type}: {top_breed} "
                f"(confidence: {top_confidence:.2%})"
            )
            
            return {
                'predicted_breed': top_breed,
                'confidence': top_confidence,
                'all_predictions': all_predictions,
                'is_supported': True,
                'low_confidence': low_confidence,
                'message': 'Breed classified successfully'
            }
            
        except Exception as e:
            logger.error(f"Breed prediction failed: {e}", exc_info=True)
            raise
    
    def normalize_breed_name(self, breed_name):
        """
        Normalize breed name for comparison
        
        Args:
            breed_name: Breed name to normalize
            
        Returns:
            str: Normalized breed name
        """
        if not breed_name:
            return ""
        
        # Convert to lowercase, replace spaces/hyphens with underscores
        normalized = breed_name.lower().strip()
        normalized = normalized.replace(' ', '_').replace('-', '_')
        
        return normalized
    
    def compare_breeds(self, predicted_breed, user_input):
        """
        Compare predicted breed with user input
        
        Args:
            predicted_breed: Model predicted breed
            user_input: User entered breed
            
        Returns:
            bool: True if match, False otherwise
        """
        if not predicted_breed or not user_input:
            return False
        
        normalized_predicted = self.normalize_breed_name(predicted_breed)
        normalized_input = self.normalize_breed_name(user_input)
        
        is_match = normalized_predicted == normalized_input
        
        logger.info(
            f"Breed comparison: predicted='{normalized_predicted}' "
            f"vs input='{normalized_input}' -> match={is_match}"
        )
        
        return is_match


# Global instance
breed_classifier = BreedClassifier()
