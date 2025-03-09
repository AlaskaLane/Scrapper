import os
import pandas as pd
import re
import joblib

print('rijgoe^')

# === 1. Extraction depuis les dossiers ===
def extract_from_folders(base_path):
    data = []
    for animal in os.listdir(base_path):
        animal_path = os.path.join(base_path, animal)
        if os.path.isdir(animal_path):
            for image in os.listdir(animal_path):
                image_path = os.path.join(animal_path, image)
                data.append([animal, image_path])
    return pd.DataFrame(data, columns=["animal", "image_url"])

# === 2. Extraction depuis les noms de fichiers ===
def extract_from_filenames(base_path):
    data = []
    pattern = re.compile(r"\d+_\d+_(\w+).jpg")
    for image in os.listdir(base_path):
        match = pattern.match(image)
        if match:
            animal = match.group(1)
            image_path = os.path.join(base_path, image)
            data.append([animal, image_path])
    return pd.DataFrame(data, columns=["animal", "image_url"])

# === 3. Extraction depuis un fichier CSV ===
def extract_from_csv(csv_path):
    df = pd.read_csv(csv_path)
    return df[["animal", "image_url"]]

# === Fusion des données ===
def merge_data(folders_path, filenames_path, csv_path):
    df1 = extract_from_folders(folders_path)
    df2 = extract_from_filenames(filenames_path)
    df3 = extract_from_csv(csv_path)
    df_final = pd.concat([df1, df2, df3], ignore_index=True)
    df_final.drop_duplicates(inplace=True)
    return df_final

# === Execution ===
FOLDER_PATH = "/Users/gordillolois/Documents/OpenAnimalTracks/cropped_imgs/test"
FILENAME_PATH = "mammal_tracks/mammal_tracks/mammal_tracks"
CSV_PATH = "validated_images.csv"

print(os.path.exists(FOLDER_PATH))  # Doit retourner True
print(os.path.exists(FILENAME_PATH))  # Doit retourner True
print(os.path.exists(CSV_PATH))  # Doit retourner True

df = merge_data(FOLDER_PATH, FILENAME_PATH, CSV_PATH)

# Verifier le fichier de sortie 
print(df.head())
print(df.shape)

# Afficher tout les noms des animaux et le nombre total d'animaux

print(df["animal"].unique())

print(len(df["animal"].unique()))

# enregistrement du df avec joblib
joblib.dump(df, "mammal_tracks/mammal_tracks/nature_tracking_data/data.pkl")