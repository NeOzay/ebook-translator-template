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

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

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

GlossaryEntrySexe = Literal["m", "f", "nc"]

GLOSSARY_COLUMNS: tuple[str, ...] = (
    "terme",
    "type",
    "sexe",
    "proposition_traduction",
)

_TYPES_AUTORISES: frozenset[str] = frozenset(GlossaryEntryType.__args__)
_SEXES_AUTORISES: frozenset[str] = frozenset(GlossaryEntrySexe.__args__)
_TYPE_INDEX: int = GLOSSARY_COLUMNS.index("type")
_SEXE_INDEX: int = GLOSSARY_COLUMNS.index("sexe")
_NB_COLONNES: int = len(GLOSSARY_COLUMNS)


class GlossaireBlock(BaseModel):
    """Tableau du glossaire au format colonnes/entrees."""

    model_config = ConfigDict(extra="forbid")

    colonnes: list[
        Literal["terme", "type", "sexe", "proposition_traduction"]
    ] = Field(
        description=(
            "Noms des colonnes, dans l'ordre. Doit valoir exactement "
            f"{list(GLOSSARY_COLUMNS)}."
        ),
        min_length=_NB_COLONNES,
        max_length=_NB_COLONNES,
    )

    entrees: list[list[str]] = Field(
        description=(
            "Liste des entrées du glossaire. Chaque entrée est une liste "
            f"d'exactement {_NB_COLONNES} chaînes, dans l'ordre des colonnes."
        ),
    )

    @field_validator("colonnes")
    @classmethod
    def _colonnes_dans_lordre(
        cls, valeur: list[str]
    ) -> list[str]:
        attendu = list(GLOSSARY_COLUMNS)
        if list(valeur) != attendu:
            raise ValueError(
                f"`colonnes` doit valoir exactement {attendu}, dans cet ordre. "
                f"Reçu : {list(valeur)}."
            )
        return valeur

    @field_validator("entrees")
    @classmethod
    def _entrees_bien_formees(
        cls, entrees: list[list[str]]
    ) -> list[list[str]]:
        for index, entree in enumerate(entrees):
            if len(entree) != _NB_COLONNES:
                raise ValueError(
                    f"L'entrée à la position {index} contient {len(entree)} "
                    f"chaînes, alors que {_NB_COLONNES} sont attendues "
                    f"(une par colonne, dans l'ordre {list(GLOSSARY_COLUMNS)})."
                )

            type_recu = entree[_TYPE_INDEX]
            if type_recu not in _TYPES_AUTORISES:
                raise ValueError(
                    f"L'entrée à la position {index} a `type` = "
                    f"{type_recu!r}. Valeurs autorisées : "
                    f"{sorted(_TYPES_AUTORISES)}."
                )

            sexe_recu = entree[_SEXE_INDEX]
            if sexe_recu not in _SEXES_AUTORISES:
                raise ValueError(
                    f"L'entrée à la position {index} a `sexe` = "
                    f"{sexe_recu!r}. Valeurs autorisées : "
                    f"{sorted(_SEXES_AUTORISES)}."
                )

            for position, chaine in enumerate(entree):
                if not chaine or not chaine.strip():
                    nom_colonne = GLOSSARY_COLUMNS[position]
                    raise ValueError(
                        f"L'entrée à la position {index} a la colonne "
                        f"`{nom_colonne}` vide. Toutes les colonnes "
                        f"doivent être renseignées."
                    )

        return entrees


class GlossaireResponse(BaseModel):
    """Réponse complète de la phase glossaire."""

    model_config = ConfigDict(extra="forbid")

    glossaire: GlossaireBlock
