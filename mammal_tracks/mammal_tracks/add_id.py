import csv

csv.field_size_limit(100000000)  # Augmenter la taille limite des champs CSV

def add_id_column(input_csv, output_csv):
    # Lire le fichier CSV existant
    with open(input_csv, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)  # Lire le fichier avec DictReader (permet d'accéder par clé)
        rows = list(reader)  # Charger toutes les lignes dans une liste
        
        # Ajouter l'ID à chaque ligne
        for index, row in enumerate(rows):
            row['id'] = index  # Ajouter l'ID (index de la ligne)
        
        # Sauvegarder les nouvelles lignes dans un nouveau fichier CSV
        with open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
            fieldnames = ['id'] + reader.fieldnames  # Ajouter "id" au début des noms de colonnes existants
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()  # Écrire l'en-tête avec la nouvelle colonne "id"
            writer.writerows(rows)  # Écrire toutes les lignes avec la nouvelle colonne "id"
        
    print(f"Le fichier CSV a été mis à jour et sauvegardé sous '{output_csv}'.")

# Exemple d'utilisation
input_csv = 'tracks_with_image.csv'  # Nom de votre fichier CSV d'entrée
output_csv = 'tracks_with_image.csv'  # Nom du fichier de sortie avec la colonne 'id'
add_id_column(input_csv, output_csv)
