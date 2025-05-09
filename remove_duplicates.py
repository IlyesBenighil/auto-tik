import json
import sys

def supprimer_doublons(fichier_entree, fichier_sortie=None):
    # Si aucun fichier de sortie n'est spécifié, on écrase le fichier d'entrée
    if fichier_sortie is None:
        fichier_sortie = fichier_entree
    
    # Lecture du fichier JSON
    with open(fichier_entree, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Vérification de la structure
    if 'questions' not in data:
        print(f"Erreur: Le fichier JSON ne contient pas de clé 'questions'")
        return False
    
    # Nombre initial de questions
    nombre_initial = len(data['questions'])
    
    # Ensemble pour suivre les questions déjà vues
    questions_vues = set()
    # Liste pour stocker les questions uniques
    questions_uniques = []
    
    # Parcourir toutes les questions
    for question_obj in data['questions']:
        # Vérifier si l'objet a les clés requises
        if 'question' not in question_obj or 'answer' not in question_obj:
            continue
        
        # Créer une représentation unique pour chaque paire question-réponse
        cle_unique = (question_obj['question'], question_obj['answer'])
        
        # Ajouter seulement si elle n'existe pas déjà
        if cle_unique not in questions_vues:
            questions_vues.add(cle_unique)
            questions_uniques.append(question_obj)
    
    # Mettre à jour les données avec les questions uniques
    data['questions'] = questions_uniques
    
    # Écrire le résultat dans le fichier de sortie
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"Nombre de questions avant: {nombre_initial}")
    print(f"Nombre de questions après: {len(questions_uniques)}")
    print(f"Nombre de doublons supprimés: {nombre_initial - len(questions_uniques)}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python remove_duplicates.py fichier_entree.json [fichier_sortie.json]")
        sys.exit(1)
    
    fichier_entree = sys.argv[1]
    fichier_sortie = sys.argv[2] if len(sys.argv) > 2 else None
    
    if supprimer_doublons(fichier_entree, fichier_sortie):
        print(f"Traitement terminé avec succès.")
    else:
        print(f"Erreur lors du traitement.") 