from moviepy import VideoFileClip
import os
import sys

def trim_video(input_file, output_file, start_time=2):
    """
    Supprime les premières secondes d'une vidéo.
    
    Args:
        input_file (str): Chemin du fichier vidéo d'entrée
        output_file (str): Chemin du fichier de sortie
        start_time (float): Temps de début en secondes (par défaut: 2s)
    """
    try:
        print(f"Chargement de la vidéo: {input_file}")
        video = VideoFileClip(input_file)
        
        # Durée de la vidéo
        duration = video.duration
        print(f"Durée de la vidéo: {duration:.2f} secondes")
        
        if duration <= start_time:
            print(f"Erreur: La vidéo est plus courte que le temps de coupe ({start_time}s)")
            video.close()
            return False
        
        # Couper la vidéo à partir de start_time jusqu'à la fin
        print(f"Découpage de la vidéo à partir de {start_time}s")
        trimmed_video = video.subclipped(start_time)
        
        # Sauvegarder la nouvelle vidéo
        print(f"Sauvegarde de la vidéo coupée dans: {output_file}")
        trimmed_video.write_videofile(
            output_file,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            preset='ultrafast',
            threads=4
        )
        
        # Fermer les clips vidéo
        video.close()
        trimmed_video.close()
        
        print("Opération terminée avec succès!")
        return True
        
    except Exception as e:
        print(f"Erreur: {str(e)}")
        return False

if __name__ == "__main__":
    # Utiliser les arguments de ligne de commande si fournis
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.mp4', '_trimmed.mp4')
        start_time = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    else:
        # Utiliser back_3.mp4 par défaut
        input_file = "back_3.mp4"
        output_file = "back_3_fixed.mp4"
        start_time = 2.0
    
    # Vérifier si le fichier existe
    if not os.path.exists(input_file):
        print(f"Erreur: Le fichier {input_file} n'existe pas.")
        sys.exit(1)
    
    # Couper la vidéo
    success = trim_video(input_file, output_file, start_time)
    sys.exit(0 if success else 1) 