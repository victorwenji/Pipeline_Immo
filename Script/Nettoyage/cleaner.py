
import argparse
import io
import json
import sys
import re
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np

def to_snake(name: str) -> str:
    if not isinstance(name, str):
        name = str(name)
    s = re.sub(r"[^\w]+", "_", name, flags=re.UNICODE)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = s.strip("_").lower()
    s = re.sub(r"_+", "_", s)
    return s

def read_json_any(path: str) -> pd.DataFrame:
    if path == "./Data_Immo/citya_immobilier.json" or path is None:
        raw = sys.stdin.read()
        buf = io.StringIO(raw)
        try:
            df = pd.read_json(buf, lines=True)
            if not df.empty:
                return pd.json_normalize(df.to_dict(orient="records"))
        except ValueError:
            buf.seek(0)
        buf.seek(0)
        data = json.load(buf)
    else:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Fichier introuvable: {path}")
        try:
            df = pd.read_json(p, lines=True)
            if not df.empty:
                return pd.json_normalize(df.to_dict(orient="records"))
        except ValueError:
            pass
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)

    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list) and (len(v) == 0 or isinstance(v[0], (dict, list))):
                data = v
                break
        if isinstance(data, dict):
            data = [data]

    if isinstance(data, list):
        return pd.json_normalize(data)
    else:
        return pd.json_normalize([data])

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.rename(columns={c: to_snake(c) for c in df.columns})
    counts = {}
    new_cols = []
    for c in df.columns:
        counts[c] = counts.get(c, 0) + 1
        new_cols.append(f"{c}_{counts[c]-1}" if counts[c] > 1 else c)
    df.columns = new_cols
    return df

def trim_strings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    obj_cols = df.select_dtypes(include=["object", "string"]).columns
    for c in obj_cols:
        df[c] = (
            df[c]
            .astype("string")
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
            .replace({"": pd.NA})
        )
    return df

def parse_bool_series(s: pd.Series) -> pd.Series:
    true_set = {"true", "1", "yes", "y", "t", "vrai", "oui"}
    false_set = {"false", "0", "no", "n", "f", "faux", "non"}
    def parse_val(v):
        if pd.isna(v):
            return pd.NA
        if isinstance(v, bool):
            return v
        sv = str(v).strip().lower()
        if sv in true_set:
            return True
        if sv in false_set:
            return False
        return pd.NA
    return s.map(parse_val).astype("boolean")

def smart_type_cast(df: pd.DataFrame, parse_dates: Optional[List[str]] = None) -> pd.DataFrame:
    df = df.copy()
    for c in df.columns:
        if parse_dates and c in parse_dates:
            df[c] = pd.to_datetime(df[c], errors="coerce", utc=True)
            continue
        if df[c].dtype == "object" or pd.api.types.is_string_dtype(df[c]):
            b = parse_bool_series(df[c])
            n_bool = b.dropna().unique()
            if set(n_bool).issubset({True, False}) and (b.notna().sum() >= 0.7 * len(df)):
                df[c] = b
                continue
            coerced = pd.to_numeric(df[c].astype("string").str.replace(",", ".", regex=False), errors="coerce")
            if coerced.notna().sum() >= 0.6 * len(df):
                df[c] = coerced
                continue
    for c in df.columns:
        if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c]):
            sample = df[c].dropna().astype(str).head(20)
            if sample.empty:
                continue
            looks_like_date = sample.str.contains(r"\d{4}-\d{2}-\d{2}", regex=True).mean() > 0.5
            if looks_like_date:
                df[c] = pd.to_datetime(df[c], errors="coerce", utc=True)
    return df

def drop_high_missing(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    if threshold is None:
        return df
    miss_ratio = df.isna().mean()
    keep = miss_ratio[miss_ratio <= threshold].index.tolist()
    return df[keep]

def fill_missing(df: pd.DataFrame, numeric_strategy: str, categorical_strategy: str) -> pd.DataFrame:
    df = df.copy()
    num_cols = df.select_dtypes(include=[np.number]).columns
    cat_cols = df.columns.difference(num_cols)
    if numeric_strategy == "median":
        df[num_cols] = df[num_cols].fillna(df[num_cols].median(numeric_only=True))
    elif numeric_strategy == "mean":
        df[num_cols] = df[num_cols].fillna(df[num_cols].mean(numeric_only=True))
    elif numeric_strategy == "zero":
        df[num_cols] = df[num_cols].fillna(0)
    elif numeric_strategy == "ffill":
        df[num_cols] = df[num_cols].fillna(method="ffill").fillna(method="bfill")
    if len(cat_cols) > 0:
        if categorical_strategy == "mode":
            modes = df[cat_cols].mode(dropna=True)
            if not modes.empty:
                df[cat_cols] = df[cat_cols].fillna(modes.iloc[0])
        elif categorical_strategy == "ffill":
            df[cat_cols] = df[cat_cols].fillna(method="ffill").fillna(method="bfill")
        elif categorical_strategy == "constant":
            df[cat_cols] = df[cat_cols].fillna("inconnu")
    return df

def clip_outliers_iqr(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.select_dtypes(include=[np.number]).columns:
        s = df[c].dropna()
        if s.empty: continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if not (isinstance(iqr, (int,float)) or np.isscalar(iqr)) or iqr == 0 or np.isnan(iqr):
            continue
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        df[c] = df[c].clip(lower=low, upper=high)
    return df

def evaluate_new_cols(df: pd.DataFrame, expressions: List[str]) -> pd.DataFrame:
    df = df.copy()
    for expr in expressions or []:
        if "=" in expr:
            col, rhs = expr.split("=", 1)
            col = to_snake(col.strip())
            df[col] = pd.eval(rhs, engine="python", parser="pandas", target=df, local_dict={"np": np, "pd": pd})
        else:
            col = f"calc_{abs(hash(expr))%10_000}"
            df[col] = pd.eval(expr, engine="python", parser="pandas", target=df, local_dict={"np": np, "pd": pd})
    return df

def extract_immo_fields(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'prix' in df.columns:
        s = df['prix'].astype('string')
        prix_num = s.str.replace(r"[^\d]", "", regex=True).str.extract(r"(\d+)", expand=False)
        df['prix_eur'] = pd.to_numeric(prix_num, errors='coerce')
        mens = s.str.extract(r"(\d[\d\s ]*)(?=\s*€\s*/?\s*mois)", expand=False)
        df['mensualite_eur'] = pd.to_numeric(mens.str.replace(r"[^\d]", "", regex=True), errors='coerce')
    if 'charges' in df.columns:
        c = df['charges'].astype('string')
        ch = c.str.extract(r"(\d[\d\s ]*)(?=\s*€\s*/?\s*mois)", expand=False)
        df['charges_eur_mois'] = pd.to_numeric(ch.str.replace(r"[^\d]", "", regex=True), errors='coerce')
    if 'titre' in df.columns:
        t = df['titre'].astype('string')
        pieces = t.str.extract(r"(\d+)\s*pi[eè]ces?", flags=re.IGNORECASE, expand=False)
        # surface: accepte "50m²" ou "50 m2"
        surf = t.str.extract(r"(\d+)\s*m\s*²|(\d+)\s*m2", flags=re.IGNORECASE, expand=False)
        if isinstance(surf, pd.DataFrame):
            surf_series = surf.apply(lambda r: r.dropna().iloc[0] if r.dropna().size else pd.NA, axis=1)
        else:
            surf_series = surf
        df['pieces'] = pd.to_numeric(pieces, errors='coerce')
        df['surface_m2'] = pd.to_numeric(surf_series, errors='coerce')
    if 'ville' in df.columns:
        v = df['ville'].astype('string')
        df['ville_nom'] = v.str.extract(r"^\s*([^\(]+?)\s*(?:\(|$)", expand=False).str.strip()
        cp = v.str.extract(r"\((\d{5})\)", expand=False)
        df['code_postal'] = pd.to_numeric(cp, errors='coerce')
    if 'ges' in df.columns:
        df['ges'] = pd.to_numeric(df['ges'], errors='coerce')
    if 'photos' in df.columns:
        def first_url(x):
            if isinstance(x, list) and x:
                return x[0]
            return pd.NA
        df['photo_url'] = df['photos'].map(first_url)
    return df

def build_report(before: pd.DataFrame, after: pd.DataFrame) -> str:
    lines = []
    lines.append("# Rapport de nettoyage")
    lines.append(f"- Lignes avant: {len(before)}, colonnes avant: {before.shape[1]}")
    lines.append(f"- Lignes après: {len(after)}, colonnes après: {after.shape[1]}")
    miss = after.isna().mean().sort_values(ascending=False).head(10)
    if not miss.empty:
        lines.append("- Top colonnes avec valeurs manquantes (après):")
        for k, v in miss.items():
            lines.append(f"  - {k}: {v:.1%}")
    dtypes = after.dtypes.astype(str)
    lines.append("- Types de colonnes (après):")
    for c, t in dtypes.items():
        lines.append(f"  - {c}: {t}")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Nettoie un fichier JSON et exporte un CSV propre.")
    parser.add_argument("input", help="Chemin du fichier JSON d'entrée, ou '-' pour STDIN")
    parser.add_argument("output", help="Chemin du CSV de sortie, ou '-' pour STDOUT")
    parser.add_argument("--missing-threshold", type=float, default=1.0,
                        help="Seuil (0..1) pour supprimer les colonnes trop manquantes (défaut: 1.0 = ne rien supprimer)")
    parser.add_argument("--fill-numeric", choices=["median", "mean", "zero", "ffill", "none"], default="median",
                        help="Stratégie de remplissage des numériques (défaut: median)")
    parser.add_argument("--fill-categorical", choices=["mode", "ffill", "constant", "none"], default="mode",
                        help="Stratégie de remplissage des catégorielles (défaut: mode)")
    parser.add_argument("--parse-dates", type=str, default="",
                        help="Colonnes à parser comme dates (séparées par des virgules)")
    parser.add_argument("--dedupe", action="store_true", help="Supprimer les lignes dupliquées")
    parser.add_argument("--clip-outliers", action="store_true", help="Cliper les valeurs aberrantes numériques (IQR)")
    parser.add_argument("--new-col", action="append", default=[],
                        help="Expression pour créer une nouvelle colonne, ex: 'total=price*qty'. Répéter l'option.")
    parser.add_argument("--report", type=str, default="", help="Chemin pour sauvegarder un rapport markdown du nettoyage")
    parser.add_argument("--extract-immo", action="store_true", help="Extraire prix, mensualité, surface, pièces, ville/cp, etc.")

    args = parser.parse_args()

    df_raw = read_json_any(args.input)

    df = standardize_columns(df_raw)
    df = trim_strings(df)

    if args.extract_immo:
        df = extract_immo_fields(df)

    parse_dates = [to_snake(c.strip()) for c in args.parse_dates.split(",") if c.strip()]
    df = smart_type_cast(df, parse_dates=parse_dates)

    if args.missing_threshold < 1.0:
        df = drop_high_missing(df, args.missing_threshold)

    df = fill_missing(df, numeric_strategy=args.fill_numeric, categorical_strategy=args.fill_categorical)

    if args.dedupe:
        df = df.drop_duplicates()

    if args.clip_outliers:
        df = clip_outliers_iqr(df)

    if args.new_col:
        df = evaluate_new_cols(df, args.new_col)

    if args.output == "./Data_Immo/DataCleaner/":
        df.to_csv(sys.stdout, index=False)
    else:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.output, index=False, encoding="utf-8")

    if args.report:
        report = build_report(df_raw, df)
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(report, encoding="utf-8")

if __name__ == "__main__":
    pd.options.display.width = 200
    pd.options.display.max_columns = 200
    main()
