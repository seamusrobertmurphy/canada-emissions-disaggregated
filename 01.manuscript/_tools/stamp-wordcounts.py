#!/usr/bin/env python3
"""Count the rendered manuscript and fill its word count placeholders.

The manuscript carries placeholders that this script replaces with the rendered
document's own counts, so a declared length cannot drift from the document:

    {{WC_PROSE}}  {{WC_TOTAL}}  {{WC_ABSTRACT}}

WC_PROSE is running text without tables, captions, code or references. WC_TOTAL adds
tables, captions and references. WC_ABSTRACT is the Abstract section alone, found by
position between its heading and the next heading, and is in neither total.

The target journal is Climatic Change, chosen by Seamus on 1 November 2026. Its limit is
recorded in LIMITS with the page, the date it was read and its verbatim wording, and the
script computes the count the journal's own rule gives, WC_JOURNAL, and reports any excess
on every render. Read the guide again before submission, because publishers change it.

Run:  python3 01.manuscript/_tools/stamp-wordcounts.py <file.docx>
Wired into _quarto.yml as a post-render step, after format-tables.py.
"""
import os
import re
import shutil
import sys
import pathlib
import zipfile
from lxml import etree

# stem of the rendered file: the journal's limit, with its verified source
LIMITS = {
    "Manuscript": dict(
        journal="Climatic Change",
        total=10000,            # all text, references, figures and tables, by the rule below
        free_floats=3,          # figures and tables count 300 words each from the fourth
        float_words=300,
        abstract=250,           # 150 to 250 words, up to 450 for an original research article if needed
        abstract_max=450,
        source="https://link.springer.com/journal/10584/submission-guidelines, read 1 November 2026",
        wording=("Climatic Change will publish papers with up to 10,000 words, inclusive of all "
                 "text, references, figures and tables. Figures and tables are counted as 300 words "
                 "each against the total, beginning with the fourth figure or table. Submissions "
                 "exceeding the limit will be returned to the authors before review."),
    ),
}

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f"{{{W}}}{tag}"
WORD = re.compile(r"[A-Za-z0-9À-ɏ][A-Za-z0-9À-ɏ'’.\-/]*")


def words(text):
    return len(WORD.findall(text))


def para_text(p):
    return "".join(n.text or "" for n in p.iter(w("t")))


def style_of(p):
    s = p.find(f"{w('pPr')}/{w('pStyle')}")
    return s.get(w("val")) if s is not None else ""


def measure(root, limit=None):
    counts = dict(prose=0, captions=0, tables=0, refs=0, abstract=0, floats=0)
    in_abstract = False
    for child in root.find(w("body")):
        if child.tag == w("tbl"):
            # Quarto wraps each figure or table with its caption in a one-cell table, so the
            # caption is found inside it; everything else inside is table text
            for p in child.iter(w("p")):
                st, txt = style_of(p), para_text(p)
                if "aption" in st:
                    counts["captions"] += words(txt)
                    counts["floats"] += 1
                else:
                    counts["tables"] += words(txt)
            continue
        if child.tag != w("p"):
            continue
        st, txt = style_of(child), para_text(child)
        if st.startswith("Heading"):
            in_abstract = re.sub(r"^[\d.]+\s*", "", txt.strip().lower()) == "abstract"
            counts["prose"] += 0 if in_abstract else words(txt)
        elif st in ("Title", "Subtitle", "Author", "Date", "AbstractTitle", "SourceCode"):
            continue
        elif st == "Bibliography":
            counts["refs"] += words(txt)
        elif in_abstract:
            counts["abstract"] += words(txt)
        elif "aption" in st:
            counts["captions"] += words(txt)
            counts["floats"] += 1
        else:
            counts["prose"] += words(txt)
    out = {
        "WC_PROSE": counts["prose"],
        "WC_TOTAL": counts["prose"] + counts["captions"] + counts["tables"] + counts["refs"],
        "WC_ABSTRACT": counts["abstract"],
        "WC_REFS": counts["refs"],
        "WC_CAPTIONS": counts["captions"],
        "WC_FLOATS": counts["floats"],
    }
    if limit:
        charged = max(0, counts["floats"] - limit["free_floats"]) * limit["float_words"]
        out["WC_JOURNAL"] = counts["prose"] + counts["abstract"] + counts["captions"] + counts["refs"] + charged
    return out


def process(path):
    path = pathlib.Path(path)
    if not path.exists():
        print(f"  skipped, not found: {path}")
        return
    zin = zipfile.ZipFile(path)
    parts = {n: zin.read(n) for n in zin.namelist()}
    zin.close()
    root = etree.fromstring(parts["word/document.xml"])
    limit = LIMITS.get(path.stem)
    counts = measure(root, limit)

    print(f"  {path.name}: prose {counts['WC_PROSE']:,}, total with tables, captions and "
          f"references {counts['WC_TOTAL']:,}, abstract {counts['WC_ABSTRACT']:,}")
    if limit:
        print(f"  {limit['journal']} count {counts['WC_JOURNAL']:,} of {limit['total']:,} "
              f"(prose {counts['WC_PROSE']:,}, abstract {counts['WC_ABSTRACT']:,}, captions "
              f"{counts['WC_CAPTIONS']:,}, references {counts['WC_REFS']:,}, "
              f"{counts['WC_FLOATS']} figures and tables charged "
              f"{max(0, counts['WC_FLOATS'] - limit['free_floats']) * limit['float_words']:,})")
        over = [f"{limit['journal']} count over by {counts['WC_JOURNAL'] - limit['total']:,}"] * (counts["WC_JOURNAL"] > limit["total"])
        over += [f"abstract over the {limit['abstract_max']} word ceiling by {counts['WC_ABSTRACT'] - limit['abstract_max']:,}"] * (counts["WC_ABSTRACT"] > limit["abstract_max"])
        if over:
            print(f"\n{'!' * 74}\n  OVER THE LIMIT: {'; '.join(over)}.\n{'!' * 74}\n")
    else:
        print("  no verified journal limit recorded, so no limit was compared")

    hits = 0
    for p in root.iter(w("p")):
        txt = para_text(p)
        if "{{WC_" not in txt:
            continue
        for k, v in counts.items():
            txt = txt.replace("{{" + k + "}}", f"{v:,}")
        runs = p.findall(w("r"))
        for extra in runs[1:]:
            p.remove(extra)
        for t in runs[0].findall(w("t")):
            runs[0].remove(t)
        t = etree.SubElement(runs[0], w("t"))
        t.text = txt
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        hits += 1
    if not hits:
        return
    parts["word/document.xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    tmp = path.with_suffix(".docx.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in parts.items():
            zout.writestr(name, data)
    shutil.move(tmp, path)
    print(f"  {path.name}: {hits} word count placeholder paragraph(s) filled")


if __name__ == "__main__":
    args = sys.argv[1:] or [f for f in os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").split("\n")
                            if f.strip().endswith(".docx")]
    if not args:
        print("no .docx to count")
    for a in args:
        process(a.strip())
