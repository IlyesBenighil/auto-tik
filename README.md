# Auto-Tik: Automatic Quiz Video Generator for TikTok  

Auto-Tik is a Python application that automatically generates quiz videos for TikTok. The app uses AI to generate questions, text-to-speech for narration, and video editing tools to create engaging content.  

## Features  

- Automatic generation of quiz questions on different topics  
- Creation of vertical videos optimized for TikTok  

## Prerequisites  

- Python 3.8+  
- FFmpeg  
- API keys for:  
  - MistralAPI  
  - Google Cloud  

## Installation  

1. Clone the repository:  
```bash
git clone https://github.com/your-username/auto-tik.git
cd auto-tik
```

2. Create a virtual environment:  
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:  
```bash
pip install -r requirements.txt
```

4. Set up environment variables:  
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Project Structure  

```
auto-tik/
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── README.md               # Documentation
├── main.py                 # Entry point
├── config/
│   └── settings.json       # Configuration
├── src/
│   ├── theme_selector.py   # Theme selection
│   ├── question_generator.py  # Question generation
│   ├── tts_engine.py       # Text-to-speech
│   ├── video_creator.py    # Video creation
│   └── storage.py          # Storage management
└── assets/
    ├── backgrounds/        # Video backgrounds
    ├── music/              # Music
    └── generated/          # Generated videos
```

## Usage  

1. Configure the parameters in `config/settings.json`  
2. Run the generator:  
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
        "history",
        "geography",
        "cinema",
        "pop_culture"
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

Contributions are welcome! Feel free to:  
1. Fork the project  
2. Create a branch for your feature  
3. Commit your changes  
4. Push to your branch  
5. Open a Pull Request  

## Author  
Ilyes 
