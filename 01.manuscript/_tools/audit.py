"""Audit of a rendered submission set, run after every render of the blinded manuscript.

Usage, from the repository root:
    python3 01.manuscript/_tools/audit.py 01.manuscript/Manuscript-YYYYMMDD.docx [--words LIST]

The blinded Word file names the set, and the other four files and the four sources are looked
for beside it under the same date. The script exits with status 1 if any of eight checks fails.
  1. A word from the list in the repository's hidden, untracked settings folder appears in the five files or their sources.
  2. A number in the abstract is not printed in the Results.
  3. A glossary count is used two ways, treatments other than four or accounts other than three.
  4. A work cited in the manuscript source is missing from the References source, or listed there and never cited.
  5. A figure, table or Online Resource is first cited out of order, cited and absent, or present and never cited.
  6. A borrowed table, figure or box number sits outside its citation bracket.
  7. The five files and the four sources do not share the blinded file's date suffix.
  8. The journal count is over 10,000 words.
The list of check 1 is read from a file and never written here, so this script names none of its words.
"""
import argparse
import html
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
# The word list sits in a hidden folder at the root that git ignores, found by its file name
WORD_LIST = next(iter(sorted(ROOT.glob(".*/audit-words.txt"))), ROOT / "audit-words.txt")
LIMIT = 10_000
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f"{{{W}}}{tag}"

SET = ["Manuscript", "Title-page", "Cover-letter", "References", "Online-Resources"]
SOURCES = ["Manuscript", "Cover-letter", "References", "Online-Resources"]
CANON = {"treatments": "four", "accounts": "three"}
COUNT_WORDS = "one|two|both|three|four|five|six|seven|eight|nine|ten"
# A year that is part of a document's name is not a result, such as "the 2013 Kyoto Protocol Supplement"
NAMED_YEAR = re.compile(r"\b(?:19|20)\d{2}(?= (?:Kyoto Protocol Supplement|IPCC|Refinement|Wetlands Supplement|"
                        r"Guidelines|national greenhouse gas inventory|National Inventory Report))")
NUM = re.compile(r"(?<![\d.,])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?!\d)")
BORROWED = re.compile(r"\b(?:Tables?|Figs?\.|Figures?|Box(?:es)?)\s+[A-Z]?\d+(?:[.\-–]\d+)+")
MENTION = re.compile(r"\b(Tables?|Figs?\.|Figures?)\s+(\d+)(?![.\-–]\d)((?:\s*(?:,|and|to|–)\s*\d+(?![.\-–]\d))*)")
OR_MENTION = re.compile(r"\bOnline Resources?\s+(\d+)((?:\s*(?:,|and|to|–)\s*\d+)*)")
KEY = re.compile(r"(?<![\w.@])@([A-Za-z0-9_][\w:.#$%&\-+?<>~/]*)")


def paragraphs(docx):
    """Every paragraph of a Word file in reading order, as (style, text)."""
    root = etree.fromstring(zipfile.ZipFile(docx).read("word/document.xml"))
    out = []
    for p in root.iter(w("p")):
        s = p.find(f"{w('pPr')}/{w('pStyle')}")
        out.append((s.get(w("val")) if s is not None else "", "".join(n.text or "" for n in p.iter(w("t")))))
    return out


def all_text(docx):
    """The text of every XML part of a Word file, properties and comments included."""
    z = zipfile.ZipFile(docx)
    parts = []
    for name in z.namelist():
        if name.endswith(".xml") or name.endswith(".rels"):
            x = z.read(name).decode("utf8", "ignore").replace("</w:p>", "\n")
            parts.append(html.unescape(re.sub(r"<[^>]+>", "", x)))
    return "\n".join(parts)


def sections(paras):
    """Paragraph texts grouped by first-level heading, numbering stripped."""
    out, h1 = {}, "Front"
    for st, t in paras:
        if st == "Heading1":
            h1 = re.sub(r"^[\d.]+\s*", "", t.strip())
            continue
        out.setdefault(h1, []).append((st, t))
    return out


def in_citation(text, pos):
    """True if pos lies inside parentheses that hold a year, the form of an author-year citation."""
    open_ = text.rfind("(", 0, pos)
    if open_ < 0 or text.rfind(")", open_, pos) >= 0:
        return False
    close = text.find(")", pos)
    return close >= 0 and re.search(r"\b(?:19|20)\d{2}[a-z]?\b", text[open_:close]) is not None


def numbers_in(group_first, group_rest):
    found = [int(group_first)]
    nums = [int(n) for n in re.findall(r"\d+", group_rest or "")]
    if re.search(r"\bto\b|–", group_rest or "") and nums:
        found = list(range(found[0], nums[-1] + 1))
    else:
        found += nums
    return found


def strip_source(src):
    """A Quarto source without its front matter, code chunks, inline code and comments."""
    src = re.sub(r"\A---\n.*?\n---\n", "", src, flags=re.S)
    src = re.sub(r"^```.*?^```", "", src, flags=re.S | re.M)
    src = re.sub(r"`[^`\n]*`", "", src)
    return re.sub(r"<!--.*?-->", "", src, flags=re.S)


def keys_in(text):
    keys = set()
    for m in KEY.finditer(text):
        k = m.group(1).rstrip(".:#$%&-+?<>~/")
        if not re.match(r"(fig|tbl|eq|sec|lst)-", k):
            keys.add(k)
    return keys


def check_words(files, word_list):
    terms = [t.strip() for t in Path(word_list).read_text(encoding="utf8").splitlines()
             if t.strip() and not t.startswith("#")]
    pats = []
    for t in terms:
        body = re.escape(t).replace(r"\ ", r"\s+")
        flags = 0 if t.isupper() else re.I
        pats.append(re.compile(r"(?<![A-Za-z])" + body + r"s?(?![A-Za-z])", flags))
    bad = []
    for f in files:
        text = all_text(f) if f.suffix == ".docx" else f.read_text(encoding="utf8")
        for p in pats:
            n = len(p.findall(text))
            if n:
                bad.append(f"{f.name}: listed word {terms[pats.index(p)]!r} {n} time(s)")
    return bad, f"{len(terms)} listed words in {len(files)} files"


def check_abstract(sec):
    abstract = " ".join(t for _, t in sec.get("Abstract", []))
    results = " ".join(t for _, t in sec.get("Results", []))
    if not abstract or not results:
        return ["abstract or Results not found"], ""
    nums = sorted(set(NUM.findall(NAMED_YEAR.sub("", abstract))), key=lambda x: float(x.replace(",", "")))
    bad = [f"abstract number {n} is not printed in the Results" for n in nums
           if not re.search(r"(?<![\d.,])" + re.escape(n) + r"(?!\d|[.,]\d)", results)]
    return bad, f"{len(nums)} numbers in the abstract"


def check_glossary(texts):
    bad = []
    for name, text in texts:
        for m in re.finditer(rf"(?i)\b({COUNT_WORDS})\s+(treatments|accounts)\b", text):
            if m.group(1).lower() != CANON[m.group(2).lower()]:
                s = max(text.rfind(".", 0, m.start()), text.rfind("\n", 0, m.start())) + 1
                bad.append(f"{name}: {m.group(0)!r} in {text[s:m.end() + 40].strip()!r}")
    return bad, "treatments counted four, accounts three"


def check_citations(ms_src, ref_src):
    cited = keys_in(strip_source(ms_src.read_text(encoding="utf8")))
    m = re.search(r"^nocite:\s*\|\s*\n((?:[ \t]+.*\n?)+)", ref_src.read_text(encoding="utf8"), re.M)
    listed = keys_in(m.group(1)) if m else set()
    bad = [f"cited in {ms_src.name} but not listed in {ref_src.name}: @{k}" for k in sorted(cited - listed)]
    bad += [f"listed in {ref_src.name} but never cited: @{k}" for k in sorted(listed - cited)]
    return bad, f"{len(cited)} works cited, {len(listed)} listed"


def check_items(paras, or_paras):
    bad, captions, first = [], {"Table": [], "Fig.": []}, {"Table": [], "Fig.": [], "Online Resource": []}
    for st, t in paras:
        c = re.match(r"(Table|Fig\.)\s+(\d+)\s", t)
        if c and "aption" in st:
            captions[c.group(1)].append(int(c.group(2)))
            continue
        for m in MENTION.finditer(t):
            if in_citation(t, m.start()):
                continue
            kind = "Table" if m.group(1).startswith("Table") else "Fig."
            for n in numbers_in(m.group(2), m.group(3)):
                if n not in first[kind]:
                    first[kind].append(n)
        for m in OR_MENTION.finditer(t):
            for n in numbers_in(m.group(1), m.group(2)):
                if n not in first["Online Resource"]:
                    first["Online Resource"].append(n)
    present = {"Online Resource": sorted({int(m.group(1)) for _, t in or_paras
                                          for m in [re.match(r"Online Resource (\d+)\s", t)] if m})}
    for kind in ("Table", "Fig."):
        present[kind] = captions[kind]
        if captions[kind] != sorted(captions[kind]):
            bad.append(f"{kind} captions placed out of order: {captions[kind]}")
    for kind, seq in first.items():
        if seq != list(range(1, len(seq) + 1)):
            bad.append(f"{kind} first cited in the order {seq}")
        for n in seq:
            if n not in present[kind]:
                bad.append(f"{kind} {n} is cited but absent")
        for n in present[kind]:
            if n not in seq:
                bad.append(f"{kind} {n} is present but never cited")
    return bad, "; ".join(f"{k} {v}" for k, v in first.items())


def check_borrowed(paras):
    bad = []
    for _, t in paras:
        for m in BORROWED.finditer(t):
            if not in_citation(t, m.start()):
                bad.append(f"{m.group(0)!r} outside a citation bracket in {t[max(0, m.start() - 60):m.end() + 20]!r}")
    return bad, ""


def check_dates(blinded):
    m = re.match(r"Manuscript-(\d{8})\.docx$", blinded.name)
    if not m:
        return [f"{blinded.name} does not carry a date suffix"], ""
    d = m.group(1)
    want = [blinded.parent / f"{n}-{d}.docx" for n in SET] + [blinded.parent / f"{n}-{d}.qmd" for n in SOURCES]
    return [f"missing {p.name}" for p in want if not p.exists()], f"date {d}"


def check_count(blinded):
    out = subprocess.run([sys.executable, str(HERE / "section-counts.py"), str(blinded)],
                         capture_output=True, text=True).stdout
    m = re.search(r"Journal count.*?([\d,]+)\s*$", out.strip().splitlines()[-1])
    n = int(m.group(1).replace(",", ""))
    return ([f"journal count {n:,} is over {LIMIT:,}"] if n > LIMIT else []), f"journal count {n:,} of {LIMIT:,}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("blinded")
    ap.add_argument("--words", default=str(WORD_LIST))
    a = ap.parse_args()
    blinded = Path(a.blinded).resolve()
    d = re.search(r"-(\d{8})\.docx$", blinded.name)
    d = d.group(1) if d else ""
    file = lambda n, ext: blinded.parent / f"{n}-{d}.{ext}"
    paras = paragraphs(blinded)
    sec = sections(paras)
    present = [file(n, "docx") for n in SET if file(n, "docx").exists()] + \
              [file(n, "qmd") for n in SOURCES if file(n, "qmd").exists()]
    or_paras = paragraphs(file("Online-Resources", "docx")) if file("Online-Resources", "docx").exists() else []
    gloss = [(blinded.name, "\n".join(t for _, t in paras))] + \
            [(file(n, "docx").name, "\n".join(t for _, t in paragraphs(file(n, "docx"))))
             for n in ("Cover-letter", "Online-Resources") if file(n, "docx").exists()]
    checks = [
        ("1 listed words", lambda: check_words(present, a.words)),
        ("2 abstract numbers in Results", lambda: check_abstract(sec)),
        ("3 glossary counts", lambda: check_glossary(gloss)),
        ("4 citations and reference list", lambda: check_citations(file("Manuscript", "qmd"), file("References", "qmd"))),
        ("5 display item order", lambda: check_items(paras, or_paras)),
        ("6 borrowed numbers in brackets", lambda: check_borrowed(paras)),
        ("7 one date suffix", lambda: check_dates(blinded)),
        ("8 word limit", lambda: check_count(blinded)),
    ]
    failed = 0
    for name, run in checks:
        try:
            bad, note = run()
        except Exception as e:  # a check that cannot run counts as failed
            bad, note = [f"check could not run: {type(e).__name__}: {e}"], ""
        print(f"{'FAIL' if bad else 'PASS'}  {name}" + (f"  ({note})" if note else ""))
        for b in bad:
            print(f"      {b}")
        failed += bool(bad)
    print(f"{failed} of {len(checks)} checks failed" if failed else f"all {len(checks)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
