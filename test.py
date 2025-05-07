from fugashi import Tagger

def tokenize_japanese(text):
    tagger = Tagger()
    tokens = []
    for word in tagger(text):
        tokens.append(word.surface)
    return tokens

# Exemple d'utilisation
if __name__ == "__main__":
    phrase = input("Entrez une phrase en japonais : ")
    result = tokenize_japanese(phrase)
    print("Découpage en mots et particules :")
    print(result)
