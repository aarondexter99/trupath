#!/usr/bin/env python3
"""
trupath_gui.py  –  v0.8.1  (2 Jun 2025)
• Converts *all* sheets in a workbook
• Lets user pick orientation (columns works), folder name & location
• Saves <sheet>.csv files, opens the first one automatically
"""

from __future__ import annotations

import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pandas as pd
from trupath_analyser import convert_sheet

# ───────── optional drag-and-drop ───────────────────────────────────────
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    class _Tk(TkinterDnD.Tk):  # type: ignore
        pass

    DND = True
except ImportError:
    class _Tk(tk.Tk):  # type: ignore
        pass

    DND = False


def open_file(p: Path) -> None:
    for cmd in (["wslview", str(p)], ["xdg-open", str(p)]):
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            break
        except FileNotFoundError:
            continue


class Converter(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=20)
        self.pack(fill="both", expand=True)

        self.file: Path | None = None
        self.base_dir: Path = Path.home()
        self._build_ui()

    # ───────── UI layout ────────────────────────────────────────────────
    def _build_ui(self):
        self.drop = ttk.Label(
            self, text="Drop Excel file here\nor click Browse…",
            relief="ridge", padding=40, anchor="center"
        )
        self.drop.pack(fill="both", expand=True)
        if DND:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self._on_drop)

        ttk.Button(self, text="Browse…", command=self._browse_file).pack(pady=6)

        orient_box = ttk.LabelFrame(self, text="Data order")
        orient_box.pack(fill="x", pady=4)
        self.orientation = tk.StringVar(value="columns")
        for opt in ("columns", "rows"):
            ttk.Radiobutton(
                orient_box, text=opt.capitalize(), value=opt, variable=self.orientation
            ).pack(side="left", padx=8)

        folder_row = ttk.Frame(self)
        folder_row.pack(pady=4, fill="x")
        ttk.Label(folder_row, text="Output folder:").pack(side="left")
        self.folder_entry = ttk.Entry(folder_row, width=20)
        self.folder_entry.insert(0, "converted")
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        loc_row = ttk.Frame(self)
        loc_row.pack(pady=2, fill="x")
        ttk.Label(loc_row, text="Location:").pack(side="left")
        self.loc_label = ttk.Label(loc_row, text=str(self.base_dir), foreground="gray")
        self.loc_label.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(loc_row, text="Folder location…", command=self._choose_location).pack(
            side="right"
        )

        ttk.Button(self, text="Convert ALL sheets →", command=self._convert).pack(pady=12)

    # ───────── file helpers ────────────────────────────────────────────
    def _on_drop(self, event): self._load_file(event.data)

    def _browse_file(self):
        start = Path("/mnt/c/Users") if Path("/mnt/c/Users").exists() else Path.home()
        if p := filedialog.askopenfilename(
            initialdir=start, filetypes=[("Excel", "*.xlsx *.xls"), ("All files", "*.*")]
        ):
            self._load_file(p)

    def _load_file(self, raw):
        p = Path(raw.strip("{}"))
        if p.exists():
            self.file = p
            self.base_dir = p.parent
            self.drop["text"] = p.name
            self.loc_label["text"] = str(self.base_dir)
        else:
            messagebox.showerror("Error", f"{p} not found")

    def _choose_location(self):
        if d := filedialog.askdirectory(initialdir=self.base_dir, mustexist=True):
            self.base_dir = Path(d)
            self.loc_label["text"] = str(self.base_dir)

    # ───────── conversion core ─────────────────────────────────────────
    def _convert(self):
        if not self.file:
            messagebox.showwarning("No file", "Choose a workbook first.")
            return

        try:
            sheet_names = pd.ExcelFile(self.file).sheet_names
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        folder = self.folder_entry.get().strip() or "converted"
        out_dir = self.base_dir / folder

        outputs: list[Path] = []
        for idx, sheet in enumerate(sheet_names):
            try:
                out = convert_sheet(
                    excel_path=self.file,
                    sheet_name=sheet,
                    sheet_idx=idx,               # ← renamed keyword
                    out_dir=out_dir,
                    orientation=self.orientation.get(),
                )
                outputs.append(out)
            except Exception as exc:
                messagebox.showerror("Failed", f"{sheet}: {exc}")
                return

        if outputs:
            open_file(outputs[0])

        messagebox.showinfo(
            "Done", f"Saved {len(outputs)} file(s) in\n{out_dir}"
        )


# ───────── entry point ────────────────────────────────────────────────
def main() -> None:
    root = _Tk()
    root.title("Trupath Plate-Reader Converter")
    Converter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
