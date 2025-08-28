# Auto-Tik : Générateur Automatique de Quiz Vidéo pour TikTok

Auto-Tik est une application Python qui génère automatiquement des vidéos de quiz pour TikTok. L'application utilise l'IA pour générer des questions, la synthèse vocale pour la narration, et des outils de montage vidéo pour créer des contenus engageants.

## Fonctionnalités

- Génération automatique de questions sur différents thèmes
- Synthèse vocale de haute qualité avec ElevenLabs
- Création de vidéos verticales optimisées pour TikTok
- Stockage local et cloud (AWS S3, Google Cloud Storage)
- Interface modulaire et extensible

## Prérequis

- Python 3.8+
- FFmpeg
- Clés API pour :
  - OpenAI
  - ElevenLabs
  - AWS (optionnel)
  - Google Cloud (optionnel)

## Installation

1. Cloner le repository :
```bash
git clone https://github.com/votre-username/auto-tik.git
cd auto-tik
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement :
```bash
cp .env.example .env
# Éditer .env avec vos clés API
```

## Structure du Projet

```
auto-tik/
├── .env                    # Variables d'environnement
├── requirements.txt        # Dépendances Python
├── README.md              # Documentation
├── main.py               # Point d'entrée
├── config/
│   └── settings.json     # Configuration
├── src/
│   ├── theme_selector.py  # Sélection des thèmes
│   ├── question_generator.py  # Génération des questions
│   ├── tts_engine.py     # Synthèse vocale
│   ├── video_creator.py  # Création vidéo
│   └── storage.py        # Gestion du stockage
└── assets/
    ├── backgrounds/      # Fonds vidéo
    ├── music/           # Musiques
    └── generated/       # Vidéos générées
```

## Utilisation

1. Configurer les paramètres dans `config/settings.json`
2. Lancer la génération :
```bash
python main.py
```

## Configuration

### settings.json

```json
{
    "video": {
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "duration": 15
    },
    "themes": [
        "histoire",
        "géographie",
        "cinéma",
        "culture_pop"
    ],
    "tts": {
        "provider": "elevenlabs",
        "voice_id": "default"
    },
    "storage": {
        "local_path": "assets/generated",
        "cloud_provider": "none"
    }
}
```

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Auteur

Ilyes
