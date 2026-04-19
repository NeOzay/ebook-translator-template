# CLAUDE.md — Templates de traduction de livres

## Vue d'ensemble

Ce dépôt contient les templates Jinja2 utilisés par un orchestrateur Python pour traduire des livres (epub) via l'API DeepSeek V3. Les templates sont injectés comme prompts système et utilisateur dans les appels LLM.

Un pipeline de traduction est utilisé, il est organisé en phases successives.
Les phases ont la responsabilité suivante :
- segmentée le texte
- préparer le système et user prompts pour chaque segment de texte
- réaliser l'appel au modèle 
- soumettre la sortie du modèle au pipeline checks
- sauvegarde la réponse validée

Chaque phase utilise un pipeline de checks configurable, il applique des tests de validation sur la sortie du LLM, et en cas d'échec, un prompt de correction ciblé est utilisé.

## Architecture des templates

### Convention de nommage

Tous les templates suivent la convention `_system.jinja` / `_user.jinja` :
- **System** : rôle, règles, exemples, format de sortie — invariant entre les appels d'un même type
- **User** : données variables (texte source, traduction incorrecte, compteurs d'erreur)

## Concepts clés

### Système de balises

Le texte source utilise deux types de balises :
- `<N/>` (ex. `<0/>`, `<1/>`, `<25/>`) : balise de numérotation de ligne. Chaque ligne traduite doit commencer par la même balise. Le modèle ne doit pas changer l'ordre ni le nombre de lignes.
- `</>` : balise de formatage. Remplace les vraies balises HTML de l'epub. Le modèle doit conserver exactement le même nombre de `</>` aux mêmes positions relatives. Elles sont reconstruites en balises HTML après traduction.

Les lignes sans balise `<N/>` sont du contexte (non traduites, non incluses dans la sortie).

Le marqueur `[=[END]=]` termine chaque sortie de traduction/correction.

### Glossaire

Le glossaire est séparé de l'analyse littéraire pour permettre des tailles de blocs différentes (petits blocs pour le glossaire, grands pour l'analyse).

**Structure d'une entrée glossaire (sortie LLM) :**
```json
{
  "glossaire": {
    "colonnes": ["terme", "type", "sexe", "proposition_traduction"],
    "entrees": [
      ["Dark Army", "organisation", "nc", "Armée des Ténèbres"]
    ]
  }
}
```

Le format en listes (pas en objets) est un choix d'économie de tokens.

**Énumération `type` :**
`personnage`, `lieu`, `creature`, `appellation`, `organisation`, `objet`, `terme_technique`, `reference_culturelle`

**Règles de priorité en cas d'ambiguïté :**
`personnage > creature > lieu > appellation > organisation > objet > terme_technique > reference_culturelle`

Règles spécifiques :
- Un être nommé individuellement est un `personnage`, pas une `creature`
- Une fonction/titre/surnom générique est une `appellation`, pas un `personnage`
- Tout groupe structuré (armée, guilde, faction) est une `organisation`
- `reference_culturelle` est réservé aux références au monde réel

**Énumération `sexe` :** `m`, `f`, `nc`

Priorité : `f = m >> nc` (m ou f remplace nc quand il y a conflit)

**Cycle de vie d'un terme :**
1. Extraction lors de la phase 0 glossaire
2. Agrégation de chaque proposition, augmentation du poids d'un (traduction, type, sexe indépendamment)
3. Calcul de confiance (sur les traductions uniquement)
4. Réinjection dans les prompts suivants selon le niveau de confiance

**Niveaux de confiance :**

| Niveau | Seuil | Comportement dans le prompt | Sortie |
|--------|-------|-----------------------------|--------|
| `high` | score ≥ 0.7 | Affiché en format compact (contexte) | Exclu de la sortie |
| `medium` | score ≥ 0.6 | Propositions affichées avec poids | Inclus, arbitrage possible |
| `low` | score < 0.6 | Propositions affichées avec poids | Inclus, arbitrage nécessaire |

Seuil d'inclusion : seuls les termes avec `weight ≥ 3` et present dans le texte sont réinjectés.

**Formule de confiance :**
```python
def compute_confidence(d: list[int]) -> float:
    total = sum(d)
    max_val = max(d)
    ratio = max_val / total
    dominance = math.pow(ratio, 0.5)
    k = 2
    masse = total / (total + k)
    score = dominance * masse
    return round(score, 2)
```

**Sélection des propositions à afficher :**
Les traductions sont ajoutées dans l'ordre décroissant de poids jusqu'à ce que le score de couverture (même formule, appliquée sur la fraction couverte) atteigne le seuil.

**Structures Python :**

`GlossaryEntry` — entrée résolue injectée dans les phases 1 et 2 via `glossary_block.jinja` :
- `terme`, `traduction`, `type`, `sexe` : valeurs uniques résolues
- `confidence` : `"low"` / `"medium"` / `"high"`
- `weight` (optionnel) : absent pour les termes fournis par l'utilisateur

`GlossaryMultipleValueEntry` — entrée avec propositions multiples pondérées, injectée en phase 0 via `glossary_existing_block.jinja` :
- `terme`, `weight`, `confidence`
- `traductions` : `list[tuple[str, int]]` — propositions triées par poids décroissant
- `sexes` : `list[tuple[str, int]]`
- `types` : `list[tuple[str, int]]`

### Contexte littéraire

Produit par la phase 0 analyse, injecté dans les phases 1 et 2 via `literary_context_block.jinja`. Contient : résumé narratif, tonalité/ambiance, style d'écriture, thèmes/images clés, références culturelles, pistes de traduction.

## Principes de rédaction des prompts

### Ce qu'il faut faire

- **Ton neutre et déclaratif** : "La sortie doit contenir exactement 3 `</>`", pas "Tu as ENCORE échoué !"
- **Règles déclaratives, pas impératives** : le LLM ne compte pas, il suit des contraintes
- **Séparer les règles invariantes (system) des données variables (user)**
- **Une seule occurrence de chaque règle** : pas de répétition pour "insister"
- **Les règles avant les données** : le modèle lit les instructions avant de voir le texte à traiter
- **Exemples concrets avec correct/incorrect** : le modèle apprend par l'exemple
- **Contraintes de format explicites** : "Commence par `{` et termine par `}`", "termine par `[=[END]=]`"

### Ce qu'il faut éviter

- **Emojis dans les titres** : ils consomment des tokens sans signal sémantique pour le modèle
- **Séparateurs `---`** : un `###` suffit comme séparateur
- **Ton punitif** ("Ta tâche a ÉCHOUÉ") : bruit sans effet sur DeepSeek V3
- **Texte explicatif sur le "pourquoi"** des instructions : le modèle n'a pas besoin de savoir pourquoi le contexte est utile, juste de l'utiliser
- **Répéter la même règle** à plusieurs endroits pour "insister" : ça dilue le signal
- **Numérotation bancale** (règle 2.5) : signal de hiérarchie confuse

### Économie de tokens

- Les retry utilisent `common_translate_rules_light.jinja` (pas la version complète avec les exemples)
- Les termes `high` du glossaire sont en format compact (une ligne) et exclus de la sortie
- Le glossaire utilise le format listes (pas objets) pour économiser des tokens
- `nc` comme valeur de sexe (2 tokens) plutôt que `non_concerne` (4+ tokens)

## Modification des templates

### Avant de modifier

1. Identifier quel(s) template(s) sont impactés (vérifier les includes)
2. Vérifier que le changement ne crée pas de contradiction avec un include partagé
3. Les includes sont utilisés par plusieurs templates — un changement dans un include affecte tous ses consommateurs

### Graphe de dépendances

```
translate_base_system
  ├── common_translate_rules
  ├── glossary_block
  └── literary_context_block

translate_refine_system
  ├── common_translate_rules
  ├── glossary_block
  └── literary_context_block

retry_correct_fragments_system         [mode: "strict" | "flexible"]
  └── common_correct_rules

retry_correct_punctuation_system
  └── common_correct_rules

retry_translate_missing_lines_targeted_system
  └── common_translate_rules_light

retry_translate_sentence_system
  └── common_translate_rules_light

retry_correct_analysis_invalid_json_system
  (aucun include)

retry_correct_analysis_missing_sections_system
  (aucun include)

analyze_chapter_simplified_system
  (aucun include)

analyze_chapter_incremental_system
  (aucun include)

test_glossary_system
  └── glossary_existing_block
```

### Variables d'entrée par templates

Les variables utilisées par un template sont déclarées dans l'entête, le type de chaque variable doit être indiqué.