"""Word counts by section for a rendered manuscript, using the rules of
01.manuscript/_tools/stamp-wordcounts.py: the same word pattern, headings counted as prose
except the Abstract heading, captions and table text counted apart, references apart."""
import re
import sys
import zipfile
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f"{{{W}}}{tag}"
WORD = re.compile(r"[A-Za-z0-9À-ɏ][A-Za-z0-9À-ɏ'’.\-/]*")
words = lambda t: len(WORD.findall(t))
text = lambda p: "".join(n.text or "" for n in p.iter(w("t")))


def style(p):
    s = p.find(f"{w('pPr')}/{w('pStyle')}")
    return s.get(w("val")) if s is not None else ""


root = etree.fromstring(zipfile.ZipFile(sys.argv[1]).read("word/document.xml"))
h1, h2 = "Front", ""
prose, sub = {}, {}
other = dict(abstract=0, captions=0, tables=0, refs=0, floats=0)
for child in root.find(w("body")):
    if child.tag == w("tbl"):
        for p in child.iter(w("p")):
            if "aption" in style(p):
                other["captions"] += words(text(p)); other["floats"] += 1
            else:
                other["tables"] += words(text(p))
        continue
    if child.tag != w("p"):
        continue
    st, t = style(child), text(child)
    if st == "Heading1":
        h1, h2 = re.sub(r"^[\d.]+\s*", "", t.strip()), ""
        if h1.lower() != "abstract":
            prose[h1] = prose.get(h1, 0) + words(t)
        continue
    if st == "Heading2":
        h2 = re.sub(r"^[\d.]+\s*", "", t.strip())
        prose[h1] = prose.get(h1, 0) + words(t); sub[(h1, h2)] = sub.get((h1, h2), 0) + words(t)
        continue
    if st in ("Title", "Subtitle", "Author", "Date", "AbstractTitle", "SourceCode"):
        continue
    if st == "Bibliography":
        other["refs"] += words(t); continue
    if h1.lower() == "abstract":
        other["abstract"] += words(t); continue
    if "aption" in st:
        other["captions"] += words(t); other["floats"] += 1; continue
    prose[h1] = prose.get(h1, 0) + words(t)
    if h2:
        sub[(h1, h2)] = sub.get((h1, h2), 0) + words(t)

body = sum(v for k, v in prose.items() if k != "References")
print(f"Abstract {other['abstract']:,}")
for k, v in prose.items():
    if k == "References":
        continue
    print(f"{k} {v:,}")
    for (a, b), n in sub.items():
        if a == k:
            print(f"    {b} {n:,}")
print(f"Prose of the body {body:,}")
print(f"Captions {other['captions']:,} on {other['floats']} figures and tables, table text {other['tables']:,}, references {other['refs']:,}")
total = body + other["captions"] + other["tables"] + other["refs"]
print(f"Total with tables, captions and references, abstract apart {total:,}")
charged = max(0, other["floats"] - 3) * 300
print(f"Journal count, prose, abstract, captions and references plus 300 for each figure or table from the fourth "
      f"{body + other['abstract'] + other['captions'] + other['refs'] + charged:,}")
