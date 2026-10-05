#!/usr/bin/env python3
"""
Gestion d'historique des analyses
---------------------------------

Ce module fournit une persistance légère (SQLite) pour enregistrer
les analyses effectuées par les différentes pages de l'application.

Schéma de table `analysis_history`:
- id INTEGER PRIMARY KEY AUTOINCREMENT
- timestamp REAL (epoch seconds)
- page TEXT (ex: 'simple', 'realtime', 'batch')
- method TEXT (ex: 'upload', 'webcam', 'batch')
- has_crack INTEGER (0/1)
- confidence REAL (0..1)
- analysis_time REAL (seconds, optionnel)
- filename TEXT (optionnel)
- extra_json TEXT (JSON sérialisé, optionnel)
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


_DB_DIR = Path(__file__).parent.parent / "data"
_DB_PATH = _DB_DIR / "history.db"
_INIT_LOCK = threading.Lock()


def _ensure_db() -> None:
    """Crée le répertoire et la table si nécessaire (thread-safe)."""
    if not _DB_DIR.exists():
        _DB_DIR.mkdir(parents=True, exist_ok=True)

    with _INIT_LOCK:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    page TEXT NOT NULL,
                    method TEXT NOT NULL,
                    has_crack INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    analysis_time REAL,
                    filename TEXT,
                    extra_json TEXT
                )
                """
            )
            conn.commit()


def log_analysis(
    *,
    page: str,
    method: str,
    has_crack: bool,
    confidence: float,
    analysis_time: Optional[float] = None,
    filename: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Enregistre une analyse.

    Arguments:
        page: nom logique de la page (ex: 'simple', 'realtime', 'batch')
        method: méthode d'analyse (ex: 'upload', 'webcam', 'batch')
        has_crack: True si fissure détectée
        confidence: score de confiance (0..1)
        analysis_time: durée en secondes
        filename: nom de fichier si disponible
        extra: dictionnaire supplémentaire sérialisé en JSON
    """
    _ensure_db()
    payload = (
        float(time.time()),
        str(page),
        str(method),
        1 if has_crack else 0,
        float(confidence),
        float(analysis_time) if analysis_time is not None else None,
        str(filename) if filename is not None else None,
        json.dumps(extra, ensure_ascii=False) if extra is not None else None,
    )

    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO analysis_history (
                timestamp, page, method, has_crack, confidence,
                analysis_time, filename, extra_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )
        conn.commit()


def fetch_history(
    *,
    limit: int = 500,
    page: Optional[str] = None,
    method: Optional[str] = None,
    has_crack: Optional[bool] = None,
    order_desc: bool = True,
) -> List[dict]:
    """Récupère l'historique sous forme de liste de dicts."""
    _ensure_db()
    clauses: List[str] = []
    params: List[Any] = []

    if page is not None:
        clauses.append("page = ?")
        params.append(page)
    if method is not None:
        clauses.append("method = ?")
        params.append(method)
    if has_crack is not None:
        clauses.append("has_crack = ?")
        params.append(1 if has_crack else 0)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    order_sql = "DESC" if order_desc else "ASC"

    query = f"""
        SELECT id, timestamp, page, method, has_crack, confidence,
               analysis_time, filename, extra_json
        FROM analysis_history
        {where_sql}
        ORDER BY id {order_sql}
        LIMIT ?
    """
    params.append(int(limit))

    with sqlite3.connect(_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    result: List[dict] = []
    for r in rows:
        extra = None
        if r["extra_json"]:
            try:
                extra = json.loads(r["extra_json"])  # type: ignore[assignment]
            except Exception:
                extra = None
        result.append(
            {
                "id": r["id"],
                "timestamp": float(r["timestamp"]),
                "page": r["page"],
                "method": r["method"],
                "has_crack": bool(r["has_crack"]),
                "confidence": float(r["confidence"]),
                "analysis_time": float(r["analysis_time"]) if r["analysis_time"] is not None else None,
                "filename": r["filename"],
                "extra": extra,
            }
        )
    return result


def export_history_csv(*, limit: int = 5000) -> bytes:
    """Exporte l'historique en CSV (bytes)."""
    import csv
    import io

    rows = fetch_history(limit=limit)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "timestamp",
        "page",
        "method",
        "has_crack",
        "confidence",
        "analysis_time",
        "filename",
        "extra",
    ])
    for r in rows:
        writer.writerow([
            r["id"],
            r["timestamp"],
            r["page"],
            r["method"],
            1 if r["has_crack"] else 0,
            r["confidence"],
            r["analysis_time"] if r["analysis_time"] is not None else "",
            r["filename"] or "",
            json.dumps(r["extra"], ensure_ascii=False) if r.get("extra") is not None else "",
        ])
    return output.getvalue().encode("utf-8")


def clear_history() -> None:
    """Supprime tout l'historique."""
    _ensure_db()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("DELETE FROM analysis_history")
        conn.commit()


# Initialisation au chargement du module
_ensure_db()


