# ComfyUI API Pictures - Architecture

## Structure du Code

```
comfy_api_pictures/
├── script.py                 # Entrée TGUI (~80 lignes)
├── core/
│   ├── client.py            # ComfyUIClient (120 lignes)
│   └── workflow.py          # load_workflow, get_workflows (40 lignes)
├── modes/
│   ├── base.py              # Interface Mode (ABC) (40 lignes)
│   ├── manual.py            # Mode 0 (60 lignes)
│   ├── immersive.py         # Mode 1 (80 lignes)
│   ├── picturebook.py       # Mode 2 (60 lignes)
│   └── tag_processor.py     # Mode 3 (200 lignes)
├── services/
│   ├── tag_parser.py        # parse_image_tags (60 lignes)
│   └── image_replacer.py    # replace_image_tags_with_images (80 lignes)
├── utils/
│   └── helpers.py           # generate_webui (60 lignes)
├── ui/
│   ├── components.py        # Gradio components (100 lignes)
│   └── handlers.py          # Event handlers (80 lignes)
├── workflows/               # ComfyUI workflow JSON files
├── style.css
├── README.md
└── requirements.txt
```

## Principes SOLID

### 1. Single Responsibility Principle (SRP)
Chaque classe/module a une seule responsabilité:
- `ComfyUIClient`: communication API ComfyUI uniquement
- `TagParser`: parsing regex des balises `<image>`
- `ImageReplacer`: remplacement texte
- `TagProcessorMode`: logique Mode 3 uniquement
- `UI`: interface Gradio uniquement

### 2. Open/Closed Principle (OCP)
Ajouter un nouveau mode = créer `modes/mode4.py`
- Pas de modification du code existant
- Chaque mode implémente l'interface `Mode`

### 3. Liskov Substitution Principle (LSP)
Tous les modes implémentent `Mode.process_input()` et `Mode.process_output()`
- Interchangeables sans casser le code

### 4. Interface Segregation Principle (ISP)
Interfaces petites et spécifiques:
- `ImageGenerator` (génère une image)
- `TagParser` (parse des balises)
- `WorkflowLoader` (charge un workflow)

### 5. Dependency Inversion Principle (DIP)
`script.py` dépend de modules abstraits
- Injection de dépendances via factory pattern

## Modes de Fonctionnement

### Mode 0 - Manual
- Génération manuelle via boutons "Force" / "Suppress"
- Fichier: `modes/manual.py`

### Mode 1 - Immersive/Interactive
- Détection de mots-clés ("send me a picture")
- Modification de l'input
- Fichier: `modes/immersive.py`

### Mode 2 - Picturebook/Adventure
- Génération automatique pour chaque réponse
- Fichier: `modes/picturebook.py`

### Mode 3 - Process Tags
- Parsing des balises `<image>prompt</image>`
- Génération séquentielle d'images
- Remplacement des balises par les images
- Fichier: `modes/tag_processor.py`

## Extension du Code

Pour ajouter un nouveau mode:
1. Créer `modes/new_mode.py`
2. Implémenter `Mode` class
3. Ajouter dans `modes/__init__.py`
4. Ajouter dans `get_mode_instance()`

## Maintenance

- Chaque fichier < 200 lignes
- Code clair et documenté
- Tests unitaires dans `tests/`