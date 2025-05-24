# converter.py  – Trupath analyser logic for Pyodide
import re, io, zipfile, pandas as pd, numpy as np

# reorder pattern within each 16-column block: 0,8,1,9,…,7,15
WITHIN_ORDER = [c for pair in zip(range(8), range(8, 16)) for c in pair]

def extract_ratio(df):
    block = df.iloc[7:199, 3:19]
    num = block.iloc[0::2].reset_index(drop=True)
    den = block.iloc[1::2].reset_index(drop=True)
    ratio = num / den
    ratio.columns = list("ABCDEFGHIJKLMNOP")
    ratio.insert(0, "X", np.arange(1, 97))
    return ratio

def transpose_plate(df):
    t = df.drop(columns="X").T
    t.index = list("ABCDEFGHIJKLMNOP")
    return t

def convert_workbook(buffer: bytes) -> bytes:
    """Excel bytes → zipfile bytes of CSVs."""
    xls = pd.ExcelFile(io.BytesIO(buffer))
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
        for sheet in xls.sheet_names:
            raw = pd.read_excel(xls, sheet_name=sheet, header=None)
            base = transpose_plate(extract_ratio(raw))
            blocks = []
            for b in range(6):
                sub = base.iloc[:, b*16:(b+1)*16].iloc[:, WITHIN_ORDER]
                sub.columns = range(16)
                blocks.append(sub)
                if b < 5:
                    blocks.append(pd.DataFrame(np.nan, index=range(5), columns=sub.columns))
            final = pd.concat(blocks, axis=0, ignore_index=True)
            safe = re.sub(r'[\\/:"*?<>|]+', "_", sheet).replace(" ", "")
            csv_bytes = final.to_csv(index=False, header=False, na_rep="").encode()
            z.writestr(f"{safe}.csv", csv_bytes)
    return zbuf.getvalue()
