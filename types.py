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


type GlossaryEntryType = (
    Literal[
        "personnage",
        "lieu",
        "creature",
        "appellation",
        "organisation",
        "objet",
        "terme_technique",
        "reference_culturelle",
    ]
    | str
)

type GlossaryEntrySexe = Literal["m", "f", "nc"] | str


class LLMTermeGlossaire(TypedDict):
    """Représente une entrée pour le glossaire produite par le LLM"""

    terme: str
    """Terme original dans la langue source"""

    type: GlossaryEntryType
    """Type de terme pour catégorisation"""

    sexe: GlossaryEntrySexe
    """Sexe pour personnages/créatures (m=masculin, f=féminin, nc=non concerné)"""

    proposition_traduction: str
    """Proposition de traduction UNIQUE (un seul terme, pas de liste)."""


class GlossaryEntry(TypedDict):
    """Représente un terme exporté depuis le glossaire"""

    terme: str
    traduction: str
    sexe: GlossaryEntrySexe
    type: GlossaryEntryType
    weight: NotRequired[
        int
    ]  # nombre de fois que le terme a été proposé par le LLM. Les termes fournis par l'utilisateur n'ont pas de poids.
    confiance: Literal["low", "medium", "high"]


class GlossaryMultipleValueEntry(TypedDict):
    """Représente un terme exporté depuis le glossaire avec plusieurs propositions de traduction possibles pondérées."""

    terme: str
    traductions: list[tuple[str, int]]
    sexes: list[tuple[GlossaryEntrySexe, int]]
    types: list[tuple[GlossaryEntryType, int]]
    weight: int
    confidence: Literal["low", "medium", "high"]
