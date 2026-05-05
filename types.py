"""
Types partagés entre les templates Jinja2 et le pipeline de traduction.

Ce module contient les TypedDicts qui définissent les structures de données
injectées dans les templates ou produites par le LLM.
Aucune dépendance sur ebook_translator — importable partout sans circularité.
"""

from abc import abstractmethod
from functools import cache
from typing import Annotated, Any, Literal, TypedDict, final, get_type_hints

from pydantic import BaseModel, BeforeValidator, TypeAdapter


class ConvertibleModel[TD](BaseModel):
    """BaseModel qui sait se convertir en un TypedDict cible."""

    _cached_build: TD | None = None

    @abstractmethod
    def _build_impl(self) -> TD: ...

    @final
    def build(self) -> TD:
        if self._cached_build is None:
            object.__setattr__(self, "_cached_build", self._build_impl())
        return self._cached_build  # pyright: ignore[reportReturnType]

    def serialized_build(self, *, indent: int | None = None) -> str:
        return self.target_adapter().dump_json(self.build(), indent=indent).decode()

    @classmethod
    def deserialize(cls, raw: str | bytes) -> TD:
        return cls.target_adapter().validate_json(raw)

    @classmethod
    @cache
    def target_adapter(cls) -> TypeAdapter[TD]:
        """TypeAdapter pour le TypedDict cible (extrait du type de retour de build)."""
        target_type = get_type_hints(cls.build)["return"]
        return TypeAdapter(target_type)


def normalize_string(value: object) -> object:
    """Normalise une chaîne pour comparaison (minuscules, espaces réduits)."""
    return " ".join(value.strip().lower().split()) if isinstance(value, str) else value


def normalize_tuple(v: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(x.strip().lower() if isinstance(x, str) else x for x in v)


NormStrValidator = BeforeValidator(normalize_string)
NormTupleValidator = BeforeValidator(normalize_tuple)

NormStr = Annotated[str, NormStrValidator]


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
