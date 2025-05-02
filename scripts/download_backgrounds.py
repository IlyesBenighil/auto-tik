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
    # Création du dossier backgrounds s'il n'existe pas
    backgrounds_dir = Path("assets/backgrounds")
    backgrounds_dir.mkdir(parents=True, exist_ok=True)
    
    # Liste des images à télécharger (liens directs de Unsplash)
    images = [
        {
            "name": "gradient_blue.jpg",
            "url": "https://images.unsplash.com/photo-1557683316-973673baf926?w=1920&q=80"
        },
        {
            "name": "gradient_purple.jpg",
            "url": "https://images.unsplash.com/photo-1557683311-eac922347aa1?w=1920&q=80"
        },
        {
            "name": "gradient_orange.jpg",
            "url": "https://images.unsplash.com/photo-1557683312-8b3f5a573a3d?w=1920&q=80"
        },
        {
            "name": "gradient_green.jpg",
            "url": "https://images.unsplash.com/photo-1557683313-8b3f5a573a3e?w=1920&q=80"
        },
        {
            "name": "gradient_pink.jpg",
            "url": "https://images.unsplash.com/photo-1557683314-8b3f5a573a3f?w=1920&q=80"
        }
    ]
    
    print("Téléchargement des images d'arrière-plan...")
    for image in images:
        output_path = backgrounds_dir / image["name"]
        if not output_path.exists():
            print(f"\nTéléchargement de {image['name']}...")
            try:
                download_file(image["url"], output_path)
            except Exception as e:
                print(f"Erreur lors du téléchargement de {image['name']}: {str(e)}")
        else:
            print(f"\n{image['name']} existe déjà, téléchargement ignoré.")
    
    print("\nTéléchargement terminé !")

if __name__ == "__main__":
    main() 