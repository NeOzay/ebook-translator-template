"""
Schéma Pydantic de la sortie LLM de la phase glossaire.

Source de vérité unique de la structure JSON produite par le LLM. Consommé par
l'orchestrateur via Instructor en `Mode.TOOLS_STRICT`. Les contraintes
exprimables en types Python vivent ici ; le prompt (`glossary_system.jinja`)
ne décrit plus la structure.

Pour ajouter ou renommer une colonne du tableau :
  1. mettre à jour `GLOSSARY_COLUMNS` (ordre fait foi),
  2. mettre à jour le `Literal` de `GlossaireBlock.colonnes`,
  3. ajuster les validators si la colonne porte une contrainte de valeur,
  4. mettre à jour `glossary_system.jinja` (liste des colonnes affichée au LLM).
"""

from typing import Annotated, Literal, NotRequired, TypedDict, override

from pydantic import ConfigDict, Field

from template.types import ConvertibleModel, NormStr, NormTupleValidator

GlossaryEntryType = Literal[
    "personnage",
    "lieu",
    "creature",
    "appellation",
    "organisation",
    "objet",
    "terme_technique",
    "reference_culturelle",
]
type _NormGlossaryEntryType = Annotated[GlossaryEntryType, NormStr]

GlossaryEntrySexe = Literal["m", "f", "nc"]
type _NormGlossaryEntrySexe = Annotated[GlossaryEntrySexe, NormStr]

LLMColonneOrder = tuple[
    Literal["terme"],
    Literal["type"],
    Literal["sexe"],
    Literal["proposition_traduction"],
]
type _NormLLMColonneOrder = Annotated[LLMColonneOrder, NormTupleValidator]

_GLOSSARY_COLUMNS: LLMColonneOrder = (
    "terme",
    "type",
    "sexe",
    "proposition_traduction",
)

GLOSSARY_TYPES_AUTORISES: frozenset[GlossaryEntryType] = frozenset(
    GlossaryEntryType.__args__
)

GLOSSARY_SEXES_AUTORISES: frozenset[GlossaryEntrySexe] = frozenset(
    GlossaryEntrySexe.__args__
)

_TYPE_INDEX: int = _GLOSSARY_COLUMNS.index("type")
_SEXE_INDEX: int = _GLOSSARY_COLUMNS.index("sexe")
_NB_COLONNES: int = len(_GLOSSARY_COLUMNS)


class LLMTermeGlossary(TypedDict):
    """Représente un terme du glossaire tel que proposé par le LLM."""

    terme: str
    type: GlossaryEntryType
    sexe: GlossaryEntrySexe
    proposition_traduction: str


type Entree = tuple[NormStr, _NormGlossaryEntryType, _NormGlossaryEntrySexe, NormStr]


class LLMGlossaryModel(ConvertibleModel[list[LLMTermeGlossary]]):
    """Tableau du glossaire au format colonnes/entrees."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    colonnes: _NormLLMColonneOrder = Field(
        description=(
            "Noms des colonnes, dans l'ordre. Doit valoir exactement "
            f"{list(_GLOSSARY_COLUMNS)}."
        ),
        min_length=_NB_COLONNES,
        max_length=_NB_COLONNES,
    )

    entrees: list[Entree] = Field(
        description=(
            "Liste des entrées du glossaire. Chaque entrée est une liste "
            f"d'exactement {_NB_COLONNES} chaînes, dans l'ordre des colonnes."
        ),
    )

    @override
    def _build_impl(self) -> list[LLMTermeGlossary]:
        final_list: list[LLMTermeGlossary] = []
        for entree in self.entrees:
            terme, type_, sexe, proposition_traduction = entree
            final_list.append(
                {
                    "terme": terme.strip(),
                    "type": type_,
                    "sexe": sexe,
                    "proposition_traduction": proposition_traduction.strip(),
                },
            )
        return final_list


class GlossaryEntry(TypedDict):
    """Représente un terme exporté depuis le glossaire"""

    terme: str
    traduction: str
    sexe: GlossaryEntrySexe
    type: GlossaryEntryType
    weight: NotRequired[
        int
    ]  # nombre de fois que le terme a été proposé par le LLM. Les termes fournis par l'utilisateur n'ont pas de poids.
    confidence: Literal["low", "medium", "high"]


class GlossaryMultipleValueEntry(TypedDict):
    """Représente un terme exporté depuis le glossaire avec plusieurs propositions de traduction possibles pondérées."""

    terme: str
    traductions: list[tuple[str, int]]
    sexes: list[tuple[GlossaryEntrySexe, int]]
    types: list[tuple[GlossaryEntryType, int]]
    weight: int
    confidence: Literal["low", "medium", "high"]
