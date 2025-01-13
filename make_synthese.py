import json
import os

# Définir le dossier où se trouvent les relevés de compte
dossier_releves = "../../relevés_traités"

# Vérifier si le dossier existe
if not os.path.exists(dossier_releves):
    print(f"Le dossier '{dossier_releves}' n'existe pas.")
    exit()

# Lister les fichiers disponibles
fichiers = [f for f in os.listdir(dossier_releves) if f.endswith(".json")]

if not fichiers:
    print("Aucun fichier de relevé traité trouvé.")
    exit()

# Afficher la liste des fichiers
print("\n📂 Fichiers disponibles :")
for i, fichier in enumerate(fichiers, 1):
    print(f"{i}. {fichier}")

# Demander à l'utilisateur de choisir un fichier
choix = input("\nEntrez le numéro du fichier à analyser : ")

try:
    choix = int(choix)
    if choix < 1 or choix > len(fichiers):
        raise ValueError
except ValueError:
    print("❌ Choix invalide. Veuillez entrer un numéro correct.")
    exit()

# Déterminer le fichier sélectionné
nom_fichier = os.path.join(dossier_releves, fichiers[choix - 1])
print(f"\n📄 Vous avez sélectionné : {nom_fichier}")

# Fonction pour charger le fichier JSON
def charger_fichier_json(fichier):
    try:
        with open(fichier, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Le fichier {fichier} n'a pas été trouvé.")
        return None
    except json.JSONDecodeError:
        print(f"❌ Le fichier {fichier} est corrompu ou invalide.")
        return None

# Fonction pour calculer la somme des crédits et débits fixes
def calculer_sommes(fichier_json):
    """Calcule les crédits et débits séparément pour chaque type de récurrence"""

    # Dictionnaires pour stocker les résultats
    resultats = {
        "Fixe": {"credits": 0.0, "debits": 0.0, "categories_credits": {}, "categories_debits": {}},
        "Récurrent": {"credits": 0.0, "debits": 0.0, "categories_credits": {}, "categories_debits": {}},
        "Occasionnel": {"credits": 0.0, "debits": 0.0, "categories_credits": {}, "categories_debits": {}},
    }

    for transaction in fichier_json:  # Parcours des transactions
        recurrence = transaction.get("Récurrence", "Occasionnel")  # Valeur par défaut "Occasionnel"
        categorie = transaction.get("Catégorie", "Inconnue")
        montant_credit = transaction.get("Crédit euros", 0) or 0
        montant_debit = transaction.get("Débit euros", 0) or 0

        if recurrence in resultats:
            if montant_credit > 0:  # Crédit
                resultats[recurrence]["credits"] += montant_credit
                resultats[recurrence]["categories_credits"][categorie] = (
                    resultats[recurrence]["categories_credits"].get(categorie, 0) + montant_credit
                )

            if montant_debit > 0:  # Débit
                resultats[recurrence]["debits"] += montant_debit
                resultats[recurrence]["categories_debits"][categorie] = (
                    resultats[recurrence]["categories_debits"].get(categorie, 0) + montant_debit
                )

    return resultats


# Fonction pour calculer le pourcentage par catégorie
def calculer_pourcentages(somme_totale, categories):
    pourcentages = {}
    for categorie, somme in categories.items():
        pourcentage = (somme / somme_totale) * 100 if somme_totale != 0 else 0
        pourcentages[categorie] = round(pourcentage, 2)  # Arrondi à 2 décimales
    return pourcentages


# Fonction pour afficher la synthèse
def afficher_synthese(resultats):
    """Affiche une synthèse complète des transactions par récurrence"""

    total_credits = 0.0
    total_debits = 0.0

    for recurrence, donnees in resultats.items():
        credits = donnees["credits"]
        debits = donnees["debits"]
        categories_credits = donnees["categories_credits"]
        categories_debits = donnees["categories_debits"]

        total_credits += credits
        total_debits += debits

        print(f"\n📊 Synthèse des transactions {recurrence} :")
        print(f"\n💸 Total des crédits {recurrence} : {credits:.2f}€")
        print(f"💰 Total des débits {recurrence} : {debits:.2f}€")
        print(f"\n🔹 Solde {recurrence} restant : {credits - debits:.2f}€")

        print("\n🔹 Répartition des crédits par catégorie :")
        pourcentages_credits = calculer_pourcentages(credits, categories_credits)
        for categorie, pourcentage in pourcentages_credits.items():
            print(f"  - {categorie}: {pourcentage:.2f}%")

        print("\n🔸 Répartition des débits par catégorie :")
        pourcentages_debits = calculer_pourcentages(debits, categories_debits)
        for categorie, pourcentage in pourcentages_debits.items():
            print(f"  - {categorie}: {pourcentage:.2f}%")

    # 🔹 Affichage des totaux globaux
    print("\n📊 🔥 Synthèse globale de toutes les transactions 🔥")
    print(f"\n💸 Total général des crédits : {total_credits:.2f}€")
    print(f"💰 Total général des débits : {total_debits:.2f}€")
    print(f"\n🔹 Solde final : {total_credits - total_debits:.2f}€")


# Fonction principale
def main():
    """Exécute le programme et affiche la synthèse des transactions"""

    donnees_json = charger_fichier_json(nom_fichier)

    if donnees_json is None:
        return

    # Calculer les sommes pour chaque récurrence
    resultats = calculer_sommes(donnees_json)

    # Afficher la synthèse complète
    afficher_synthese(resultats)

# Lancer le programme
if __name__ == "__main__":
    main()
