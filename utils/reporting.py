#!/usr/bin/env python3
"""
Utilitaires d'export et de reporting (PDF/CSV)
Template professionnel: en-tête/pied de page, styles, métriques, figures
"""

from io import BytesIO
from datetime import datetime
from typing import Dict, Optional

from pathlib import Path
import numpy as np
try:  # conversion couleur si dispo
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # noqa: N816
from PIL import Image

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    Table,
    TableStyle,
    PageBreak,
)


# Couleurs et chemins
BRAND_ORANGE = colors.HexColor("#ff9a66")
TEXT_DARK = colors.HexColor("#222222")
MUTED = colors.HexColor("#666666")
LIGHT_BG = colors.HexColor("#f7f7f8")

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets" / "images"


def _find_logo_path() -> Optional[Path]:
    if ASSETS_DIR.exists():
        for ext in ("png", "jpg", "jpeg", "svg", "ico"):
            files = list(ASSETS_DIR.glob(f"*.{ext}"))
            if files:
                return files[0]
    return None


def _header_footer(canvas_obj: canvas.Canvas, doc):
    canvas_obj.saveState()
    width, height = A4
    # Bande supérieure
    canvas_obj.setFillColor(BRAND_ORANGE)
    canvas_obj.rect(0, height - 1.2 * cm, width, 1.2 * cm, stroke=0, fill=1)
    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont("Helvetica-Bold", 12)
    canvas_obj.drawString(2 * cm, height - 0.75 * cm, "Rapport d'Analyse — Détection de Fissures")

    # Logo si disponible
    logo = _find_logo_path()
    if logo and logo.exists():
        try:
            canvas_obj.drawImage(str(logo), width - 3.5 * cm, height - 1.05 * cm, 2.2 * cm, 0.9 * cm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Pied de page
    canvas_obj.setFillColor(MUTED)
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawString(2 * cm, 1.5 * cm, f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    canvas_obj.drawRightString(width - 2 * cm, 1.5 * cm, f"Page {doc.page}")
    canvas_obj.restoreState()


def _style(title_size=16):
    return {
        "title": ParagraphStyle(
            name="Title",
            fontName="Helvetica-Bold",
            fontSize=title_size,
            leading=title_size + 4,
            textColor=TEXT_DARK,
            spaceAfter=8,
        ),
        "h1": ParagraphStyle(
            name="H1",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=TEXT_DARK,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            name="Body",
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=TEXT_DARK,
            spaceAfter=4,
        ),
        "muted": ParagraphStyle(
            name="Muted",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=MUTED,
        ),
    }


def _np_to_pil(image_np: np.ndarray) -> Image.Image:
    if image_np is None:
        raise ValueError("image_np is None")
    if image_np.ndim == 2:
        return Image.fromarray(image_np.astype(np.uint8))
    if image_np.ndim == 3 and image_np.shape[2] == 3:
        arr = image_np
        if cv2 is not None:
            try:
                arr = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
            except Exception:
                pass
        return Image.fromarray(arr.astype(np.uint8))
    # autres formes: convertir au mieux
    return Image.fromarray(image_np.astype(np.uint8))


def _flowable_image_from_array(arr: np.ndarray, max_width: float = 16 * cm) -> Optional[RLImage]:
    try:
        pil_img = _np_to_pil(arr)
    except Exception:
        return None
    bio = BytesIO()
    pil_img.save(bio, format="PNG")
    bio.seek(0)
    img = RLImage(bio)
    # mise à l'échelle douce
    if img.drawWidth > max_width:
        ratio = max_width / float(img.drawWidth)
        img.drawWidth = max_width
        img.drawHeight = img.drawHeight * ratio
    return img


def _metrics_table(rows):
    table = Table(rows, colWidths=[6 * cm, 10 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#dddddd')),
        ('GRID', (0, 1), (-1, -1), 0.25, colors.HexColor('#eaeaea')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
    ]))
    return table


def create_simple_report_pdf(analysis_results: Dict) -> bytes:
    """
    Rapport professionnel pour une analyse simple.
    analysis_results attend:
      {
        'classification': {'has_crack': bool, 'confidence': float},
        'segmentation': {...} (optionnel),
        'figures': {'original': np.ndarray, 'mask': np.ndarray, 'overlay': np.ndarray} (optionnel)
      }
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=3 * cm,
        bottomMargin=2 * cm,
    )
    styles = _style()

    story = []

    story.append(Paragraph("Rapport d'analyse — Détection de Fissures", styles["title"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Type d'analyse: <b>Simple</b>", styles["muted"]))
    story.append(Spacer(1, 10))

    cls = (analysis_results or {}).get('classification', {})
    has_crack = bool(cls.get('has_crack', False))
    confidence = float(cls.get('confidence', 0.0))

    # Tableau Métriques
    result_text = "Fissure détectée" if has_crack else "Aucune fissure"
    rows = [["Résumé Exécutif", ""]]
    rows += [["Résultat", result_text], ["Confiance", f"{confidence:.1%}"]]
    seg = (analysis_results or {}).get('segmentation', {}) or {}
    if seg:
        surface = seg.get('surface_area')
        density = seg.get('crack_density')
        if surface is not None:
            rows.append(["Surface fissurée (mm²)", f"{surface:.1f}"])
        if density is not None:
            rows.append(["Densité", f"{density:.2f}%"])
    story.append(_metrics_table(rows))
    story.append(Spacer(1, 16))

    # Interprétation & Recommandations
    story.append(Paragraph("Interprétation & Recommandations", styles["h1"]))
    recos = [
        "Si une fissure est détectée avec forte confiance, une inspection visuelle détaillée est recommandée.",
        "Si la densité dépasse 5%, prioriser une intervention et un suivi rapproché.",
        "Compléter par des mesures in situ et/ou imagerie complémentaire en cas d'incertitude.",
    ]
    for r in recos:
        story.append(Paragraph(f"• {r}", styles["body"]))
    story.append(Spacer(1, 12))

    # Méthodologie
    story.append(Paragraph("Méthodologie", styles["h1"]))
    for m in (
        "Classification: modèle CNN (ResNet50) pour la présence de fissures.",
        "Segmentation: approche OpenCV binaire pour la localisation pixel.",
        "Indicateurs: surface fissurée, densité, longueurs approximatives.",
    ):
        story.append(Paragraph(f"• {m}", styles["body"]))

    # Figures optionnelles
    figs = (analysis_results or {}).get('figures') or {}
    original = figs.get('original')
    mask = figs.get('mask')
    overlay = figs.get('overlay')
    images = []
    if isinstance(original, np.ndarray):
        img = _flowable_image_from_array(original)
        if img: images.append(("Image originale", img))
    if isinstance(mask, np.ndarray):
        img = _flowable_image_from_array(mask)
        if img: images.append(("Prédiction (Binaire)", img))
    if isinstance(overlay, np.ndarray):
        img = _flowable_image_from_array(overlay)
        if img: images.append(("Overlay", img))
    if images:
        story.append(Spacer(1, 14))
        story.append(Paragraph("Figures", styles["h1"]))
        for caption, img in images:
            story.append(img)
            story.append(Paragraph(caption, styles["muted"]))
            story.append(Spacer(1, 8))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def create_batch_report_pdf(summary: Dict) -> bytes:
    """Rapport professionnel de synthèse pour l'analyse batch."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=3 * cm,
        bottomMargin=2 * cm,
    )
    styles = _style()
    story = []

    story.append(Paragraph("Rapport — Analyse Batch", styles["title"]))
    story.append(Spacer(1, 10))

    # Tableau des stats
    rows = [["Statistiques Globales", ""]]
    for key, value in (summary or {}).items():
        label = key.replace('_', ' ').title()
        rows.append([label, str(value)])
    story.append(_metrics_table(rows))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Commentaires & Recommandations", styles["h1"]))
    for t in (
        "Prioriser l'inspection des images classées 'Fissure détectée'.",
        "Utiliser le CSV détaillé pour un suivi temporel et archivage.",
        "Envisager un contrôle supplémentaire si le taux de fissures est élevé.",
    ):
        story.append(Paragraph(f"• {t}", styles["body"]))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

