#!/usr/bin/env python3
"""Strip the author from a rendered manuscript for double-blind review.

Climatic Change reviews double blind and asks the author to remove names, affiliations
and anything identifying from the manuscript and every attached file, with a separate
title page carrying them. Quarto writes the author block from the YAML header and the
file properties from the user account, and neither can be switched off for one render
without touching the manuscript, so this runs on a copy of the render instead.

It removes every paragraph in the Author, Affiliation or Date styles, every paragraph
whose text contains one of the identifying strings below, and the creator and last
modified fields of the file properties. It then checks every part of the file for the
strings and stops with an error if any remains.

Run:  python3 01.manuscript/_tools/anonymise-docx.py 01.manuscript/Manuscript-anonymised.docx
"""
import re
import shutil
import sys
import pathlib
import zipfile
from lxml import etree

IDENTIFYING = ["Murphy", "Seamus", "seamusrobert", "0000-0002-1792-0351", "github.com/seamusrobertmurphy", "canada-emissions-disaggregated"]
STYLES = {"Author", "Affiliation", "Date"}

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f"{{{W}}}{tag}"


def anonymise(path):
    path = pathlib.Path(path)
    zin = zipfile.ZipFile(path)
    parts = {n: zin.read(n) for n in zin.namelist()}
    zin.close()

    root = etree.fromstring(parts["word/document.xml"])
    removed = 0
    for p in list(root.iter(w("p"))):
        style = p.find(f"{w('pPr')}/{w('pStyle')}")
        text = "".join(t.text or "" for t in p.iter(w("t")))
        if (style is not None and style.get(w("val")) in STYLES) or any(s in text for s in IDENTIFYING):
            p.getparent().remove(p)
            removed += 1
    parts["word/document.xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    core = parts["docProps/core.xml"].decode("utf-8")
    core = re.sub(r"(<dc:creator>)[^<]*", r"\1", core)
    core = re.sub(r"(<cp:lastModifiedBy>)[^<]*", r"\1", core)
    parts["docProps/core.xml"] = core.encode("utf-8")

    left = {n: s for n, data in parts.items() for s in IDENTIFYING if s.encode("utf-8") in data}
    if left:
        raise SystemExit(f"identifying text remains in {left}")

    tmp = path.with_suffix(".docx.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in parts.items():
            zout.writestr(name, data)
    shutil.move(tmp, path)
    print(f"  {path.name}: {removed} identifying paragraph(s) removed, file properties cleared, no identifying string remains")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        anonymise(a)
