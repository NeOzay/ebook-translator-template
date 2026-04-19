"""
Types partagés entre les templates Jinja2 et le pipeline de traduction.

Ce module contient les TypedDicts qui définissent les structures de données
injectées dans les templates ou produites par le LLM.
Aucune dépendance sur ebook_translator — importable partout sans circularité.
"""

from typing import Literal, NotRequired, TypedDict

type AnalyseLitteraireKey = Literal[
    "resume_narratif",
    "tonalite_ambiance",
    "style_ecriture",
    "themes_images_cles",
    "references_culturelles",
    "pistes_traduction",
]


class AnalyseLitteraire(TypedDict):
    """Analyse littéraire synthétique du chapitre."""

    resume_narratif: str
    """Résumé narratif (max 5 lignes)"""

    tonalite_ambiance: str
    """Tonalité et ambiance générale"""

    style_ecriture: str
    """Style d'écriture observé"""

    themes_images_cles: str
    """Thèmes et images clés du chapitre"""

    references_culturelles: str
    """Références culturelles présentes"""

    pistes_traduction: list[str]
    """Liste de pistes concrètes pour la traduction."""


class GlossaryEntry(TypedDict):
    terme: str
    traduction: str
    sexe: str
    type: str
    weight: NotRequired[int]
    confiance: Literal["low", "medium", "high"]


class GlossaryMultipleValueEntry(TypedDict):
    terme: str
    traductions: list[tuple[str, int]]
    sexes: list[tuple[str, int]]
    types: list[tuple[str, int]]
    weight: int
    confidence: Literal["low", "medium", "high"]
