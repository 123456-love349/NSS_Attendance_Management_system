import os
import re
import pandas as pd
 
from utils.image_preprocess import preprocess_image
from utils.text_extractor import extract_text
 
 
# ─────────────────────────────────────────────
#  ID Helpers  — adjust regex to your college's format
# ─────────────────────────────────────────────
 
def clean_id(text: str) -> str:
    """Strip all spaces and convert to uppercase."""
    return re.sub(r"\s+", "", str(text)).upper()
 
 
def is_crn(text: str) -> bool:
    """
    CRN = purely numeric, 7-10 digits.
    Example valid CRNs: 2212345  /  1234567890
    Adjust the {7,10} range to match YOUR college's CRN length.
    """
    t = clean_id(text)
    return bool(re.fullmatch(r"\d{7,10}", t))
 
 
def is_urn(text: str) -> bool:
    """
    URN = alphanumeric, 8-14 characters.
    Example valid URNs: 22BTCSE001  /  2215CSE1234
    Adjust the pattern to match YOUR college's URN format.
    """
    t = clean_id(text)
    return bool(re.fullmatch(r"[A-Z0-9]{8,14}", t))
 
 
def extract_ids_from_ocr(ocr_results: list) -> dict:
    """
    Walk every OCR token and sort into CRN or URN buckets.
    Returns {"crn": [...], "urn": [...]}
    """
    crns, urns = [], []
 
    for item in ocr_results:
        raw     = item.get("text", "").strip()
        cleaned = clean_id(raw)
 
        if not cleaned:
            continue
 
        if is_crn(cleaned) and cleaned not in crns:
            crns.append(cleaned)
        elif is_urn(cleaned) and cleaned not in urns:
            urns.append(cleaned)
 
    return {"crn": crns, "urn": urns}
 
 
# ─────────────────────────────────────────────
#  Master Excel loader
# ─────────────────────────────────────────────
 
def load_master_excel(excel_path: str) -> pd.DataFrame:
    """
    Load the master (online) attendance Excel.
    The file MUST have columns named CRN and/or URN.
    All other columns (Name, Branch, Section…) are carried through.
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(
            f"Master Excel not found: {excel_path}\n"
            "Make sure 'uploads/attendance.xlsx' exists."
        )
 
    df = pd.read_excel(excel_path, dtype=str)
 
    # Normalise headers → lowercase + underscores
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
 
    if "crn" not in df.columns and "urn" not in df.columns:
        raise ValueError(
            "Master Excel must contain a 'CRN' and/or 'URN' column. "
            f"Found columns: {list(df.columns)}"
        )
 
    # Clean id columns
    for col in ("crn", "urn"):
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: clean_id(str(x)) if pd.notna(x) else ""
            )
 
    return df
 
 
# ─────────────────────────────────────────────
#  OCRReader — main class
# ─────────────────────────────────────────────
 
class OCRReader:
 
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
 
    # ── Public API ────────────────────────────
 
    def read_image(self, image_path: str) -> dict:
        """
        Full pipeline:
          1. Preprocess image
          2. Run OCR
          3. Extract CRN / URN tokens
          4. Compare with master Excel (by CRN / URN only, NOT name)
          5. Return result dict for the template
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
 
        # 1 — preprocess
        _original, processed = preprocess_image(image_path)
 
        # 2 — OCR
        ocr_results = extract_text(processed)
 
        # 3 — extract IDs
        detected = extract_ids_from_ocr(ocr_results)
 
        # 4 — compare
        master_df       = load_master_excel(self.excel_path)
        comparison_data = self._compare(detected, master_df)
 
        return {
            "detected_crn_count": len(detected["crn"]),
            "detected_urn_count": len(detected["urn"]),
            "detected_crns":      detected["crn"],
            "detected_urns":      detected["urn"],
            "comparison_data":    comparison_data,
        }
 
    def get_best_match(self, image_path: str) -> dict:
        """Backward-compatibility alias."""
        return self.read_image(image_path)
 
    # ── Internal ──────────────────────────────
 
    def _compare(self, detected: dict, master_df: pd.DataFrame) -> list:
        """
        Mark every student in the master Excel as Present or Absent.
        Matching priority: CRN first, URN as fallback.
        Name is NEVER used for matching.
        """
        detected_crns = set(detected["crn"])
        detected_urns = set(detected["urn"])
 
        rows = []
 
        for _, row in master_df.iterrows():
            master_crn = row.get("crn", "")
            master_urn = row.get("urn", "")
 
            present = False
 
            # Try CRN match first
            if master_crn and detected_crns:
                present = master_crn in detected_crns
 
            # Fallback to URN
            if not present and master_urn and detected_urns:
                present = master_urn in detected_urns
 
            entry = {
                "CRN":    master_crn,
                "URN":    master_urn,
                "Status": "Present" if present else "Absent",
            }
 
            # Carry all other columns (Student Name, Branch, Section…)
            for col in master_df.columns:
                if col not in ("crn", "urn"):
                    nice_key = col.replace("_", " ").title()
                    entry[nice_key] = row.get(col, "")
 
            rows.append(entry)
 
        return rows
 