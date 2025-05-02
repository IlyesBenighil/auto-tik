import os
import json
from pathlib import Path
from typing import Optional
import boto3
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

class StorageManager:
    def __init__(self, config_path: str = "config/settings.json"):
        self.config = self._load_config(config_path)
        self.local_path = Path(self.config["storage"]["local_path"])
        self.cloud_provider = self.config["storage"]["cloud_provider"]
        
        # Création du dossier local
        self.local_path.mkdir(parents=True, exist_ok=True)
        
        # Initialisation des clients cloud si nécessaire
        self._init_cloud_clients()

    def _load_config(self, config_path: str) -> dict:
        """Charge la configuration depuis le fichier settings.json"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _init_cloud_clients(self):
        """Initialise les clients cloud selon la configuration"""
        if self.cloud_provider == "aws":
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            self.bucket_name = os.getenv("AWS_BUCKET_NAME")
        
        elif self.cloud_provider == "gcp":
            self.gcs_client = storage.Client()
            self.bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET")

    def save_video(self, video_path: str, filename: Optional[str] = None) -> str:
        """
        Sauvegarde la vidéo localement et dans le cloud si configuré.
        
        Args:
            video_path (str): Chemin de la vidéo à sauvegarder
            filename (Optional[str]): Nom du fichier de sortie
            
        Returns:
            str: Chemin final de la vidéo sauvegardée
        """
        try:
            # Génération du nom de fichier
            if not filename:
                filename = Path(video_path).name
            
            # Sauvegarde locale
            local_path = self.local_path / filename
            Path(video_path).rename(local_path)
            
            # Sauvegarde dans le cloud si configuré
            if self.cloud_provider == "aws":
                self.s3_client.upload_file(
                    str(local_path),
                    self.bucket_name,
                    f"videos/{filename}"
                )
            
            elif self.cloud_provider == "gcp":
                bucket = self.gcs_client.bucket(self.bucket_name)
                blob = bucket.blob(f"videos/{filename}")
                blob.upload_from_filename(str(local_path))
            
            return str(local_path)

        except Exception as e:
            raise Exception(f"Erreur lors de la sauvegarde de la vidéo: {str(e)}")

    def list_videos(self) -> list:
        """
        Liste toutes les vidéos sauvegardées.
        
        Returns:
            list: Liste des chemins des vidéos
        """
        try:
            videos = []
            
            # Vidéos locales
            for video in self.local_path.glob("*.mp4"):
                videos.append(str(video))
            
            # Vidéos dans le cloud
            if self.cloud_provider == "aws":
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix="videos/"
                )
                for obj in response.get("Contents", []):
                    videos.append(f"s3://{self.bucket_name}/{obj['Key']}")
            
            elif self.cloud_provider == "gcp":
                bucket = self.gcs_client.bucket(self.bucket_name)
                for blob in bucket.list_blobs(prefix="videos/"):
                    videos.append(f"gs://{self.bucket_name}/{blob.name}")
            
            return videos

        except Exception as e:
            raise Exception(f"Erreur lors de la liste des vidéos: {str(e)}")

    def delete_video(self, video_path: str):
        """
        Supprime une vidéo.
        
        Args:
            video_path (str): Chemin de la vidéo à supprimer
        """
        try:
            # Suppression locale
            if os.path.exists(video_path):
                os.remove(video_path)
            
            # Suppression dans le cloud
            if self.cloud_provider == "aws":
                key = f"videos/{Path(video_path).name}"
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
            
            elif self.cloud_provider == "gcp":
                bucket = self.gcs_client.bucket(self.bucket_name)
                blob = bucket.blob(f"videos/{Path(video_path).name}")
                blob.delete()

        except Exception as e:
            raise Exception(f"Erreur lors de la suppression de la vidéo: {str(e)}") 