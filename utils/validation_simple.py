#!/usr/bin/env python3
"""
Validation allégée pour Détection Simple et Analyse Batch.

Objectif: accepter des surfaces en béton plus variées (textures peu contrastées,
photos smartphones, éclairage variable) tout en filtrant les cas évidents non-béton.
"""

from typing import Tuple

import cv2
import numpy as np


def _validate_concrete_surface_simple(image_array: np.ndarray) -> Tuple[bool, str]:
    """Validation plus permissive de surface béton.

    Retourne (is_valid, message)
    """
    try:
        if image_array is None:
            return False, "❌ Image vide"

        # Grayscale
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array.copy()

        concrete_score = 0
        total_checks = 0

        # 1) Entropie (distribution des niveaux de gris)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_norm = hist.flatten() / max(np.sum(hist), 1)
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        # Plage plus large pour accepter murs peints/granuleux
        if 3.5 < entropy < 8.2:
            concrete_score += 1
        total_checks += 1

        # 2) Variance locale (texture)
        kernel = np.ones((5, 5), np.float32) / 25.0
        blurred = cv2.filter2D(gray, -1, kernel)
        variance = np.var(gray.astype(float) - blurred.astype(float))
        if 50 < variance < 4000:
            concrete_score += 1
        total_checks += 1

        # 3) Densité de contours
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.sum(edges > 0)) / float(edges.size)
        if 0.003 < edge_density < 0.30:
            concrete_score += 1
        total_checks += 1

        # 4) Couleurs (faible saturation, tons gris/beige)
        if len(image_array.shape) == 3:
            hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
            saturation = hsv[:, :, 1]
            avg_saturation = float(np.mean(saturation))
            if avg_saturation < 120:  # plus permissif
                concrete_score += 1
            total_checks += 1

            r, g, b = cv2.split(image_array)
            r_mean, g_mean, b_mean = np.mean(r), np.mean(g), np.mean(b)
            channel_diff = max(abs(r_mean - g_mean), abs(g_mean - b_mean), abs(r_mean - b_mean))
            if channel_diff < 60:
                concrete_score += 1
            total_checks += 1

        # 5) Motifs (fréquences moyennes)
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.log(np.abs(f_shift) + 1)
        center = magnitude_spectrum[gray.shape[0]//4:3*gray.shape[0]//4,
                                    gray.shape[1]//4:3*gray.shape[1]//4]
        avg_freq = float(np.mean(center))
        if 5 < avg_freq < 18:
            concrete_score += 1
        total_checks += 1

        confidence = concrete_score / max(total_checks, 1)

        # Seuils plus permissifs pour Simple/Batch
        if confidence >= 0.60:
            return True, f"✅ Surface en béton détectée (confiance: {confidence:.1%})"
        elif confidence >= 0.40:
            return False, f"⚠️ Surface douteuse - Essayez d'améliorer la netteté/l'éclairage (confiance: {confidence:.1%})"
        return False, f"❌ Cette image ne ressemble pas suffisamment à du béton (confiance: {confidence:.1%})"
    except Exception as e:
        return False, f"❌ Erreur validation simple: {e}"


def validate_image_for_analysis_simple(image_array: np.ndarray) -> Tuple[bool, str]:
    """Validation complète allégée pour Simple/Batch.

    - Valide techniquement l'image (dimensions/canaux implicites via traitements)
    - Valide la surface béton avec critères permissifs
    """
    if image_array is None:
        return False, "❌ Image vide"

    # Vérification minimales: taille raisonnable
    h, w = image_array.shape[:2]
    if h < 64 or w < 64:
        return False, "❌ Image trop petite (min 64x64)"

    # Validation béton (permissive)
    return _validate_concrete_surface_simple(image_array)


