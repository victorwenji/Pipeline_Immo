

import pandas as pd
import numpy as np
import json
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class CityaDataCleaner:
    def __init__(self, json_file):
        """Initialiser avec le fichier JSON"""
        self.json_file = json_file
        self.df = None
        self.df_clean = None
        
    def charger_donnees(self):
        """Charger le fichier JSON"""
        print("=" * 60)
        print("CHARGEMENT DES DONNÉES")
        print("=" * 60)
        
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.df = pd.DataFrame(data)
            print(f"✓ {len(self.df)} annonces chargées")
            print(f"✓ {len(self.df.columns)} colonnes trouvées")
            print(f"\nColonnes disponibles: {', '.join(self.df.columns)}")
            
            return True
        except FileNotFoundError:
            print(f"✗ Fichier '{self.json_file}' introuvable!")
            return False
        except json.JSONDecodeError:
            print(f"✗ Erreur de lecture du fichier JSON!")
            return False
    
    def afficher_statistiques_initiales(self):
        """Afficher les statistiques avant nettoyage"""
        print("\n" + "=" * 60)
        print("STATISTIQUES INITIALES")
        print("=" * 60)
        
        print(f"\nNombre total d'annonces: {len(self.df)}")
        print(f"\nValeurs manquantes par colonne:")
        missing = self.df.isnull().sum()
        missing_pct = (missing / len(self.df) * 100).round(2)
        
        for col in self.df.columns:
            if missing[col] > 0:
                print(f"  • {col}: {missing[col]} ({missing_pct[col]}%)")
        
        print(f"\nTypes de données:")
        print(self.df.dtypes)
    
    def extraire_nombres(self, texte):
        """Extraire les nombres d'une chaîne de caractères"""
        if pd.isna(texte):
            return None
        
        texte = str(texte)
        # Chercher un nombre (entier ou décimal)
        match = re.search(r'(\d+(?:[.,]\d+)?)', texte.replace(' ', ''))
        if match:
            # Remplacer virgule par point pour conversion
            return float(match.group(1).replace(',', '.'))
        return None
    
    def nettoyer_prix(self, prix_str):
        """Nettoyer et convertir le prix en nombre"""
        if pd.isna(prix_str):
            return None
        
        prix_str = str(prix_str).lower()
        # Enlever les symboles et espaces
        prix_str = prix_str.replace('€', '').replace(' ', '').replace('\xa0', '')
        
        # Extraire le nombre
        nombre = self.extraire_nombres(prix_str)
        
        return nombre
    
    def nettoyer_surface(self, surface_str):
        """Nettoyer et convertir la surface en nombre"""
        if pd.isna(surface_str):
            return None
        
        surface_str = str(surface_str).lower()
        # Chercher le motif "XX m²" ou "XX m2"
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*m', surface_str)
        if match:
            return float(match.group(1).replace(',', '.'))
        
        # Sinon extraire juste le nombre
        return self.extraire_nombres(surface_str)
    
    def nettoyer_pieces(self, pieces_str):
        """Extraire le nombre de pièces"""
        if pd.isna(pieces_str):
            return None
        
        pieces_str = str(pieces_str).lower()
        # Chercher "X pièce(s)" ou "T3", "F4", etc.
        
        # Pattern 1: "3 pièces", "2 pieces"
        match = re.search(r'(\d+)\s*(?:pi[èe]ces?|rooms?)', pieces_str)
        if match:
            return int(match.group(1))
        
        # Pattern 2: "T3", "F4", "P2"
        match = re.search(r'[tTfFpP](\d+)', pieces_str)
        if match:
            return int(match.group(1))
        
        # Sinon extraire le premier nombre
        return self.extraire_nombres(pieces_str)
    
    def nettoyer_code_postal(self, code_str):
        """Extraire et nettoyer le code postal"""
        if pd.isna(code_str):
            return None
        
        code_str = str(code_str)
        # Chercher un code postal français (5 chiffres)
        match = re.search(r'\b(\d{5})\b', code_str)
        if match:
            return match.group(1)
        
        return None
    
    def extraire_departement(self, code_postal):
        """Extraire le département depuis le code postal"""
        if pd.isna(code_postal):
            return None
        
        code = str(code_postal)
        if len(code) >= 2:
            return code[:2]
        return None
    
    def categoriser_type_bien(self, type_str):
        """Catégoriser le type de bien"""
        if pd.isna(type_str):
            return 'Autre'
        
        type_str = str(type_str).lower()
        
        if 'appartement' in type_str or 'appart' in type_str:
            return 'Appartement'
        elif 'maison' in type_str or 'villa' in type_str:
            return 'Maison'
        elif 'terrain' in type_str:
            return 'Terrain'
        elif 'local' in type_str or 'commerce' in type_str or 'bureau' in type_str:
            return 'Local commercial'
        elif 'parking' in type_str or 'garage' in type_str:
            return 'Parking/Garage'
        else:
            return 'Autre'
    
    def nettoyer_donnees(self):
        """Nettoyer toutes les données"""
        print("\n" + "=" * 60)
        print("NETTOYAGE DES DONNÉES")
        print("=" * 60)
        
        self.df_clean = self.df.copy()
        
        # 1. Nettoyer le prix
        print("\n1. Nettoyage des prix...")
        if 'prix' in self.df_clean.columns:
            self.df_clean['prix_num'] = self.df_clean['prix'].apply(self.nettoyer_prix)
            print(f"   ✓ {self.df_clean['prix_num'].notna().sum()} prix nettoyés")
        
        # 2. Nettoyer la surface
        print("2. Nettoyage des surfaces...")
        if 'surface' in self.df_clean.columns:
            self.df_clean['surface_m2'] = self.df_clean['surface'].apply(self.nettoyer_surface)
            print(f"   ✓ {self.df_clean['surface_m2'].notna().sum()} surfaces nettoyées")
        
        # 3. Nettoyer le nombre de pièces
        print("3. Nettoyage du nombre de pièces...")
        if 'pieces' in self.df_clean.columns:
            self.df_clean['nb_pieces'] = self.df_clean['pieces'].apply(self.nettoyer_pieces)
            print(f"   ✓ {self.df_clean['nb_pieces'].notna().sum()} nombres de pièces extraits")
        
        # 4. Nettoyer le nombre de chambres
        print("4. Nettoyage du nombre de chambres...")
        if 'chambres' in self.df_clean.columns:
            self.df_clean['nb_chambres'] = self.df_clean['chambres'].apply(self.extraire_nombres)
            print(f"   ✓ {self.df_clean['nb_chambres'].notna().sum()} nombres de chambres extraits")
        
        # 5. Nettoyer le code postal et extraire département
        print("5. Nettoyage des codes postaux...")
        if 'code_postal' in self.df_clean.columns:
            self.df_clean['code_postal_clean'] = self.df_clean['code_postal'].apply(self.nettoyer_code_postal)
            self.df_clean['departement'] = self.df_clean['code_postal_clean'].apply(self.extraire_departement)
            print(f"   ✓ {self.df_clean['code_postal_clean'].notna().sum()} codes postaux nettoyés")
            print(f"   ✓ {self.df_clean['departement'].notna().sum()} départements extraits")
        
        # 6. Catégoriser le type de bien
        print("6. Catégorisation des types de biens...")
        if 'type_bien' in self.df_clean.columns:
            self.df_clean['categorie_bien'] = self.df_clean['type_bien'].apply(self.categoriser_type_bien)
            print(f"   ✓ Types de biens catégorisés")
            print(f"     Répartition: {self.df_clean['categorie_bien'].value_counts().to_dict()}")
        
        # 7. Compter le nombre de photos
        print("7. Traitement des photos...")
        if 'photos' in self.df_clean.columns:
            self.df_clean['nb_photos_reel'] = self.df_clean['photos'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
            print(f"   ✓ Nombre de photos comptées")
        
        # 8. Calculer le prix au m²
        print("8. Calcul du prix au m²...")
        if 'prix_num' in self.df_clean.columns and 'surface_m2' in self.df_clean.columns:
            self.df_clean['prix_m2'] = (
                self.df_clean['prix_num'] / self.df_clean['surface_m2']
            ).round(2)
            nb_prix_m2 = self.df_clean['prix_m2'].notna().sum()
            print(f"   ✓ {nb_prix_m2} prix au m² calculés")
        
        print("\n✓ Nettoyage terminé!")
    
    
    
    def calculer_statistiques(self):
        """Calculer des statistiques avancées"""
        print("\n" + "=" * 60)
        print("CALCULS ET STATISTIQUES")
        print("=" * 60)
        
        # 1. Statistiques par type de bien
        if 'categorie_bien' in self.df_clean.columns and 'prix_num' in self.df_clean.columns:
            print("\n1. Prix moyen par type de bien:")
            stats_type = self.df_clean.groupby('categorie_bien')['prix_num'].agg([
                ('nombre', 'count'),
                ('prix_moyen', 'mean'),
                ('prix_median', 'median'),
                ('prix_min', 'min'),
                ('prix_max', 'max')
            ]).round(2)
            print(stats_type)
        
        # 2. Statistiques par département
        if 'departement' in self.df_clean.columns and 'prix_m2' in self.df_clean.columns:
            print("\n2. Prix au m² moyen par département:")
            stats_dept = self.df_clean.groupby('departement')['prix_m2'].agg([
                ('nombre', 'count'),
                ('prix_m2_moyen', 'mean'),
                ('prix_m2_median', 'median')
            ]).round(2).sort_values('prix_m2_moyen', ascending=False).head(10)
            print(stats_dept)
        
        # 3. Statistiques par nombre de pièces
        if 'nb_pieces' in self.df_clean.columns and 'prix_num' in self.df_clean.columns:
            print("\n3. Prix moyen par nombre de pièces:")
            stats_pieces = self.df_clean.groupby('nb_pieces')['prix_num'].agg([
                ('nombre', 'count'),
                ('prix_moyen', 'mean')
            ]).round(2).sort_index()
            print(stats_pieces)
        
        # 4. Créer des catégories de prix
        
        # 5. Créer des catégories de surface
        if 'surface_m2' in self.df_clean.columns:
            self.df_clean['gamme_surface'] = pd.cut(
                self.df_clean['surface_m2'],
                bins=[0, 40, 70, 100, 150, float('inf')],
                labels=['< 40m²', '40-70m²', '70-100m²', '100-150m²', '> 150m²']
            )
            print("\n5. Répartition par gamme de surface:")
            print(self.df_clean['gamme_surface'].value_counts().sort_index())
        
        
        # 7. Identifier les bonnes affaires (prix/m² inférieur à la médiane)
        if 'prix_m2' in self.df_clean.columns:
            mediane_prix_m2 = self.df_clean['prix_m2'].median()
            self.df_clean['bonne_affaire'] = self.df_clean['prix_m2'] < mediane_prix_m2
            nb_bonnes_affaires = self.df_clean['bonne_affaire'].sum()
            print(f"\n7. Bonnes affaires potentielles (prix/m² < médiane):")
            print(f"  • {nb_bonnes_affaires} annonces identifiées")
    
    def selectionner_colonnes_finales(self):
        """Sélectionner et ordonner les colonnes pour l'export"""
        colonnes_export = [
            'url',
            'titre',
            'categorie_bien',
            'prix_num',
            'surface_m2',
            'prix_m2',
            'nb_pieces',
            'nb_chambres',
            'ville',
            'code_postal_clean',
            
        ]
        
        # Ne garder que les colonnes qui existent
        colonnes_disponibles = [col for col in colonnes_export if col in self.df_clean.columns]
        
        self.df_final = self.df_clean[colonnes_disponibles]
        
        return self.df_final
    
    def exporter_csv(self, nom_fichier='citya_clean.csv'):
        """Exporter les données nettoyées en CSV"""
        print("\n" + "=" * 60)
        print("EXPORT DES DONNÉES")
        print("=" * 60)
        
        df_export = self.selectionner_colonnes_finales()
        
        # Exporter
        df_export.to_csv(nom_fichier, index=False, encoding='utf-8-sig')
        
        print(f"\n✓ Données exportées dans '{nom_fichier}'")
        print(f"  • Nombre de lignes: {len(df_export)}")
        print(f"  • Nombre de colonnes: {len(df_export.columns)}")
        print(f"  • Colonnes exportées: {', '.join(df_export.columns)}")
    
    def generer_rapport(self, nom_fichier='rapport_analyse.txt'):
        """Générer un rapport d'analyse complet"""
        print("\n" + "=" * 60)
        print("GÉNÉRATION DU RAPPORT")
        print("=" * 60)
        
        with open(nom_fichier, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RAPPORT D'ANALYSE DES DONNÉES IMMOBILIÈRES CITYA\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Date du rapport: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Fichier source: {self.json_file}\n\n")
            
            # Section 1: Vue d'ensemble
            f.write("\n" + "=" * 80 + "\n")
            f.write("1. VUE D'ENSEMBLE\n")
            f.write("=" * 80 + "\n")
            f.write(f"Nombre total d'annonces: {len(self.df_clean)}\n")
            f.write(f"Nombre d'annonces avec données complètes: {self.df_clean['donnees_completes'].sum()}\n\n")
            
            # Section 2: Statistiques de prix
            f.write("\n" + "=" * 80 + "\n")
            f.write("2. STATISTIQUES DE PRIX\n")
            f.write("=" * 80 + "\n")
            if 'prix_num' in self.df_clean.columns:
                f.write(f"Prix moyen: {self.df_clean['prix_num'].mean():.2f} €\n")
                f.write(f"Prix médian: {self.df_clean['prix_num'].median():.2f} €\n")
                f.write(f"Prix minimum: {self.df_clean['prix_num'].min():.2f} €\n")
                f.write(f"Prix maximum: {self.df_clean['prix_num'].max():.2f} €\n\n")
            
            # Section 3: Statistiques de surface
            f.write("\n" + "=" * 80 + "\n")
            f.write("3. STATISTIQUES DE SURFACE\n")
            f.write("=" * 80 + "\n")
            if 'surface_m2' in self.df_clean.columns:
                f.write(f"Surface moyenne: {self.df_clean['surface_m2'].mean():.2f} m²\n")
                f.write(f"Surface médiane: {self.df_clean['surface_m2'].median():.2f} m²\n")
                f.write(f"Surface minimum: {self.df_clean['surface_m2'].min():.2f} m²\n")
                f.write(f"Surface maximum: {self.df_clean['surface_m2'].max():.2f} m²\n\n")
            
            # Section 4: Répartition par type
            f.write("\n" + "=" * 80 + "\n")
            f.write("4. RÉPARTITION PAR TYPE DE BIEN\n")
            f.write("=" * 80 + "\n")
            if 'categorie_bien' in self.df_clean.columns:
                repartition = self.df_clean['categorie_bien'].value_counts()
                for cat, count in repartition.items():
                    pct = (count / len(self.df_clean) * 100)
                    f.write(f"{cat}: {count} ({pct:.1f}%)\n")
            
            # Section 5: Top 10 départements
            f.write("\n" + "=" * 80 + "\n")
            f.write("5. TOP 10 DÉPARTEMENTS\n")
            f.write("=" * 80 + "\n")
            if 'departement' in self.df_clean.columns:
                top_dept = self.df_clean['departement'].value_counts().head(10)
                for dept, count in top_dept.items():
                    f.write(f"Département {dept}: {count} annonces\n")
        
        print(f"✓ Rapport généré: '{nom_fichier}'")
    
    def executer_pipeline_complet(self, fichier_csv='citya_clean.csv'):
        """Exécuter tout le pipeline de nettoyage"""
        print("\n" + "╔" + "=" * 78 + "╗")
        print("║" + " " * 20 + "PIPELINE DE NETTOYAGE CITYA" + " " * 31 + "║")
        print("╚" + "=" * 78 + "╝")
        
        # 1. Charger
        if not self.charger_donnees():
            return False
        
        # 2. Stats initiales
        self.afficher_statistiques_initiales()
        
        # 3. Nettoyer
        self.nettoyer_donnees()
        
        # 4. Gérer valeurs manquantes
        #self.gerer_valeurs_manquantes()
        
        # 5. Calculer statistiques
        #self.calculer_statistiques()
        
        # 6. Exporter
        self.exporter_csv(fichier_csv)
        
        # 7. Rapport
        self.generer_rapport()
        
        print("\n" + "╔" + "=" * 78 + "╗")
        print("║" + " " * 28 + "PIPELINE TERMINÉ ✓" + " " * 32 + "║")
        print("╚" + "=" * 78 + "╝\n")
        
        return True


# ============================================================================
# SCRIPT PRINCIPAL
# ============================================================================

if __name__ == '__main__':
    # Configuration
    FICHIER_JSON = r'Data_Immo/Data_Init/citya_immobilier1.json' 
    FICHIER_CSV_SORTIE = '../Pipeline_Immo/Data_Immo/Data_Init/citya_immobilier_clean.csv'
    
    # Créer l'instance du cleaner
    cleaner = CityaDataCleaner(FICHIER_JSON)
    
    # Exécuter le pipeline complet
    succes = cleaner.executer_pipeline_complet(FICHIER_CSV_SORTIE)
    
    if succes:
        print(f"\n✅ Fichier CSV propre disponible: {FICHIER_CSV_SORTIE}")
        print(f"✅ Rapport d'analyse disponible: rapport_analyse.txt")
        
        # Afficher un aperçu des données nettoyées
        print("\n" + "=" * 60)
        print("APERÇU DES DONNÉES NETTOYÉES (5 premières lignes)")
        print("=" * 60)
        print(cleaner.df_final.head())
    else:
        print("\n❌ Erreur lors de l'exécution du pipeline")