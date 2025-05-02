import os
import requests
from pathlib import Path
from tqdm import tqdm

def download_file(url: str, output_path: Path):
    """Télécharge un fichier avec une barre de progression"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as file, tqdm(
        desc=output_path.name,
        total=total_size,
        unit='iB',
        unit_scale=True
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            pbar.update(size)

def main():
    # Création du dossier music s'il n'existe pas
    music_dir = Path("assets/music")
    music_dir.mkdir(parents=True, exist_ok=True)
    
    # Liste des musiques à télécharger (liens directs de Pixabay)
    musics = [
        {
            "name": "ambient_1.mp3",
            "url": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6ff1bab.mp3"
        },
        {
            "name": "ambient_2.mp3",
            "url": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6ff1bac.mp3"
        },
        {
            "name": "ambient_3.mp3",
            "url": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6ff1bad.mp3"
        }
    ]
    
    print("Téléchargement des musiques...")
    for music in musics:
        output_path = music_dir / music["name"]
        if not output_path.exists():
            print(f"\nTéléchargement de {music['name']}...")
            try:
                download_file(music["url"], output_path)
            except Exception as e:
                print(f"Erreur lors du téléchargement de {music['name']}: {str(e)}")
        else:
            print(f"\n{music['name']} existe déjà, téléchargement ignoré.")
    
    print("\nTéléchargement terminé !")

if __name__ == "__main__":
    main() 