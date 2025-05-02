from mistralai import Mistral
import os
from dotenv import load_dotenv

def test_model():
    print("Initialisation de l'API Mistral...")
    
    # Rechargement du fichier .env
    load_dotenv(override=True)
    
    # Initialisation du client Mistral avec la clé API
    api_key = os.getenv("MISTRAL_API_KEY")
    print(api_key)
    if not api_key:
        raise ValueError("La clé API Mistral n'est pas définie. Veuillez définir la variable d'environnement MISTRAL_API_KEY")
    
    client = Mistral(api_key=api_key)
    
    print("\nTest de génération de texte...")
    theme = "science"
    # Prompt plus direct et spécifique
    prompt = f"""Génère une question de type QCM sur le thème de '{theme}'.

Pour la question :
- Propose 4 choix de réponse numérotés ("1", "2", "3", "4").
- Indique laquelle est la bonne réponse.
- La réponse doit être correcte et vérifiable scientifiquement.

Le format de sortie doit être strictement en JSON comme ceci :

{
  "questions": [
    {
      "question": "Texte de la question",
      "choices": {
        "1": "Choix 1",
        "2": "Choix 2",
        "3": "Choix 3",
        "4": "Choix 4"
      },
      "answer": "3"
    }
    // 5 autres questions au même format, sans répétition sur les questions
  ]
}

A toi de me donner le QCM en JSON :"""
    
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    # Appel à l'API Mistral
    chat_response = client.chat.complete(
        model="open-mistral-nemo",
        messages=messages
    )
    
    print("\nRésultat :")
    print(chat_response.choices[0].message.content)

if __name__ == "__main__":
    test_model()
