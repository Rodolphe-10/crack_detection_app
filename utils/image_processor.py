#!/usr/bin/env python3
"""
Traitement d'images pour l'application
=====================================

Module contenant les fonctions de traitement d'images
pour l'analyse de fissures.
"""

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageEnhance
import albumentations as A
from albumentations.pytorch import ToTensorV2
from typing import Tuple, Optional, List, Dict
import matplotlib.pyplot as plt
import seaborn as sns

from config.config import AppConfig
import logging

logger = logging.getLogger(__name__)

def debug_tensor_shape(tensor: torch.Tensor, context: str = ""):
    """Fonction d'aide pour débugger les formes de tenseurs."""
    logger.info(f"Debug tenseur {context}: forme={tensor.shape}, dim={tensor.dim()}, dtype={tensor.dtype}")
    if tensor.dim() >= 1:
        logger.info(f"  Dimensions détaillées: {[tensor.size(i) for i in range(tensor.dim())]}")

def create_transforms():
    """Crée les transformations pour l'inférence."""
    transform = A.Compose([
        A.Resize(AppConfig.IMAGE_SIZE, AppConfig.IMAGE_SIZE),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])
    return transform

def preprocess_image_for_classification(image: np.ndarray) -> torch.Tensor:
    """Prétraite une image pour la classification avec gestion robuste des dimensions."""
    transform = create_transforms()
    
    # Convertir en RGB si nécessaire
    if len(image.shape) == 3 and image.shape[2] == 3:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        image_rgb = image
    
    # Appliquer les transformations
    augmented = transform(image=image_rgb)
    image_tensor = augmented["image"]
    
    # Debug de la forme initiale
    original_shape = image_tensor.shape
    debug_tensor_shape(image_tensor, "après transformation")
    
    # Correction robuste des dimensions
    # Supprimer toutes les dimensions de taille 1 inutiles
    while image_tensor.dim() > 4:
        # Si on a plus de 4 dimensions, supprimer les dimensions de taille 1
        squeeze_dims = [i for i in range(image_tensor.dim()) if image_tensor.size(i) == 1]
        if squeeze_dims:
            # Supprimer la première dimension de taille 1 trouvée
            image_tensor = image_tensor.squeeze(squeeze_dims[0])
            debug_tensor_shape(image_tensor, f"après suppression dimension {squeeze_dims[0]}")
        else:
            # Si pas de dimension de taille 1, c'est un vrai problème
            raise ValueError(f"Trop de dimensions sans dimension unitaire: {image_tensor.shape}")
    
    # S'assurer qu'on a exactement 4 dimensions [batch, channels, height, width]
    if image_tensor.dim() == 3:  # [C, H, W] -> [1, C, H, W]
        image_tensor = image_tensor.unsqueeze(0)
        debug_tensor_shape(image_tensor, "après ajout dimension batch")
    elif image_tensor.dim() == 2:  # [H, W] -> [1, 1, H, W]
        image_tensor = image_tensor.unsqueeze(0).unsqueeze(0)
        debug_tensor_shape(image_tensor, "après ajout dimensions batch et channel")
    elif image_tensor.dim() == 1:  # Cas exceptionnel
        raise ValueError(f"Tenseur 1D non valide: {image_tensor.shape}")
    
    # Vérification finale stricte
    if image_tensor.dim() != 4:
        raise ValueError(f"Nombre de dimensions invalide: {image_tensor.dim()}. Attendu: 4")
    
    # Vérifier le format [batch, channels, height, width]
    if image_tensor.size(1) != 3:
        logger.warning(f"Nombre de canaux inattendu: {image_tensor.size(1)}, attendu: 3")
        # Si on a 1 canal, répliquer pour avoir 3 canaux
        if image_tensor.size(1) == 1:
            image_tensor = image_tensor.repeat(1, 3, 1, 1)
            debug_tensor_shape(image_tensor, "après réplication des canaux")
    
    # Vérification finale
    expected_shape = (1, 3, AppConfig.IMAGE_SIZE, AppConfig.IMAGE_SIZE)
    if tuple(image_tensor.shape) != expected_shape:
        logger.warning(f"Forme finale inattendue: {image_tensor.shape}, attendu: {expected_shape}")
    
    debug_tensor_shape(image_tensor, "final")
    return image_tensor

def preprocess_image_for_segmentation(image: np.ndarray) -> torch.Tensor:
    """Prétraite une image pour la segmentation."""
    # Même préprocessing que pour la classification
    return preprocess_image_for_classification(image)

def safe_model_inference(model, input_tensor: torch.Tensor, model_type: str = "unknown"):
    """
    Effectue une inférence de modèle de manière sécurisée avec gestion d'erreurs de dimensions.
    
    Args:
        model: Le modèle PyTorch
        input_tensor: Le tenseur d'entrée
        model_type: Type de modèle pour le debug
        
    Returns:
        Le résultat de l'inférence ou None en cas d'erreur
    """
    debug_tensor_shape(input_tensor, f"entrée {model_type}")
    
    try:
        # Première tentative d'inférence
        with torch.no_grad():
            output = model(input_tensor)
        debug_tensor_shape(output, f"sortie {model_type}")
        return output
        
    except RuntimeError as e:
        error_msg = str(e)
        logger.warning(f"Erreur d'inférence {model_type}: {error_msg}")
        
        # Gestion spécifique des erreurs de conv2d
        if "conv2d" in error_msg and "input of size" in error_msg:
            logger.info("Tentative de correction des dimensions pour conv2d...")
            
            # Essayer de corriger les dimensions en supprimant les dimensions unitaires
            corrected_tensor = input_tensor.clone()
            
            # Supprimer les dimensions unitaires au début
            while corrected_tensor.dim() > 4 and corrected_tensor.size(0) == 1:
                corrected_tensor = corrected_tensor.squeeze(0)
                debug_tensor_shape(corrected_tensor, f"correction {model_type}")
            
            # S'assurer qu'on a la bonne forme [batch, channels, height, width]
            if corrected_tensor.dim() == 3:
                corrected_tensor = corrected_tensor.unsqueeze(0)
                debug_tensor_shape(corrected_tensor, f"batch ajouté {model_type}")
            
            try:
                # Deuxième tentative avec le tenseur corrigé
                with torch.no_grad():
                    output = model(corrected_tensor)
                debug_tensor_shape(output, f"sortie corrigée {model_type}")
                logger.info(f"Correction réussie pour {model_type}")
                return output
                
            except Exception as e2:
                logger.error(f"Échec de la correction pour {model_type}: {e2}")
                return None
        else:
            logger.error(f"Erreur non récupérable pour {model_type}: {error_msg}")
            return None
    
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'inférence {model_type}: {e}")
        return None

def run_classification_analysis(model, image: np.ndarray):
    """
    Lance l'analyse de classification de manière sécurisée.
    
    Args:
        model: Le modèle de classification
        image: L'image à analyser
        
    Returns:
        Tuple (pred_class, confidence, probabilities) ou None en cas d'erreur
    """
    try:
        # Préprocessing
        input_tensor = preprocess_image_for_classification(image)
        
        # Inférence sécurisée
        output = safe_model_inference(model, input_tensor, "classification")
        if output is None:
            return None
        
        # Post-processing
        probabilities = torch.softmax(output, dim=1)
        confidence, pred_class = torch.max(probabilities, dim=1)
        
        return pred_class.item(), confidence.item(), probabilities.squeeze().cpu().numpy()
        
    except Exception as e:
        logger.error(f"Erreur dans run_classification_analysis: {e}")
        return None

def run_segmentation_analysis(model, image: np.ndarray):
    """
    Lance l'analyse de segmentation de manière sécurisée.
    
    Args:
        model: Le modèle de segmentation
        image: L'image à analyser
        
    Returns:
        Le masque de segmentation ou None en cas d'erreur
    """
    try:
        # Préprocessing
        input_tensor = preprocess_image_for_segmentation(image)
        
        # Inférence sécurisée
        output = safe_model_inference(model, input_tensor, "segmentation")
        if output is None:
            return None
        
        # Post-processing
        if isinstance(output, dict) and 'out' in output:
            mask = output['out']
        else:
            mask = output
            
        # Convertir en masque binaire
        mask = torch.sigmoid(mask)
        mask = (mask > 0.5).float()
        
        return mask.squeeze().cpu().numpy()
        
    except Exception as e:
        logger.error(f"Erreur dans run_segmentation_analysis: {e}")
        return None

def safe_model_inference(model, input_tensor: torch.Tensor, model_type: str = "unknown"):
    """
    Exécute l'inférence du modèle avec gestion d'erreur robuste.
    
    Args:
        model: Le modèle PyTorch
        input_tensor: Tenseur d'entrée
        model_type: Type de modèle pour les messages d'erreur
    
    Returns:
        Résultat de l'inférence ou None en cas d'erreur
    """
    try:
        # Debug des dimensions avant inférence
        debug_tensor_shape(input_tensor, f"avant inférence {model_type}")
        
        # Vérifications préliminaires
        if input_tensor.dim() not in [3, 4]:
            raise ValueError(f"Format d'entrée invalide: {input_tensor.shape}")
        
        # S'assurer que le tenseur est au bon format [batch, channels, height, width]
        if input_tensor.dim() == 3:
            input_tensor = input_tensor.unsqueeze(0)
        
        # Inférence
        with torch.no_grad():
            output = model(input_tensor)
        
        debug_tensor_shape(output, f"sortie {model_type}")
        return output
        
    except RuntimeError as e:
        error_msg = str(e)
        if "Expected 3D" in error_msg and "4D" in error_msg and "conv2d" in error_msg:
            logger.error(f"Erreur de dimension conv2d détectée pour {model_type}")
            logger.error(f"Forme d'entrée problématique: {input_tensor.shape}")
            logger.error("Tentative de correction automatique...")
            
            # Tentative de correction
            try:
                # Enlever toutes les dimensions de taille 1 sauf la batch dimension
                corrected_tensor = input_tensor.squeeze()
                if corrected_tensor.dim() == 3:  # [C, H, W]
                    corrected_tensor = corrected_tensor.unsqueeze(0)  # [1, C, H, W]
                
                logger.info(f"Forme corrigée: {corrected_tensor.shape}")
                
                with torch.no_grad():
                    output = model(corrected_tensor)
                
                logger.info("Correction réussie!")
                return output
                
            except Exception as correction_error:
                logger.error(f"Échec de la correction automatique: {correction_error}")
                return None
        else:
            logger.error(f"Erreur d'inférence {model_type}: {e}")
            return None
    
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'inférence {model_type}: {e}")
        return None





def postprocess_segmentation_mask(mask: torch.Tensor, 
                                target_size: Tuple[int, int],
                                threshold: float = 0.5) -> np.ndarray:
    """Post-traite le masque de segmentation."""
    # Convertir en numpy
    mask_np = mask.squeeze().cpu().numpy()
    
    # Appliquer le seuil
    mask_binary = (mask_np > threshold).astype(np.uint8)
    
    # Redimensionner à la taille cible
    mask_resized = cv2.resize(mask_binary, target_size, interpolation=cv2.INTER_NEAREST)
    
    return mask_resized

def run_opencv_segmentation(image: np.ndarray) -> np.ndarray:
    """
    Segmentation de fissures (style binaire net): fond noir, fissures blanches 1-2 px.
    Retourne un masque uint8 en 0/255.
    """
    try:
        from skimage.morphology import skeletonize, remove_small_objects
        from skimage.util import img_as_bool
        
        # Grayscale
        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Contraste + débruitage léger
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        enhanced = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)

        # Mise en évidence des structures fines (black-hat)
        kernel_bh = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        blackhat = cv2.morphologyEx(enhanced, cv2.MORPH_BLACKHAT, kernel_bh)

        # Seuillage adaptatif (blanc = fissure)
        thresh = cv2.adaptiveThreshold(
            blackhat, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, -2
        )

        # Nettoyage morphologique
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Suppression des petits objets (moins de N pixels)
        bool_img = img_as_bool(closed)
        cleaned_bool = remove_small_objects(bool_img, min_size=40)

        # Squelettisation pour traits fins
        skeleton = skeletonize(cleaned_bool)

        # Filtrage par composantes: ne garder que les segments longs et allongés
        from skimage.measure import label, regionprops
        labeled = label(skeleton)
        filtered = np.zeros_like(skeleton, dtype=bool)

        # Seuils (ajustables)
        min_length_px = max(40, int(0.02 * max(skeleton.shape)))  # longueur minimale
        min_eccentricity = 0.9  # très allongé

        for region in regionprops(labeled):
            # nombre de pixels squelettiques ~ longueur approximative
            length = region.area
            ecc = getattr(region, 'eccentricity', 0.0)
            if length >= min_length_px and ecc >= min_eccentricity:
                coords = region.coords
                filtered[coords[:, 0], coords[:, 1]] = True

        # Option: épaissir légèrement (1 px) pour meilleure visibilité
        filtered_uint8 = (filtered.astype(np.uint8)) * 255
        kernel_vis = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        mask_binary = cv2.dilate(filtered_uint8, kernel_vis, iterations=1)
        return mask_binary

    except Exception as e:
        logger.error(f"Erreur dans la segmentation OpenCV: {e}")
        base = image[:,:,0] if image.ndim == 3 else image
        return np.zeros_like(base, dtype=np.uint8)

def enhance_image_quality(image: np.ndarray) -> np.ndarray:
    """Améliore la qualité de l'image pour une meilleure détection."""
    # Convertir en PIL pour les améliorations
    pil_image = Image.fromarray(image)
    
    # Améliorer le contraste
    enhancer = ImageEnhance.Contrast(pil_image)
    enhanced = enhancer.enhance(1.2)
    
    # Améliorer la netteté
    enhancer = ImageEnhance.Sharpness(enhanced)
    enhanced = enhancer.enhance(1.1)
    
    # Retourner en numpy
    return np.array(enhanced)

def calculate_crack_statistics(mask: np.ndarray, 
                             image_shape: Tuple[int, int],
                             pixel_size_mm: float = 1.0) -> Dict:
    """Calcule des statistiques détaillées sur les fissures."""
    if mask is None or np.sum(mask) == 0:
        return {
            'total_area_mm2': 0.0,
            'total_length_mm': 0.0,
            'max_width_mm': 0.0,
            'mean_width_mm': 0.0,
            'crack_density': 0.0,
            'num_segments': 0,
            'severity_level': 'Aucune fissure'
        }
    
    # Calculer la surface totale
    crack_pixels = np.sum(mask > 0)
    total_area_mm2 = crack_pixels * (pixel_size_mm ** 2)
    
    # Préparer un masque binaire uint8 (0/255) pour OpenCV
    if mask.dtype != np.uint8:
        mask_u8 = ((mask > 0).astype(np.uint8)) * 255
    else:
        # S'assurer d'une vraie binaire 0/255
        mask_u8 = (mask > 0).astype(np.uint8) * 255
    mask_u8 = np.ascontiguousarray(mask_u8)
    
    # Analyser les contours
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    total_length_mm = 0
    widths = []
    valid_segments = 0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > AppConfig.MIN_CONTOUR_AREA:
            perimeter = cv2.arcLength(contour, False)
            total_length_mm += perimeter * pixel_size_mm
            
            # Estimer la largeur moyenne
            if perimeter > 0:
                width = area / perimeter
                widths.append(width * pixel_size_mm)
            
            valid_segments += 1
    
    # Calculer les statistiques
    max_width_mm = max(widths) if widths else 0.0
    mean_width_mm = np.mean(widths) if widths else 0.0
    
    # Densité de fissuration (pourcentage de l'image)
    total_image_pixels = image_shape[0] * image_shape[1]
    crack_density = (crack_pixels / total_image_pixels) * 100
    
    # Niveau de sévérité
    if crack_density < 1.0:
        severity_level = 'Légère'
    elif crack_density < 5.0:
        severity_level = 'Modérée'
    elif crack_density < 15.0:
        severity_level = 'Sévère'
    else:
        severity_level = 'Critique'
    
    return {
        'total_area_mm2': total_area_mm2,
        'total_length_mm': total_length_mm,
        'max_width_mm': max_width_mm,
        'mean_width_mm': mean_width_mm,
        'crack_density': crack_density,
        'num_segments': valid_segments,
        'severity_level': severity_level
    }

def create_enhanced_overlay(original_image: np.ndarray,
                          mask: np.ndarray,
                          alpha: float = 0.6,
                          colormap: str = 'hot') -> np.ndarray:
    """Crée un overlay amélioré avec différentes options de visualisation."""
    if mask is None:
        return original_image
    
    # S'assurer que l'image est en RGB/BGR
    if len(original_image.shape) == 2:
        original_image = cv2.cvtColor(original_image, cv2.COLOR_GRAY2BGR)
    
    # Redimensionner le masque si nécessaire et s'assurer qu'il est 2D
    if mask.shape[:2] != original_image.shape[:2]:
        mask = cv2.resize(mask, (original_image.shape[1], original_image.shape[0]))
    
    # S'assurer que le masque est 2D
    if len(mask.shape) > 2:
        mask = mask[:, :, 0] if mask.shape[2] == 1 else np.mean(mask, axis=2)
    
    # Créer le masque coloré selon le colormap choisi
    if colormap == 'hot':
        # Rouge vif pour les fissures
        overlay = original_image.copy()
        # S'assurer que le masque est binaire et de la bonne taille
        binary_mask = (mask > 0).astype(bool)
        overlay[binary_mask] = [255, 0, 0]  # Rouge
    elif colormap == 'rainbow':
        # Utiliser un colormap plus complexe
        mask_colored = cv2.applyColorMap((mask * 255).astype(np.uint8), cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(original_image, 1-alpha, mask_colored, alpha, 0)
        return overlay
    else:
        # Défaut: rouge
        overlay = original_image.copy()
        # S'assurer que le masque est binaire et de la bonne taille
        binary_mask = (mask > 0).astype(bool)
        overlay[binary_mask] = AppConfig.MASK_COLORS['crack']
    
    # Combiner avec l'image originale
    result = cv2.addWeighted(original_image, 1-alpha, overlay, alpha, 0)
    
    return result

def create_contour_visualization(original_image: np.ndarray,
                               mask: np.ndarray,
                               thickness: int = 2) -> np.ndarray:
    """Crée une visualisation avec contours des fissures."""
    if mask is None:
        return original_image
    
    result = original_image.copy()
    
    # Trouver les contours
    # Assurer un masque uint8 binaire pour les contours
    if mask.dtype != np.uint8:
        mask_u8 = ((mask > 0).astype(np.uint8)) * 255
    else:
        mask_u8 = (mask > 0).astype(np.uint8) * 255
    mask_u8 = np.ascontiguousarray(mask_u8)
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Dessiner les contours
    cv2.drawContours(result, contours, -1, AppConfig.MASK_COLORS['crack'], thickness)
    
    return result

def analyze_crack_orientation(mask: np.ndarray) -> Dict:
    """Analyse l'orientation des fissures."""
    if mask is None or np.sum(mask) == 0:
        return {'dominant_orientation': 0, 'orientation_std': 0}
    
    # Trouver les contours
    # Assurer un masque uint8 binaire pour les contours
    if mask.dtype != np.uint8:
        mask_u8 = ((mask > 0).astype(np.uint8)) * 255
    else:
        mask_u8 = (mask > 0).astype(np.uint8) * 255
    mask_u8 = np.ascontiguousarray(mask_u8)
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    orientations = []
    
    for contour in contours:
        if len(contour) >= 5:  # Minimum pour fitEllipse
            try:
                ellipse = cv2.fitEllipse(contour)
                angle = ellipse[2]  # Angle de l'ellipse
                orientations.append(angle)
            except:
                continue
    
    if orientations:
        dominant_orientation = np.mean(orientations)
        orientation_std = np.std(orientations)
    else:
        dominant_orientation = 0
        orientation_std = 0
    
    return {
        'dominant_orientation': dominant_orientation,
        'orientation_std': orientation_std
    }

def create_analysis_report_image(original_image: np.ndarray,
                               mask: np.ndarray,
                               statistics: Dict,
                               classification_result: Tuple) -> np.ndarray:
    """Crée une image de rapport complet."""
    # Créer une figure avec subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Image originale
    axes[0, 0].imshow(cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB))
    axes[0, 0].set_title('Image Originale')
    axes[0, 0].axis('off')
    
    # Masque de segmentation
    if mask is not None:
        axes[0, 1].imshow(mask, cmap='Reds')
        axes[0, 1].set_title('Masque de Segmentation')
        axes[0, 1].axis('off')
        
        # Overlay
        overlay = create_enhanced_overlay(original_image, mask)
        axes[1, 0].imshow(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
        axes[1, 0].set_title('Overlay')
        axes[1, 0].axis('off')
    else:
        axes[0, 1].text(0.5, 0.5, 'Aucune fissure\ndétectée', 
                       ha='center', va='center', transform=axes[0, 1].transAxes)
        axes[0, 1].axis('off')
        axes[1, 0].axis('off')
    
    # Statistiques
    axes[1, 1].axis('off')
    
    # Préparer le texte des statistiques
    pred_class, confidence, _ = classification_result
    class_name = AppConfig.CLASSIFICATION_CLASSES[pred_class]
    
    stats_text = f"""Résultats d'Analyse:
    
Classification: {class_name}
Confiance: {confidence:.1%}

Statistiques:
Surface: {statistics.get('total_area_mm2', 0):.1f} mm²
Longueur: {statistics.get('total_length_mm', 0):.1f} mm
Largeur max: {statistics.get('max_width_mm', 0):.2f} mm
Densité: {statistics.get('crack_density', 0):.2f}%
Sévérité: {statistics.get('severity_level', 'N/A')}
Segments: {statistics.get('num_segments', 0)}
"""
    
    axes[1, 1].text(0.1, 0.9, stats_text, transform=axes[1, 1].transAxes,
                    fontsize=10, verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    
    # Convertir en image numpy
    fig.canvas.draw()
    img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    
    plt.close(fig)
    
    return img

def batch_process_images(images: List[np.ndarray], 
                        classification_model,
                        segmentation_model,
                        device: str) -> List[Dict]:
    """Traite un batch d'images et retourne les résultats."""
    results = []
    
    for i, image in enumerate(images):
        try:
            # Préprocessing
            image_tensor = preprocess_image_for_classification(image)
            
            # Classification
            classification_model.eval()
            with torch.no_grad():
                image_tensor_device = image_tensor.to(device)
                outputs = classification_model(image_tensor_device)
                probabilities = F.softmax(outputs, dim=1)
                predicted_class = torch.argmax(outputs, dim=1)
                confidence = torch.max(probabilities, dim=1)[0]
            
            classification_result = (
                predicted_class.item(),
                confidence.item(),
                probabilities.cpu().numpy()[0]
            )
            
            # Segmentation si fissure détectée
            mask = None
            statistics = {}
            
            if predicted_class.item() == 1:  # Fissure détectée
                segmentation_model.eval()
                with torch.no_grad():
                    seg_outputs = segmentation_model(image_tensor_device)
                    mask_tensor = torch.sigmoid(seg_outputs)
                    mask = (mask_tensor > 0.5).float().squeeze().cpu().numpy()
                
                # Calculer les statistiques
                statistics = calculate_crack_statistics(mask, image.shape[:2])
            
            results.append({
                'index': i,
                'classification': classification_result,
                'mask': mask,
                'statistics': statistics,
                'status': 'success'
            })
            
        except Exception as e:
            results.append({
                'index': i,
                'error': str(e),
                'status': 'error'
            })
    
    return results

def validate_image_file(image_array):
    """Valide la qualité et la taille de l'image."""
    try:
        if image_array is None:
            return False, "Image vide"
        
        # Vérifier les dimensions
        if len(image_array.shape) < 2:
            return False, "Image invalide (dimensions insuffisantes)"
        
        # Vérifier la taille minimale
        min_size = 50
        if image_array.shape[0] < min_size or image_array.shape[1] < min_size:
            return False, f"Image trop petite (minimum {min_size}x{min_size} pixels)"
        
        # Vérifier la taille maximale
        max_size = 5000
        if image_array.shape[0] > max_size or image_array.shape[1] > max_size:
            return False, f"Image trop grande (maximum {max_size}x{max_size} pixels)"
        
        return True, "Image valide"
        
    except Exception as e:
        return False, f"Erreur de validation: {str(e)}"

def validate_concrete_surface(image_array: np.ndarray) -> Tuple[bool, str]:
    """
    Valide si l'image correspond à une surface en béton.
    
    Args:
        image_array: Image numpy array
        
    Returns:
        Tuple (is_valid, message): True si c'est du béton, False sinon
    """
    try:
        if image_array is None:
            return False, "❌ Image vide"
        
        # Convertir en grayscale si nécessaire
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array.copy()
        
        # Analyse de la texture et des caractéristiques du béton
        concrete_score = 0
        total_checks = 0
        
        # Vérification 1: Distribution des niveaux de gris (béton = gris uniforme)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_norm = hist.flatten() / np.sum(hist)
        
        # Le béton a généralement une distribution plus uniforme
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        if 4.0 < entropy < 7.5:  # Plage plus stricte pour le béton
            concrete_score += 1
        total_checks += 1
        
        # Vérification 2: Variance locale (béton = texture fine)
        kernel_size = 5
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
        blurred = cv2.filter2D(gray, -1, kernel)
        variance = np.var(gray.astype(float) - blurred.astype(float))
        
        if 100 < variance < 2000:  # Plage plus stricte pour le béton
            concrete_score += 1
        total_checks += 1
        
        # Vérification 3: Détection de contours (béton = contours fins et nombreux)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        
        if 0.01 < edge_density < 0.15:  # Plage plus stricte pour le béton
            concrete_score += 1
        total_checks += 1
        
        # Vérification 4: Analyse des couleurs (béton = tons gris/beiges)
        if len(image_array.shape) == 3:
            # Convertir en HSV pour analyser la saturation
            hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
            saturation = hsv[:, :, 1]
            avg_saturation = np.mean(saturation)
            
            # Le béton a généralement une saturation faible
            if avg_saturation < 80:  # Seuil plus strict pour les couleurs neutres
                concrete_score += 1
            total_checks += 1
            
            # Vérification 5: Analyse des canaux RGB (béton = R≈G≈B)
            r, g, b = cv2.split(image_array)
            r_mean, g_mean, b_mean = np.mean(r), np.mean(g), np.mean(b)
            
            # Vérifier si les canaux sont similaires (caractéristique du gris)
            channel_diff = max(abs(r_mean - g_mean), abs(g_mean - b_mean), abs(r_mean - b_mean))
            if channel_diff < 30:  # Seuil plus strict pour les couleurs neutres
                concrete_score += 1
            total_checks += 1
        
        # Vérification 6: Détection de motifs répétitifs (caractéristique du béton)
        # Utiliser la FFT pour détecter les motifs
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.log(np.abs(f_shift) + 1)
        
        # Le béton a généralement des motifs de fréquence moyenne
        center_freq = magnitude_spectrum[gray.shape[0]//4:3*gray.shape[0]//4, 
                                       gray.shape[1]//4:3*gray.shape[1]//4]
        avg_freq = np.mean(center_freq)
        
        if 6 < avg_freq < 15:  # Plage élargie pour le béton
            concrete_score += 1
        total_checks += 1
        
        # Calcul du score final
        confidence = concrete_score / total_checks
        
        # Seuils de décision (très stricts pour éviter les faux positifs)
        if confidence >= 0.9:  # Très strict - seulement du béton évident
            return True, f"✅ Surface en béton détectée (confiance: {confidence:.1%})"
        elif confidence >= 0.7:  # Strict - surface douteuse
            return False, f"⚠️ Surface douteuse - Veuillez utiliser une image de surface en béton claire (confiance: {confidence:.1%})"
        else:
            return False, f"❌ Cette image ne semble pas être une surface en béton. Veuillez utiliser une image de mur, sol ou structure en béton (confiance: {confidence:.1%})"
            
    except Exception as e:
        logger.error(f"Erreur lors de la validation de surface en béton: {e}")
        return False, f"❌ Erreur lors de la validation: {str(e)}"

def validate_image_for_analysis(image_array: np.ndarray, strict_validation: bool = True) -> Tuple[bool, str]:
    """
    Validation complète d'une image pour l'analyse de fissures.
    Combine la validation technique et la validation de surface en béton.
    
    Args:
        image_array: Image numpy array
        strict_validation: Si True, applique la validation stricte du béton
        
    Returns:
        Tuple (is_valid, message): True si l'image est valide pour l'analyse
    """
    # Validation technique de base
    is_valid_tech, tech_msg = validate_image_file(image_array)
    if not is_valid_tech:
        return False, tech_msg
    
    # Validation de surface en béton (optionnelle)
    if strict_validation:
        is_concrete, concrete_msg = validate_concrete_surface(image_array)
        if not is_concrete:
            return False, concrete_msg
    else:
        # Mode non-strict : accepter toutes les images techniquement valides
        concrete_msg = "⚠️ Validation du béton désactivée"
    
    return True, f"✅ Image valide pour l'analyse de fissures ({concrete_msg})"

def get_validation_details(image_array: np.ndarray) -> Dict:
    """
    Retourne des détails sur la validation de l'image.
    
    Args:
        image_array: Image numpy array
        
    Returns:
        Dict contenant les détails de validation
    """
    try:
        if image_array is None:
            return {"error": "Image vide"}
        
        # Convertir en grayscale si nécessaire
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array.copy()
        
        details = {
            "image_shape": image_array.shape,
            "is_color": len(image_array.shape) == 3,
            "size_pixels": image_array.shape[0] * image_array.shape[1]
        }
        
        # Analyse de la texture
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_norm = hist.flatten() / np.sum(hist)
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        details["entropy"] = float(entropy)
        
        # Variance locale
        kernel_size = 5
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
        blurred = cv2.filter2D(gray, -1, kernel)
        variance = np.var(gray.astype(float) - blurred.astype(float))
        details["local_variance"] = float(variance)
        
        # Densité de contours
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        details["edge_density"] = float(edge_density)
        
        # Analyse des couleurs si disponible
        if len(image_array.shape) == 3:
            hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
            saturation = hsv[:, :, 1]
            avg_saturation = np.mean(saturation)
            details["avg_saturation"] = float(avg_saturation)
            
            r, g, b = cv2.split(image_array)
            r_mean, g_mean, b_mean = np.mean(r), np.mean(g), np.mean(b)
            channel_diff = max(abs(r_mean - g_mean), abs(g_mean - b_mean), abs(r_mean - b_mean))
            details["channel_difference"] = float(channel_diff)
        
        return details
        
    except Exception as e:
        return {"error": str(e)}