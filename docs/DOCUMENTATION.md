# Documentation Complète - ComfyUI API Pictures

## Table des Matières

1. [Introduction](#introduction)
2. [Architecture Globale](#architecture-globale)
3. [Modules](#modules)
   - [script.py](#scriptpy)
   - [core/client.py](#coreclientpy)
   - [core/workflow.py](#coreworkflowpy)
   - [modes/base.py](#modesbasepy)
   - [modes/manual.py](#modesmanualpy)
   - [modes/immersive.py](#modesimmersivepy)
   - [modes/picturebook.py](#modespicturebookpy)
   - [modes/tag_processor.py](#modestag_processorpy)
   - [services/tag_parser.py](#servicestag_parserpy)
   - [services/image_replacer.py](#servicesimage_replacerpy)
   - [utils/helpers.py](#utilshelperspy)
   - [ui/components.py](#uicomponentspy)
   - [global_state.py](#global_statepy)
   - [javascript/script.js](#javascriptscriptjs)
4. [Modes de Fonctionnement](#modes-de-fonctionnement)
5. [Configuration](#configuration)
6. [Workflow ComfyUI](#workflow-comfyui)
7. [Tests](#tests)

---

## Introduction

**ComfyUI API Pictures** est une extension pour text-generation-webui (TGUI) qui permet à l'LLM de générer des images via l'API ComfyUI. Elle fonctionne de manière similaire à l'extension `sd_api_pictures` mais utilise ComfyUI comme backend.

### Fonctionnalités Principales

- **Intégration ComfyUI**: Connexion à une instance ComfyUI locale pour générer des images
- **Génération dans le Chat**: Génération automatique d'images basées sur les réponses de l'LLM
- **Modes Interactifs**:
  - **Manual**: Génération manuelle via bouton
  - **Immersive**: Détection de mots-clés déclencheurs
  - **Picturebook**: Génération automatique pour chaque réponse
  - **Process Tags**: Parsing des balises `<image>prompt</image>`
- **Support des Workflows**: Sélection de workflows ComfyUI en format JSON

---

## Architecture Globale

```
comfy_api_pictures/
├── script.py                 # Point d'entrée principal (~150 lignes)
├── core/
│   ├── client.py            # ComfyUIClient - API communication (~147 lignes)
│   └── workflow.py          # Gestion des workflows (~36 lignes)
├── modes/
│   ├── base.py              # Classe abstraite Mode (~32 lignes)
│   ├── manual.py            # Mode 0 - Manual (~57 lignes)
│   ├── immersive.py         # Mode 1 - Immersive (~109 lignes)
│   ├── picturebook.py       # Mode 2 - Picturebook (~61 lignes)
│   └── tag_processor.py     # Mode 3 - Tag Processor (~158 lignes)
├── services/
│   ├── tag_parser.py        # Parsing des balises <image> (~37 lignes)
│   └── image_replacer.py    # Remplacement des balises (~44 lignes)
├── utils/
│   └── helpers.py           # Utilitaires de génération (~33 lignes)
├── ui/
│   └── components.py        # Composants Gradio (~69 lignes)
├── global_state.py          # État global (~17 lignes)
├── javascript/
│   └── script.js            # JavaScript personnalisé (~160 lignes)
├── workflows/               # Fichiers workflow JSON
├── tests/                   # Tests unitaires
├── style.css                # Styles CSS
└── requirements.txt         # Dépendances
```

### Principes de Conception

#### SOLID Principles

1. **Single Responsibility Principle (SRP)**: Chaque classe/module a une seule responsabilité
   - `ComfyUIClient`: communication API uniquement
   - `TagParser`: parsing regex des balises
   - `ImageReplacer`: remplacement texte
   - `UI`: interface Gradio uniquement

2. **Open/Closed Principle (OCP)**: Ajouter un nouveau mode = créer `modes/modeN.py` sans modifier le code existant

3. **Liskov Substitution Principle (LSP)**: Tous les modes implémentent l'interface `Mode` et sont interchangeables

4. **Interface Segregation Principle (ISP)**: Interfaces petites et spécifiques

5. **Dependency Inversion Principle (DIP)**: Dépendance vers des abstractions via injection de dépendances

---

## Modules

### script.py

**Fichier**: `script.py`  
**Lignes**: ~154  
**Rôle**: Point d'entrée principal de l'extension

#### Description

C'est le fichier principal qui orchestre toute l'extension. Il définit les paramètres par défaut, les fonctions de modification d'entrée/sortie, et l'interface utilisateur Gradio.

#### Paramètres

```python
params = {
    "comfyui_url": "http://127.0.0.1:8188",  # URL du serveur ComfyUI
    "selected_workflow": "",                  # Workflow sélectionné
    "mode": 0,                                # Mode d'opération (0-3)
}
```

#### Fonctions Principales

**`get_mode_instance(mode_index)`** (lignes 21-36)
- Retourne l'instance du mode correspondant à l'index
- Utilise un factory pattern pour créer les modes
- Retourne: Instance de `Mode`

**`input_modifier(string)`** (lignes 39-50)
- Modifie le texte d'entrée avant de l'envoyer à l'LLM
- Dépend du mode sélectionné
- Utilisé pour le mode Immersive (modifie l'input pour déclencher la génération)

**`output_modifier(string, state)`** (lignes 52-70)
- Modifie le texte de sortie de l'LLM
- Peut ajouter des images au texte
- Retourne le texte modifié (avec ou sans images)

**`custom_css()`** (lignes 72-75)
- Charge le CSS personnalisé depuis `style.css`
- Appliqué à l'interface TGUI

**`ui()`** (lignes 78-154)
- Crée tous les composants UI Gradio
- Configure les événements (clics, changements)
- Retourne la liste des composants

#### Événements UI

1. **Refresh Workflows** (lignes 86-94)
   - Rafraîchit la liste des workflows disponibles
   - Met à jour le dropdown

2. **Generate Test Image** (lignes 96-110)
   - Génère une image de test avec un prompt donné
   - Affiche le résultat dans un élément HTML

3. **Mode Selection** (lignes 122-131)
   - Met à jour le paramètre `mode`
   - Active/désactive la génération automatique pour modes 1 et 2

4. **Force/Suppress Button** (lignes 133-138)
   - Force ou supprime la génération d'image
   - Modifie l'état global `picture_response`

---

### core/client.py

**Fichier**: `core/client.py`  
**Lignes**: ~147  
**Rôle**: Client API ComfyUI

#### Description

Classe `ComfyUIClient` qui gère la communication avec le serveur ComfyUI via HTTP et WebSocket.

#### Attribution

- `server_address`: URL du serveur ComfyUI
- `client_id`: Identifiant unique du client (UUID)
- `ws`: Connexion WebSocket

#### Méthodes

**`__init__(server_address)`** (lignes 13-17)
- Initialise le client avec l'adresse du serveur
- Génère un `client_id` unique
- Initialise `ws` à None

**`queue_prompt(prompt, client_id)`** (lignes 18-31)
- Met une requête de génération dans la file d'attente
- Envoie un POST à `/prompt`
- Retourne: `{"prompt_id": "..."}`

**`get_image(filename, subfolder, folder_type)`** (lignes 33-49)
- Récupère les données d'une image générée
- Appel GET à `/view?filename=...&subfolder=...&type=...`
- Retourne: Données binaires de l'image

**`get_history(prompt_id)`** (lignes 51-63)
- Récupère l'historique d'une génération
- Appel GET à `/history/{prompt_id}`
- Retourne: Dict avec les résultats

**`connect()`** (lignes 65-73)
- Établit une connexion WebSocket
- URL: `ws://{server}/ws?clientId={client_id}`

**`generate_image(workflow, text_input)`** (lignes 75-147)
- Méthode principale de génération d'image
- Étapes:
  1. Connecte au WebSocket si nécessaire
  2. Injecte le prompt dans le workflow (remplace "YOUR PROMPT HERE")
  3. Randomise le seed pour chaque génération
  4. Met la requête dans la file d'attente
  5. Attend la fin de l'exécution via WebSocket
  6. Récupère l'historique et les images
  7. Retourne la première image générée

#### Gestion des Erreurs

- Lance `ValueError` si "YOUR PROMPT HERE" n'est pas trouvé dans le workflow
- Retourne `None` en cas d'erreur
- Print les erreurs pour le débogage

---

### core/workflow.py

**Fichier**: `core/workflow.py`  
**Lignes**: ~36  
**Rôle**: Gestion des workflows ComfyUI

#### Description

Module pour charger et lister les fichiers de workflow JSON.

#### Fonctions

**`get_workflows()`** (lignes 7-18)
- Retourne la liste des fichiers JSON dans le dossier `workflows/`
- Utilise `Path.glob("*.json")`
- Retourne: Liste de noms de fichiers

**`load_workflow(workflow_name)`** (lignes 21-36)
- Charge un fichier workflow JSON
- Lit le fichier et le parse en JSON
- Retourne: Dict représentant le workflow ou `None` si erreur

#### Structure des Workflows

Les workflows sont des dicts JSON avec la structure ComfyUI:
```json
{
  "1": {
    "inputs": {"prompt": "YOUR PROMPT HERE", ...},
    "class_type": "CLIPTextEncode"
  },
  "2": {...}
}
```

---

### modes/base.py

**Fichier**: `modes/base.py`  
**Lignes**: ~32  
**Rôle**: Classe abstraite pour les modes

#### Description

Interface `Mode` que tous les modes doivent implémenter. Assure la cohérence et la substitutabilité.

#### Classe: `Mode` (ABC)

**Méthodes Abstraites**

**`process_input(text)`** (lignes 9-19)
- Modifie le texte d'entrée avant envoi à l'LLM
- Args: `text` (str) - Texte d'entrée
- Retourne: Texte modifié

**`process_output(text, state)`** (lignes 21-31)
- Modifie le texte de sortie de l'LLM
- Peut ajouter des images
- Args: `text` (str), `state` (dict)
- Retourne: Texte modifié (éventuellement avec images)

---

### modes/manual.py

**Fichier**: `modes/manual.py`  
**Lignes**: ~57  
**Rôle**: Mode 0 - Génération manuelle

#### Description

Mode où les images ne sont générées que lorsque l'utilisateur appuie sur "Force the picture response".

#### Classe: `ManualMode`

**`__init__(params, picture_response=None)`** (lignes 11-12)
- Stocke les paramètres
- `picture_response` est l'état global

**`process_input(text)`** (lignes 14-23)
- Ne modifie pas l'input
- Retourne le texte tel quel

**`process_output(text, state)`** (lignes 25-57)
- Vérifie si `picture_response` est True
- Si oui:
  1. Charge le workflow sélectionné
  2. Génère l'image via `generate_webui()`
  3. Consomme `picture_response` (le met à False)
  4. Retourne texte + image HTML ou texte seul
- Print des logs pour le débogage

#### Flux

1. Utilisateur appuie sur "Force" → `toggle_generation(True)`
2. Envoi message à l'LLM
3. `output_modifier()` appelle `process_output()`
4. Si `picture_response=True`, génération d'image
5. `picture_response` est consommé (set à False)

---

### modes/immersive.py

**Fichier**: `modes/immersive.py`  
**Lignes**: ~109  
**Rôle**: Mode 1 - Mots-clés déclencheurs

#### Description

Mode qui détecte des mots-clés dans l'input utilisateur pour déclencher automatiquement la génération d'image.

#### Classe: `ImmersiveMode`

**`process_input(text)`** (lignes 15-47)
- Vérifie si des mots-clés sont présents via `_triggers_are_in()`
- Si déclencheur détecté:
  1. Appelle `toggle_generation(True)`
  2. Modifie le texte pour demander une description détaillée
  3. Extrait le sujet si "of" est présent
  4. Retourne texte modifié
- Mots-clés: "send", "mail", "message", "me", "fais" + "image", "pic", "photo", "snap", "selfie", "meme"

**`process_output(text, state)`** (lignes 49-88)
- Génère l'image si `picture_response=True`
- Même logique que ManualMode
- Consomme `picture_response` après génération

**`_triggers_are_in(string)`** (lignes 90-105)
- Vérifie la présence de mots-clés avec regex
- Regex: `(?aims)(send|mail|message|me|fais)\b.+ ?\b(image|pic(ture)?|photo|snap(shot)?|selfie|meme)s?\b`
- Ignore le texte entre `*` (formattage markdown)

**`_remove_surrounded_chars(string)`** (lignes 107-108)
- Supprime le texte entre `*` (italique markdown)
- Empêche les faux positifs

#### Exemples de Déclencheurs

- "send me a picture of a cat" → déclenche
- "fais moi une photo" → déclenche
- "show me yourself" → déclenche
- "I like cats" → ne déclenche pas

---

### modes/picturebook.py

**Fichier**: `modes/picturebook.py`  
**Lignes**: ~61  
**Rôle**: Mode 2 - Génération automatique

#### Description

Mode où une image est générée pour **chaque** réponse de l'LLM.

#### Classe: `PicturebookMode`

**`process_input(text)`** (lignes 13-22)
- Ne modifie pas l'input
- Retourne le texte tel quel

**`process_output(text, state)`** (lignes 24-61)
- Vérifie `picture_response` (doit être True pour modes 1 et 2)
- Si True:
  1. Génère l'image
  2. Consomme `picture_response`
  3. Retourne texte + image ou texte seul
- Active automatiquement au changement de mode (lignes 127-131 de script.py)

#### Particularité

- `picture_response` est activé automatiquement quand on sélectionne le mode Picturebook
- `toggle_generation(True)` est appelé dans `ui()` pour `x > 1 and x < 3`

---

### modes/tag_processor.py

**Fichier**: `modes/tag_processor.py`  
**Lignes**: ~158  
**Rôle**: Mode 3 - Balises `<image>`

#### Description

Mode le plus complexe qui parse les balises `<image>prompt</image>` dans la réponse de l'LLM et génère une image pour chaque balise.

#### Classe: `TagProcessorMode`

**`process_output(text, state)`** (lignes 28-66)
- Étapes:
  1. Parse les balises avec `parse_image_tags()`
  2. Si balises trouvées:
     - Extrait les prompts
     - Génère les images séquentiellement
     - Remplace les balises par les images
  3. Retourne texte modifié

**`_generate_multiple_images_sequential(prompts, workflow_name, url)`** (lignes 68-157)
- Génère plusieurs images une par une
- Pour chaque prompt:
  1. Recharge le workflow (évite la modification cumulative)
  2. Appelle `client.generate_image()`
  3. Attend 0.3s pour UX
  4. Ajoute le résultat à la liste
- Retourne: Liste de dicts avec `prompt`, `image_data`, `success`, `start_pos`, `end_pos`

#### Gestion des Erreurs

- Si workflow introuvable → tous les résultats ont `success=False`
- Si génération échoue → balise originale conservée dans le texte
- Logs détaillés pour chaque étape

#### Flux Complet

1. LLM répond avec `<image>prompt1</image> et <image>prompt2</image>`
2. `parse_image_tags()` extrait les prompts et positions
3. Images générées séquentiellement
4. `replace_image_tags_with_images()` remplace les balises
5. Texte final: "prompt1\n<img>...\n et <img>...\n"

---

### services/tag_parser.py

**Fichier**: `services/tag_parser.py`  
**Lignes**: ~37  
**Rôle**: Parsing des balises `<image>`

#### Description

Module pour extraire les balises `<image>...</image>` du texte avec leurs positions.

#### Fonction: `parse_image_tags(text)`

**Entrée**: Texte potentiellement contenant des balises  
**Sortie**: Liste de tuples `(prompt, start_pos, end_pos)`

#### Logique

1. Vérifie si les balises sont échappées (`&lt;image&gt;`)
2. Si échappées: déséchappe le texte d'abord
3. Utilise regex `<image>(.*?)</image>` avec `re.DOTALL`
4. Pour chaque match:
   - Extrait le contenu (prompt)
   - Stocke start_pos et end_pos
   - Strip le prompt
5. Retourne la liste

#### Regex Expliquée

- `<image>`: Ouverture de balise
- `(.*?)`: Capture non-greedy du contenu
- `</image>`: Fermeture de balise
- `re.DOTALL`: `.` inclut les newline

#### Exemples

```python
text = "<image>a cat</image> and <image>a dog</image>"
# Retourne: [
#   ("a cat", 0, 18),
#   ("a dog", 23, 40)
# ]
```

---

### services/image_replacer.py

**Fichier**: `services/image_replacer.py`  
**Lignes**: ~44  
**Rôle**: Remplacement des balises par les images

#### Description

Remplace les balises `<image>...</image>` par des balises `<img>` avec les données d'image en base64.

#### Fonction: `replace_image_tags_with_images(text, image_results)`

**Entrée**:
- `text`: Texte original
- `image_results`: Liste de dicts avec `prompt`, `image_data`, `success`, `start_pos`, `end_pos`

**Sortie**: Texte modifié avec balises remplacées

#### Logique

1. Vérifie si texte échappé → déséchappe si nécessaire
2. Trie les résultats par `start_pos`
3. Pour chaque résultat:
   - Si succès: crée balise `<img src="data:image/png;base64,...">`
   - Si échec: garde balise originale
4. Applique les remplacements de fin en début (pour préserver les positions)
5. Retourne texte modifié

#### Base64 Encoding

- `base64.b64encode(image_data).decode("utf-8")`
- Format: `data:image/png;base64,{encoded_data}`

#### Ordre des Remplacements

- De fin en début pour préserver les positions
- Exemple: positions [10, 50, 80] → remplace d'abord 80, puis 50, puis 10

---

### utils/helpers.py

**Fichier**: `utils/helpers.py`  
**Lignes**: ~33  
**Rôle**: Utilitaires de génération

#### Description

Fonctions utilitaires pour générer des images et les convertir en HTML.

#### Fonction: `generate_webui(prompt, workflow_name, url)`

**Rôle**: Génère une image et retourne une balise HTML img

**Logique**:
1. Crée `ComfyUIClient`
2. Charge le workflow
3. Appelle `client.generate_image()`
4. Si succès: encode en base64 et retourne HTML
5. Si échec: retourne `None`

#### Utilisation

Utilisée par:
- Mode Manual
- Mode Immersive
- Mode Picturebook
- Bouton "Generate Test Image"

---

### ui/components.py

**Fichier**: `ui/components.py`  
**Lignes**: ~69  
**Rôle**: Composants Gradio

#### Description

Crée tous les composants UI de l'extension.

#### Fonction: `create_ui_components(params)`

**Composants Créés**:

1. **comfy_url** (Textbox)
   - Label: "ComfyUI Server URL"
   - Valeur par défaut: `params["comfyui_url"]`

2. **selected_workflow** (Dropdown)
   - Liste des workflows disponibles
   - Valeur par défaut: premier workflow ou None

3. **refresh_btn** (Button)
   - Label: "Refresh Workflows"
   - Rafraîchit la liste des workflows

4. **mode** (Dropdown)
   - Options: ["Manual", "Immersive/Interactive", "Picturebook/Adventure", "Process Tags"]
   - Type: index (0-3)

5. **force_pic** (Button)
   - Label: "Force the picture response"
   - Active la génération

6. **suppr_pic** (Button)
   - Label: "Suppress the picture response"
   - Désactive la génération

7. **test_prompt** (Textbox)
   - Pour les tests de génération

8. **generate_btn** (Button)
   - Label: "Generate Test Image"
   - Génère une image de test

9. **output_image** (HTML)
   - Affiche l'image générée

#### Retourne

Dict avec toutes les références aux composants pour les événements

---

### global_state.py

**Fichier**: `global_state.py`  
**Lignes**: ~17  
**Rôle**: État global de l'extension

#### Description

Gère l'état global de la génération d'images.

#### Variables

**`picture_response`** (ligne 3)
- Booléen global
- `True` = génération activée
- `False` = génération désactivée

#### Fonctions

**`toggle_generation(*args)`** (lignes 6-17)
- Active/désactive la génération
- Sans args: toggle (`not picture_response`)
- Avec args: set à `args[0]`

#### Utilisation

Appelé par:
- Boutons Force/Suppress
- Mode Immersive (détection déclencheur)
- Mode Picturebook (sélection du mode)

---

### javascript/script.js

**Fichier**: `javascript/script.js`  
**Lignes**: ~160  
**Rôle**: JavaScript personnalisé pour TGUI

#### Description

JavaScript qui ajoute une fonctionnalité de commentaire et de génération ComfyUI sur sélection de texte.

#### Fonctionnalités

**1. Popup de Commentaire** (lignes 5-18)
- Crée un popup avec textarea et boutons
- Affiché après sélection de texte

**2. Détection de Sélection** (lignes 30-84)
- Écoute `mouseup`
- Vérifie si sélection dans chat
- Positionne le trigger button près de la sélection

**3. Popup Display** (lignes 87-98)
- Affiche le popup au clic sur trigger
- Positionne le popup

**4. Gestion des Boutons** (lignes 101-131)
- **Cancel**: ferme le popup
- **Submit**: insère le commentaire dans le chat
- **Comfy**: déclenche génération d'image

**5. Génération ComfyUI** (lignes 133-159)
- Insère le texte sélectionné dans un prompt caché
- Clique sur un button caché pour déclencher
- Feedback visuel "Generating..."

#### Sélecteurs

- `#chat`: zone de chat
- `.message`: message individuel
- `#chat-input textarea`: input du chat
- `#comfy_hidden_prompt`: prompt caché
- `#comfy_hidden_trigger`: trigger caché

---

## Modes de Fonctionnement

### Mode 0: Manual

**Caractéristiques**:
- Génération uniquement manuelle
- Boutons "Force" / "Suppress"
- `picture_response` doit être True

**Cas d'usage**:
- Génération occasionnelle
- Contrôle total sur quand générer

**Fichier**: `modes/manual.py`

### Mode 1: Immersive/Interactive

**Caractéristiques**:
- Détection de mots-clés
- Modifie l'input pour demander description
- Mots-clés: "send me a picture", "fais moi une photo", etc.

**Cas d'usage**:
- Rôles où l'utilisateur demande des images
- Interaction naturelle

**Fichier**: `modes/immersive.py`

### Mode 2: Picturebook/Adventure

**Caractéristiques**:
- Génération automatique pour chaque réponse
- Activé automatiquement au changement de mode
- Chaque réponse a une image

**Cas d'usage**:
- Histoires illustrées
- Aventures visuelles

**Fichier**: `modes/picturebook.py`

### Mode 3: Process Tags

**Caractéristiques**:
- Balises `<image>prompt</image>` dans la réponse
- Génération séquentielle
- Remplacement automatique des balises

**Cas d'usage**:
- Contrôle précis des images
- Multiple images par réponse

**Fichier**: `modes/tag_processor.py`

---

## Configuration

### Installation

1. **ComfyUI**: Assurez-vous que ComfyUI est installé et running
   - URL par défaut: `http://127.0.0.1:8188`

2. **Copie du dossier**:
   ```bash
   cp -r comfy_api_pictures extensions/
   ```

3. **Dépendances**:
   ```bash
   pip install websocket-client pytest pytest-mock pytest-cov
   ```

### Paramètres UI

- **ComfyUI Server URL**: Adresse du serveur ComfyUI
- **Workflow**: Sélection du fichier JSON
- **Mode**: Choix du mode d'opération
- **Force/Suppress**: Contrôle manuel de la génération

### Configuration Avancée

**Mots-clés Immersive** (modifiables dans `modes/immersive.py`):
```python
regex = "(?aims)(send|mail|message|me|fais)\\b.+ ?\\b(image|pic(ture)?|photo|snap(shot)?|selfie|meme)s?\\b"
```

**Délai Mode 3** (dans `modes/tag_processor.py:144`):
```python
time.sleep(0.3)  # Délai entre images
```

---

## Workflow ComfyUI

### Structure Requise

Un workflow doit contenir exactement la chaîne `"YOUR PROMPT HERE"` dans un node:

```json
{
  "1": {
    "inputs": {
      "prompt": "YOUR PROMPT HERE",
      "clip": ["2", 0]
    },
    "class_type": "CLIPTextEncode"
  }
}
```

### Configuration d'un Workflow

1. Ouvrir le workflow dans ComfyUI
2. Trouver le node qui encode le prompt positif
3. Remplacer le prompt par `"YOUR PROMPT HERE"`
4. Exporter en JSON
5. Sauvegarder dans `workflows/`

### Exemple de Workflow Complet

```json
{
  "3": {
    "inputs": {
      "ckpt_name": "model.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "4": {
    "inputs": {
      "prompt": "YOUR PROMPT HERE",
      "clip": ["3", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "5": {
    "inputs": {
      "prompt": "negative prompt",
      "clip": ["3", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "6": {
    "inputs": {
      "seed": 123456,
      "steps": 20,
      "cfg": 8.0,
      "sampler_name": "euler",
      "model": ["3", 0],
      "positive": ["4", 0],
      "negative": ["5", 0],
      "latent_image": ["7", 0]
    },
    "class_type": "KSampler"
  },
  "7": {
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage"
  },
  "8": {
    "inputs": {
      "samples": ["6", 0],
      "vae": ["3", 2]
    },
    "class_type": "VAEDecode"
  },
  "9": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": ["8", 0]
    },
    "class_type": "SaveImage"
  }
}
```

### Workflows Disponibles

Dossier `workflows/` contient:
- `DGR-Qwen-image-Rapid-AIO.json`
- `EBU-Qwen-image-Rapid-AIO.json`
- `JN-Qwen-image-Rapid-AIO.json`
- `Qwen-image-Rapid-AIO.json`
- `image_flux2_text_to_image_9b(1).json`

---

## Tests

### Structure des Tests

Dossier `tests/` contient:
- `conftest.py`: Fixtures pytest
- `test_tag_parser.py`: Tests du parser de balises
- `test_image_replacer.py`: Tests du remplacement
- `test_comfy_client.py`: Tests du client API
- `test_workflow_loader.py`: Tests de chargement workflow
- `test_mode_3.py`: Tests du mode Tags
- `test_modes_integration.py`: Tests d'intégration

### Exécution des Tests

```bash
# Tous les tests
pytest

# Avec couverture
pytest --cov=comfy_api_pictures

# Tests spécifiques
pytest tests/test_tag_parser.py -v

# Marqueurs
pytest -m slow  # Tests lents
pytest -m integration  # Tests d'intégration
```

### Fixtures Principales

**`sample_workflow`**: Workflow JSON avec placeholder  
**`mock_comfy_client`**: Client mocké  
**`sample_tags_text`**: Texte avec balises  
**`mock_ws_connection`**: WebSocket mocké  
**`params`**: Paramètres par défaut

### Couverture de Test

- **Tag Parser**: 13 tests (balises simples, multiples, échappées, etc.)
- **Image Replacer**: Tests de remplacement base64
- **Comfy Client**: Tests de génération, historique, WebSocket
- **Workflow Loader**: Tests de chargement, erreurs
- **Mode 3**: Tests complets de génération séquentielle
- **Integration**: Tests d'intégration tous modes

---

## Débogage

### Logs

L'extension print des logs détaillés:

```
[INIT] Extension initialized. Mode: 0, Workflow: 'test.json'
[MANUAL MODE] Generating image...
[MANUAL MODE] Using workflow: 'test.json'
[MANUAL MODE] Image generated successfully
```

### Niveaux de Logs

- `[INIT]`: Initialisation
- `[MODE N]`: Log spécifique au mode
- `[TEST MODE]`: Tests de génération
- `[MODE 3]`: Mode Tags (détailé)

### Problèmes Courants

**1. "YOUR PROMPT HERE" non trouvé**
- Vérifier le workflow JSON
- S'assurer que la chaîne exacte est présente

**2. Generation échoue**
- Vérifier ComfyUI running
- Vérifier URL dans UI
- Check logs pour erreurs

**3. Images ne s'affichent pas**
- Vérifier console browser
- Check base64 encoding
- Vériser format image

**4. Mots-clés ne déclenchent pas**
- Vérifier regex dans immersive.py
- Check format du texte (ignorer `*`)

---

## Extension

### Ajouter un Nouveau Mode

1. Créer `modes/modeN.py`:
```python
from .base import Mode

class ModeN(Mode):
    def __init__(self, params, picture_response=None):
        self.params = params
    
    def process_input(self, text):
        return text
    
    def process_output(self, text, state):
        # Logique du mode
        return text
```

2. Ajouter dans `modes/__init__.py`:
```python
from .modeN import ModeN
```

3. Ajouter dans `script.py:get_mode_instance()`:
```python
mode_classes = [
    ManualMode,
    ImmersiveMode,
    PicturebookMode,
    TagProcessorMode,
    ModeN,  # Nouveau mode
]
```

4. Ajouter dans `ui/components.py`:
```python
modes_list = [
    "Manual",
    "Immersive/Interactive",
    "Picturebook/Adventure",
    "Process Tags",
    "Mode N",  # Nouveau mode
]
```

### Ajouter un Service

1. Créer `services/nouveau_service.py`
2. Implémenter fonction spécifique
3. Importer dans `modes/` ou `utils/`
4. Écrire des tests

---

## Performance

### Optimisations

- **Mode 3**: Recharge workflow à chaque génération (évite modification cumulative)
- **Délai 0.3s** entre images Mode 3 (UX)
- **Seed randomisé** à chaque génération (variété)

### Limitations

- **Génération séquentielle** Mode 3 (pas parallèle)
- **Une image** par génération (sauf Mode 3)
- **Workflow reload** à chaque appel (sécurité)

---

## Sécurité

### Points de Sécurité

1. **Aucune donnée externe**: Tout local
2. **Pas de secrets**: URL ComfyUI configurée manuellement
3. **Validation input**: Regex pour mots-clés
4. **Sanitization**: Base64 encoding sécurisé

### Précautions

- Ne pas exposer ComfyUI sur internet sans auth
- Vérifier workflows avant utilisation
- Limiter taille prompts

---

## Maintenance

### Bonnes Pratiques

- **Fichiers < 200 lignes**: Respecté
- **Code documenté**: Docstrings présentes
- **Tests unitaires**: Couverture complète
- **Logs**: Pour débogage

### Refactoring

- Chaque module a une responsabilité unique
- Dépendances injectées
- Interface `Mode` pour extensibilité

---

## Conclusion

Cette extension fournit une intégration complète entre TGUI et ComfyUI avec 4 modes d'opération flexibles. L'architecture modulaire permet l'extension facile et la maintenance simplifiée.

Pour plus d'informations, consulter:
- README.md: Introduction rapide
- ARCHITECTURE.md: Vue d'ensemble technique
- Code source: Documentation inline