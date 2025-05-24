#!/usr/bin/env python3
"""
trupath_analyser.py  –  v0.14  (2 Jun 2025)

• Extract D8–S199
• Row-pair ratio  → 96 values / column
• Transpose       → 16 rows (A–P) × 96 columns
• For each 16-col block:
      reorder cols 0,8,1,9,2,10…7,15
      rename cols 0-15   (so every block sits in A–P)
• Stack blocks vertically with 5 blank rows between
• Output = 121 rows × 16 columns, headerless, indexless
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, List

import numpy as np
import pandas as pd


# ─────── helpers ────────────────────────────────────────────────────────
def extract_ratio_block(df: pd.DataFrame) -> pd.DataFrame:
    block = df.iloc[7:199, 3:19]                       # D8:S199
    num = block.iloc[0::2].reset_index(drop=True)
    den = block.iloc[1::2].reset_index(drop=True)
    ratio = num / den
    ratio.columns = list("ABCDEFGHIJKLMNOP")
    ratio.insert(0, "X", np.arange(1, 97))
    return ratio


def transpose_plate(df: pd.DataFrame) -> pd.DataFrame:
    trans = df.drop(columns="X").T                     # 16×96
    trans.index = list("ABCDEFGHIJKLMNOP")
    return trans


WITHIN_ORDER = [c for pair in zip(range(8), range(8, 16)) for c in pair]  # 0,8,1,9…

# ─────── core conversion ────────────────────────────────────────────────
def convert_sheet(
    excel_path: Path,
    sheet_name: str,
    sheet_idx: int,
    out_dir: Path,
    orientation: Literal["columns", "rows"] = "columns",
) -> Path:
    engine = "openpyxl" if excel_path.suffix.lower().endswith("x") else "xlrd"
    raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None, engine=engine)

    if orientation != "columns":
        raise NotImplementedError("Rows-orientation not yet implemented.")

    base = transpose_plate(extract_ratio_block(raw))    # 16 × 96

    blocks: List[pd.DataFrame] = []
    for blk in range(6):
        sub = base.iloc[:, blk * 16 : (blk + 1) * 16]
        sub = sub.iloc[:, WITHIN_ORDER]                 # reorder cols
        sub.columns = range(16)                         # rename to 0-15
        blocks.append(sub)
        if blk < 5:                                     # 5 empty rows gap
            blank = pd.DataFrame(np.nan, index=range(5), columns=sub.columns)
            blocks.append(blank)

    final = pd.concat(blocks, axis=0, ignore_index=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[\\/:"*?<>|]+', "_", sheet_name).replace(" ", "")
    out_path = out_dir / f"{safe}.csv"
    final.to_csv(out_path, index=False, header=False, na_rep="")
    return out_path
