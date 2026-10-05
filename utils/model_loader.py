#!/usr/bin/env python3
"""
Chargement et gestion des modèles
=================================

Ce module gère le chargement et l'initialisation des modèles
de classification et de segmentation.
"""

import torch
import torch.nn as nn
import torchvision.models as models
import streamlit as st
from pathlib import Path
import logging
from typing import Tuple, Optional

from config.config import AppConfig

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CLASSES POUR LA SEGMENTATION ==========

class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels, dropout_rate=0.1):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout2d(dropout_rate),

            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout2d(dropout_rate),
        )

    def forward(self, x):
        return self.double_conv(x)

class AttentionBlock(nn.Module):
    """Bloc d'attention pour améliorer les performances."""
    def __init__(self, F_g, F_l, F_int):
        super().__init__()
        self.W_g = nn.Sequential(
            nn.Conv2d(F_g, F_int, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(F_int)
        )
        
        self.W_x = nn.Sequential(
            nn.Conv2d(F_l, F_int, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(F_int)
        )

        self.psi = nn.Sequential(
            nn.Conv2d(F_int, 1, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(1),
            nn.Sigmoid()
        )
        
        self.relu = nn.ReLU(inplace=True)

    def forward(self, g, x):
        g1 = self.W_g(g)
        x1 = self.W_x(x)
        psi = self.relu(g1 + x1)
        psi = self.psi(psi)
        return x * psi

class UNet(nn.Module):
    def __init__(self, in_channels=3, out_channels=1, dropout_rate=0.1):
        super().__init__()

        # Encoder - Amélioré avec plus de features
        self.down1 = DoubleConv(in_channels, 64, dropout_rate)
        self.pool1 = nn.MaxPool2d(2)

        self.down2 = DoubleConv(64, 128, dropout_rate)
        self.pool2 = nn.MaxPool2d(2)

        self.down3 = DoubleConv(128, 256, dropout_rate)
        self.pool3 = nn.MaxPool2d(2)

        self.down4 = DoubleConv(256, 512, dropout_rate)
        self.pool4 = nn.MaxPool2d(2)

        # Bottleneck - Plus profond
        self.bottleneck = DoubleConv(512, 1024, dropout_rate)

        # Decoder avec attention
        self.up4 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        self.att4 = AttentionBlock(F_g=512, F_l=512, F_int=256)
        self.conv4 = DoubleConv(1024, 512, dropout_rate)

        self.up3 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.att3 = AttentionBlock(F_g=256, F_l=256, F_int=128)
        self.conv3 = DoubleConv(512, 256, dropout_rate)

        self.up2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.att2 = AttentionBlock(F_g=128, F_l=128, F_int=64)
        self.conv2 = DoubleConv(256, 128, dropout_rate)

        self.up1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.att1 = AttentionBlock(F_g=64, F_l=64, F_int=32)
        self.conv1 = DoubleConv(128, 64, dropout_rate)

        # Couche finale avec activation
        self.final = nn.Conv2d(64, out_channels, kernel_size=1)
        
        # Initialisation des poids
        self._initialize_weights()

    def _initialize_weights(self):
        """Initialisation des poids pour de meilleures performances."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        # Encoder
        d1 = self.down1(x)
        d2 = self.down2(self.pool1(d1))
        d3 = self.down3(self.pool2(d2))
        d4 = self.down4(self.pool3(d3))

        # Bottleneck
        bn = self.bottleneck(self.pool4(d4))

        # Decoder avec attention
        up4 = self.up4(bn)
        x4 = self.att4(g=up4, x=d4)
        up4 = torch.cat([up4, x4], dim=1)
        up4 = self.conv4(up4)

        up3 = self.up3(up4)
        x3 = self.att3(g=up3, x=d3)
        up3 = torch.cat([up3, x3], dim=1)
        up3 = self.conv3(up3)

        up2 = self.up2(up3)
        x2 = self.att2(g=up2, x=d2)
        up2 = torch.cat([up2, x2], dim=1)
        up2 = self.conv2(up2)

        up1 = self.up1(up2)
        x1 = self.att1(g=up1, x=d1)
        up1 = torch.cat([up1, x1], dim=1)
        up1 = self.conv1(up1)

        # Sortie sans sigmoid (sera appliqué dans la loss)
        return self.final(up1)

# ========== CLASSES POUR LA CLASSIFICATION ==========

class CrackClassifier(nn.Module):
    """Modèle de classification des fissures (copie de notre modèle)."""
    
    def __init__(self, num_classes=2, dropout_rate=0.3, backbone="resnet50"):
        super(CrackClassifier, self).__init__()
        
        # Charger le backbone
        if backbone == "resnet18":
            self.backbone = models.resnet18(pretrained=False)
        elif backbone == "resnet34":
            self.backbone = models.resnet34(pretrained=False)
        elif backbone == "resnet50":
            self.backbone = models.resnet50(pretrained=False)
        else:
            raise ValueError(f"Backbone non supporté: {backbone}")
        
        # Extraire les features
        in_features = self.backbone.fc.in_features
        
        # Architecture simplifiée et robuste
        self.feature_extractor = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout_rate),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout_rate),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout_rate * 0.5),
            nn.Linear(128, num_classes)
        )
        
        # Remplacer la dernière couche du backbone
        self.backbone.fc = nn.Identity()
    
    def forward(self, x):
        # Extraire les features du backbone
        features = self.get_features(x)
        # Passer par le classifieur
        output = self.feature_extractor(features)
        return output
    
    def get_features(self, x):
        """Extrait les features du backbone."""
        x = self.backbone.conv1(x)
        x = self.backbone.bn1(x)
        x = self.backbone.relu(x)
        x = self.backbone.maxpool(x)
        
        x = self.backbone.layer1(x)
        x = self.backbone.layer2(x)
        x = self.backbone.layer3(x)
        x = self.backbone.layer4(x)
        
        x = self.backbone.avgpool(x)
        x = torch.flatten(x, 1)
        
        return x

class UNet(nn.Module):
    """Modèle UNet pour la segmentation (architecture simplifiée pour l'app)."""
    
    def __init__(self, in_channels=3, out_channels=1):
        super(UNet, self).__init__()
        
        # Encoder
        self.encoder1 = self._conv_block(in_channels, 64)
        self.encoder2 = self._conv_block(64, 128)
        self.encoder3 = self._conv_block(128, 256)
        self.encoder4 = self._conv_block(256, 512)
        
        # Bottleneck
        self.bottleneck = self._conv_block(512, 1024)
        
        # Decoder
        self.upconv4 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        self.decoder4 = self._conv_block(1024, 512)
        
        self.upconv3 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.decoder3 = self._conv_block(512, 256)
        
        self.upconv2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.decoder2 = self._conv_block(256, 128)
        
        self.upconv1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.decoder1 = self._conv_block(128, 64)
        
        # Output
        self.final_conv = nn.Conv2d(64, out_channels, kernel_size=1)
        
        # Pooling
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
    
    def _conv_block(self, in_channels, out_channels):
        """Bloc de convolution."""
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, x):
        # Encoder
        enc1 = self.encoder1(x)
        enc2 = self.encoder2(self.pool(enc1))
        enc3 = self.encoder3(self.pool(enc2))
        enc4 = self.encoder4(self.pool(enc3))
        
        # Bottleneck
        bottleneck = self.bottleneck(self.pool(enc4))
        
        # Decoder
        dec4 = self.upconv4(bottleneck)
        dec4 = torch.cat((dec4, enc4), dim=1)
        dec4 = self.decoder4(dec4)
        
        dec3 = self.upconv3(dec4)
        dec3 = torch.cat((dec3, enc3), dim=1)
        dec3 = self.decoder3(dec3)
        
        dec2 = self.upconv2(dec3)
        dec2 = torch.cat((dec2, enc2), dim=1)
        dec2 = self.decoder2(dec2)
        
        dec1 = self.upconv1(dec2)
        dec1 = torch.cat((dec1, enc1), dim=1)
        dec1 = self.decoder1(dec1)
        
        # Output
        output = self.final_conv(dec1)
        
        return output

@st.cache_resource
def setup_device() -> str:
    """Configure et retourne le device optimal."""
    if torch.cuda.is_available():
        device = "cuda"
        logger.info(f"GPU détecté: {torch.cuda.get_device_name(0)}")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = "mps"
        logger.info("Apple Silicon GPU détecté")
    else:
        device = "cpu"
        logger.info("Utilisation du CPU")
    
    return device

@st.cache_resource
def load_classification_model() -> Optional[CrackClassifier]:
    """Charge le modèle de classification."""
    try:
        device = setup_device()
        
        # Créer le modèle
        model = CrackClassifier(
            num_classes=2,
            dropout_rate=0.3,
            backbone="resnet50"
        )
        
        # Vérifier si le fichier de modèle existe
        model_path = AppConfig.CLASSIFICATION_MODEL_PATH
        if not model_path.exists():
            logger.warning(f"Modèle de classification non trouvé: {model_path}")
            # Retourner le modèle non entraîné pour les tests
            return model.to(device)
        
        # Charger les poids
        checkpoint = torch.load(model_path, map_location=device)
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        
        model.eval()
        model = model.to(device)
        
        logger.info("Modèle de classification chargé avec succès")
        return model
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle de classification: {e}")
        return None

@st.cache_resource
def load_segmentation_model() -> Optional[UNet]:
    """Charge le modèle de segmentation."""
    try:
        device = setup_device()
        
        # Créer le modèle
        model = UNet(in_channels=3, out_channels=1)
        
        # Vérifier si le fichier de modèle existe
        model_path = AppConfig.SEGMENTATION_MODEL_PATH
        if not model_path.exists():
            logger.warning(f"Modèle de segmentation non trouvé: {model_path}")
            return model.to(device)
        
        # Charger les poids
        checkpoint = torch.load(model_path, map_location=device)
        
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'], strict=False)
        else:
            model.load_state_dict(checkpoint, strict=False)
        
        model.eval()
        model = model.to(device)
        
        logger.info("Modèle de segmentation chargé avec succès")
        return model
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle de segmentation: {e}")
        return None

def load_models() -> Tuple[Optional[CrackClassifier], Optional[UNet]]:
    """Charge les deux modèles."""
    logger.info("Chargement des modèles...")
    
    classification_model = load_classification_model()
    segmentation_model = load_segmentation_model()
    
    return classification_model, segmentation_model

def get_model_info() -> dict:
    """Retourne les informations sur les modèles."""
    device = setup_device()
    
    classification_info = {
        'name': 'ResNet50 Classifier',
        'accuracy': AppConfig.MODEL_METRICS['classification']['accuracy'],
        'precision': AppConfig.MODEL_METRICS['classification']['precision'],
        'recall': AppConfig.MODEL_METRICS['classification']['recall'],
        'f1_score': AppConfig.MODEL_METRICS['classification']['f1_score']
    }
    
    segmentation_info = {
        'name': 'UNet Segmentation',
        'dice_score': AppConfig.MODEL_METRICS['segmentation']['dice_score'],
        'iou': AppConfig.MODEL_METRICS['segmentation']['iou']
    }
    
    return {
        'device': device,
        'classification': classification_info,
        'segmentation': segmentation_info
    }

def verify_models() -> dict:
    """Vérifie la disponibilité des modèles."""
    results = {
        'classification': {
            'available': AppConfig.CLASSIFICATION_MODEL_PATH.exists(),
            'path': str(AppConfig.CLASSIFICATION_MODEL_PATH)
        },
        'segmentation': {
            'available': AppConfig.SEGMENTATION_MODEL_PATH.exists(),
            'path': str(AppConfig.SEGMENTATION_MODEL_PATH)
        }
    }
    
    return results