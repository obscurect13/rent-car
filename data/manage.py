import sqlite3

# Connexion à votre fichier de base de données
connexion = sqlite3.connect('rental.db')
curseur = connexion.cursor()

def get_tables():   
    try:
        # Requête pour récupérer le nom de toutes les tables (type = 'table')
        # On exclut 'sqlite_sequence' qui est une table interne générée automatiquement
        curseur.execute("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%';
        """)
        
        tables = curseur.fetchall()
        
        if tables:
            print("--- Liste des tables dans la base de données ---")
            for table in tables:
                print(f"- {table[0]}")
        else:
            print("La base de données ne contient aucune table.")
    
    except sqlite3.Error as e:
        print(f"Erreur lors de la lecture des tables : {e}")
    
    finally:
        # Fermeture de la connexion
        connexion.close()

def read_table(table_name):
    try:
            # 1. Exécuter la requête pour récupérer toutes les données de la table 'cars'
            curseur.execute("SELECT * FROM {}".format(table_name))
            
            # 2. Récupérer le nom des colonnes de la table
            # curseur.description contient les métadonnées de la dernière requête exécutée
            colonnes = [description[0] for description in curseur.description]
            
            # 3. Récupérer toutes les lignes de données
            lignes = curseur.fetchall()
            
            # 4. Affichage des résultats
            if lignes:
                # Afficher les en-têtes (le nom des colonnes séparés par des tabulations)
                print(" | ".join(colonnes))
                print("-" * (len(" | ".join(colonnes)) + 5)) # Ligne de séparation
                
                # Afficher chaque ligne de la table
                for ligne in lignes:
                    # On convertit chaque élément en chaîne de caractères pour l'affichage
                    print(" | ".join(str(valeur) for valeur in ligne))
                    
                print(f"\nNombre total de voitures trouvées : {len(lignes)}")
            else:
                print("La table 'cars' existe mais elle est actuellement vide.")
    
    except sqlite3.OperationalError as e:
        # Cette erreur survient généralement si la table 'cars' n'existe pas dans ce fichier .db
        print(f"Erreur opérationnelle : {e}")
        print("Vérifiez que le nom de la table est bien orthographié et que vous ciblez le bon fichier .db.")
    
    except sqlite3.Error as e:
        print(f"Une erreur SQLite est survenue : {e}")
        
read_table('cars')