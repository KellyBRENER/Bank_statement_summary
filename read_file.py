import pandas as pd
import os
import re
import json
import warnings
from fuzzywuzzy import fuzz

warnings.simplefilter("ignore", UserWarning)

# Définir le dossier où se trouvent les relevés de compte
dossier_releves = "../../relevé_de_compte"

# Vérifier si le dossier existe
if not os.path.exists(dossier_releves):
    print(f"Le dossier '{dossier_releves}' n'existe pas.")
    exit()

# Lister les fichiers disponibles
fichiers = [f for f in os.listdir(dossier_releves) if f.endswith(".xlsx")]

if not fichiers:
    print("Aucun fichier de relevé de compte trouvé.")
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

def nettoyer_json(fichier="categories.json"):
    """Nettoie les libellés dans le fichier JSON et détecte les doublons intelligemment."""
    try:
        with open(fichier, "r") as f:
            donnees = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    donnees_nettoyees = {}
    donnees_modifiees = False  # Suivi des modifications

    # Nettoyage des libellés et vérification des récurrences
    for libelle, info in donnees.items():
        libelle_nettoye = nettoyer_libelle(libelle)

        # Vérification de la récurrence
        if "recurrence" not in info or not info["recurrence"]:
            print(f"\n⚠️ La récurrence est manquante pour la catégorie '{info['categorie']}' du libellé '{libelle}'.")
            info["recurrence"] = demander_recurrence(libelle)
            donnees_modifiees = True

        donnees_nettoyees[libelle_nettoye] = info

    donnees_sans_doublons = donnees_nettoyees.copy()
    doublons_trouves = True

    while doublons_trouves:
        doublons_trouves = False

        for libelle1, info1 in list(donnees_sans_doublons.items()):
            for libelle2, info2 in list(donnees_sans_doublons.items()):
                if libelle1 != libelle2:
                    score_similarite = fuzz.ratio(libelle1.lower(), libelle2.lower())

                    if score_similarite > 85:  # Seuil ajustable
                        print(f"⚠️ Doublon détecté entre : '{libelle1}' et '{libelle2}'")
                        print(f"  Catégories : '{info1['categorie']}' et '{info2['categorie']}'")

                        choix = input(f"Conserver : 1 = {libelle1}, 2 = {libelle2}, 3 = Fusionner, 0 = Annuler : ").strip()

                        if choix == '1':
                            print(f"✅ '{libelle2}' a été supprimé.")
                            donnees_sans_doublons.pop(libelle2, None)
                        elif choix == '2':
                            print(f"✅ '{libelle1}' a été supprimé.")
                            donnees_sans_doublons.pop(libelle1, None)
                        elif choix == '3':
                            fusion = input(f"Entrez le libellé fusionné (ex: '{libelle1} / {libelle2}') : ").strip()
                            nouvelle_categorie = info1["categorie"] if info1["categorie"] == info2["categorie"] else f"{info1['categorie']} / {info2['categorie']}"
                            nouvelle_recurrence = info1["recurrence"] if info1["recurrence"] == info2["recurrence"] else "Occasionnel"

                            donnees_sans_doublons[fusion] = {
                                "categorie": nouvelle_categorie,
                                "recurrence": nouvelle_recurrence
                            }
                            donnees_sans_doublons.pop(libelle1, None)
                            donnees_sans_doublons.pop(libelle2, None)
                            print(f"✅ Fusion en '{fusion}' avec catégorie '{nouvelle_categorie}'.")

                        elif choix == '0':
                            print("❌ Annulation de la suppression.")
                        else:
                            print("⚠️ Choix invalide. Aucune suppression.")

                        doublons_trouves = True
                        break
            if doublons_trouves:
                break

    # Écriture des mises à jour dans le fichier JSON
    if donnees_modifiees:
        with open(fichier, "w") as f:
            json.dump(donnees_sans_doublons, f, indent=4)
        print("✅ Mise à jour du fichier JSON avec les récurrences et doublons traités.")

    return donnees_sans_doublons


def nettoyer_libelle(libelle):
    """Nettoie le libellé."""
    libelle = re.sub(r'[^a-zA-Z\s]', '', libelle)  # Ne garder que les lettres et les espaces
    libelle = re.sub(r'\s+', ' ', libelle).strip()  # Supprimer les espaces en trop
    return libelle


# Charger et nettoyer le JSON
donnees_json_nettoyees = nettoyer_json()  # Applique la fonction de nettoyage sur le fichier JSON

# Charger les catégories existantes
def charger_categories(fichier="categories.json"):
    try:
        with open(fichier, "r") as f:
            donnees = json.load(f)
            return sorted(set(entry["categorie"].strip().lower() for entry in donnees.values()))
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Retourne une liste vide si le fichier n'existe pas ou est corrompu


categories_existantes = charger_categories()  # Charger les catégories connues

# Lire le fichier Excel
df = pd.read_excel(nom_fichier, engine="openpyxl", header=None)  # Pas d'en-tête au début

# Fonction pour vérifier si une valeur est une date
def est_une_date(valeur):
    if isinstance(valeur, pd.Timestamp):
        return True
    if isinstance(valeur, (float, int)):
        try:
            return pd.to_datetime(valeur, origin='1899-12-30', unit='D', errors='coerce') is not pd.NaT
        except:
            return False
    if isinstance(valeur, str):
        try:
            return pd.to_datetime(valeur, dayfirst=True, errors='coerce') is not pd.NaT
        except:
            return False
    return False

# Gestion des catégories et récurrences
def demander_categorie(libelle, type_transaction, montant, categories_existantes, fichier="categories.json"):
    """Demande à l'utilisateur de catégoriser une transaction et de choisir une récurrence."""
    print(f"\nLibellé : {libelle}")
    print(f"Type de transaction : {type_transaction}")
    print(f"Montant : {montant:.2f}€")
    print("Ce libellé n'a pas encore de catégorie.")
    print("Choisissez une catégorie existante ou entrez une nouvelle catégorie.")

    print(f"{0}. Entrer une nouvelle catégorie")
    for i, categorie in enumerate(categories_existantes, 1):
        print(f"{i}. {categorie}")
    try:
        choix = int(input("Entrez le numéro de la catégorie : "))

        if choix == 0:  # Nouvelle catégorie
            nouvelle_categorie = input("Entrez la nouvelle catégorie : ")
            recurrence = demander_recurrence(libelle)  # Demander la récurrence
            stocker_donnees(libelle, nouvelle_categorie, recurrence, fichier)  # Sauvegarde

            # Enregistrer la nouvelle catégorie dans les catégories existantes
            categories_existantes.append(nouvelle_categorie)

            # Relancer la fonction pour réévaluer la catégorie et récurrence après la création de la nouvelle catégorie
            return trouver_categorie_approximative(libelle, donnees_json_nettoyees)

        elif 1 <= choix <= len(categories_existantes):
            # Si une catégorie existante est choisie, demander la récurrence et enregistrer les données
            recurrence = demander_recurrence(libelle)  # Demander la récurrence
            stocker_donnees(libelle, categories_existantes[choix - 1], recurrence, fichier)  # Sauvegarde

            # Relancer la fonction pour s'assurer que toutes les occurrences similaires sont traitées
            return trouver_categorie_approximative(libelle, donnees_json_nettoyees)

        else:
            print("⚠️ Choix invalide, veuillez recommencer.")
            return demander_categorie(libelle, type_transaction, montant, categories_existantes, fichier)
    except ValueError:
        print("⚠️ Entrée invalide, veuillez entrer un nombre.")
        return demander_categorie(libelle, type_transaction, montant, categories_existantes, fichier)


def demander_recurrence(libelle):
    """Demande à l'utilisateur la récurrence d'une dépense."""
    print(f"\nQuel type de récurrence pour la dépense '{libelle}' ?")
    print("1. Fixe (montant constant chaque mois)")
    print("2. Récurrent (plusieurs fois par mois, mais montant variable)")
    print("3. Occasionnel (quelques fois par an)")

    choix_recurrence = input("Entrez le numéro correspondant à la récurrence : ")

    if choix_recurrence == "1":
        return "Fixe"
    elif choix_recurrence == "2":
        return "Récurrent"
    elif choix_recurrence == "3":
        return "Occasionnel"
    else:
        print("⚠️ Choix invalide. Par défaut, récurrence 'Occasionnel'.")
        return "Occasionnel"

def enregistrer_categorie(libelle, categorie, fichier="categories.json"):
    """Ajoute une nouvelle catégorie à la base de données."""
    try:
        with open(fichier, "r") as f:
            donnees = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        donnees = {}  # Initialise un nouveau dictionnaire

    if libelle not in donnees:
        donnees[libelle] = {"categorie": categorie, "frequence": 1}
    else:
        donnees[libelle]["frequence"] += 1  # Augmente le compteur d'utilisation

    with open(fichier, "w") as f:
        json.dump(donnees, f, indent=4)

    print(f"✅ La catégorie '{categorie}' a été enregistrée pour '{libelle}'.")


def stocker_donnees(libelle, categorie, recurrence, fichier="categories.json"):
    """Enregistre la catégorie et la récurrence d'un libellé dans un fichier JSON."""
    try:
        with open(fichier, "r") as f:
            donnees = json.load(f)
    except FileNotFoundError:
        donnees = {}

    if libelle in donnees:
        donnees[libelle]["frequence"] += 1  # Augmente le compteur d'utilisation
    else:
        donnees[libelle] = {"categorie": categorie, "recurrence": recurrence, "frequence": 1}

    with open(fichier, "w") as f:
        json.dump(donnees, f, indent=4)

    print(f"✅ '{libelle}' enregistré avec la catégorie '{categorie}' et récurrence '{recurrence}'.")

def trouver_categorie_approximative(libelle, donnees_json):
    """Trouve la meilleure correspondance pour un libellé dans le JSON"""
    score_max = 80  # Ajustable selon le besoin
    meilleure_categorie = None
    meilleure_recurrence = None

    for cle, info in donnees_json.items():
        score = fuzz.ratio(libelle.lower(), cle.lower())
        if score > score_max:
            score_max = score
            meilleure_categorie = info["categorie"]
            meilleure_recurrence = info.get("recurrence", "Occasionnel")  # Assure une valeur par défaut

    return meilleure_categorie, meilleure_recurrence


# Trouver la première ligne contenant une date
ligne_depart = None
for index, row in df.iterrows():
    if any(est_une_date(cell) for cell in row):
        ligne_depart = index
        break

# Lire les données à partir de cette ligne
if ligne_depart is not None:
    df = pd.read_excel(nom_fichier, engine="openpyxl", skiprows=ligne_depart - 1)
else:
    print("❌ Impossible de trouver une date de début")
    exit()

# Séparer les colonnes 'Libellé' et 'Type de transaction' sur "\n"
df[['Type de transaction', 'Libellé']] = df['Libellé'].str.split("\n", n=1, expand=True)

# Ajouter les colonnes Catégorie et Récurrence si elles n'existent pas
df["Catégorie"] = ""
df["Récurrence"] = ""

# Boucle pour traiter les transactions
for index, row in df.iterrows():
    libelle = nettoyer_libelle(row["Libellé"])  # Nettoyer le libellé du fichier Excel
    type_transaction = row["Type de transaction"]
    montant = row["Débit euros"] if not pd.isna(row["Débit euros"]) else row["Crédit euros"]

    # Recherche de la catégorie et récurrence dans les données JSON nettoyées
    categorie, recurrence = trouver_categorie_approximative(libelle, donnees_json_nettoyees)

    if not categorie:  # Si aucune correspondance trouvée, demander à l'utilisateur
        categorie, recurrence = demander_categorie(libelle, type_transaction, montant, categories_existantes)

    # Assurer que les valeurs sont bien affectées
    df.at[index, "Catégorie"] = categorie
    df.at[index, "Récurrence"] = recurrence

# 📂 Définir le dossier de sauvegarde
dossier_sauvegarde = "../../relevés_traités"

# 📌 Vérifier si le dossier existe, sinon le créer
os.makedirs(dossier_sauvegarde, exist_ok=True)

# 📝 Demander à l'utilisateur un nom de fichier
nom_fichier = input("Entrez un nom pour le fichier JSON (sans extension) : ").strip()
if not nom_fichier:
    nom_fichier = "relevé_traite"  # Nom par défaut si l'utilisateur ne met rien

# 📂 Construire le chemin complet du fichier
chemin_fichier = os.path.join(dossier_sauvegarde, f"{nom_fichier}.json")

# 💾 Sauvegarder le DataFrame en JSON
df.to_json(chemin_fichier, orient="records", indent=4, force_ascii=False)

print(f"✅ Fichier enregistré sous : {chemin_fichier}")


# Aperçu du dataframe final après correction
print("\n📝 Aperçu du relevé de compte après traitement :")
print(df.head(10))


# Aperçu du dataframe final
print("\n📝 Aperçu du relevé de compte après traitement :")
print(df.head(10))
