"""Proof that every check of audit.py can fail: each fault is planted in a fresh copy of the set,
and the check must then fail and name the planted fault.

Usage, from the repository root:
    python3 01.manuscript/_tools/audit-selftest.py 01.manuscript/Manuscript-YYYYMMDD.docx SCRATCH_DIR

The copies are made under SCRATCH_DIR, and the set itself is never written. The listed word of
check 1 is read from the same list audit.py reads, so this script names none of those words.
"""
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SET = ["Manuscript", "Title-page", "Cover-letter", "References", "Online-Resources"]
SOURCES = ["Manuscript", "Cover-letter", "References", "Online-Resources"]

blinded, scratch = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
date = re.search(r"-(\d{8})\.docx$", blinded.name).group(1)
word_list = next(iter(sorted(ROOT.glob(".*/audit-words.txt"))))
word = next(t.strip() for t in word_list.read_text(encoding="utf8").splitlines()
            if t.strip() and not t.startswith("#"))


def fresh(name):
    d = scratch / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for n in SET:
        shutil.copy2(blinded.parent / f"{n}-{date}.docx", d)
    for n in SOURCES:
        shutil.copy2(blinded.parent / f"{n}-{date}.qmd", d)
    return d


def docx_replace(path, old, new):
    """Replace the first occurrence of old inside one text run of a Word file."""
    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                x = data.decode("utf8")
                m = re.search(r"(<w:t(?: [^>]*)?>)([^<]*?)" + re.escape(old), x)
                assert m, f"{old!r} not found inside one run of {path.name}"
                x = x[:m.end() - len(old)] + new + x[m.end():]
                data = x.encode("utf8")
            zout.writestr(item, data)
    tmp.replace(path)


def text_replace(path, old, new):
    s = path.read_text(encoding="utf8")
    assert old in s, f"{old!r} not in {path.name}"
    path.write_text(s.replace(old, new, 1), encoding="utf8")


def audit(d):
    out = subprocess.run([sys.executable, str(HERE / "audit.py"), str(d / f"Manuscript-{date}.docx")],
                         capture_output=True, text=True).stdout
    blocks, cur = {}, None
    for line in out.splitlines():
        m = re.match(r"(PASS|FAIL)\s+(\d) ", line)
        if m:
            cur = m.group(2)
            blocks[cur] = [m.group(1), ""]
        elif cur and line.startswith("      "):
            blocks[cur][1] += line + "\n"
    return blocks


def plant_1(d):
    docx_replace(d / f"Title-page-{date}.docx", "Net emissions", f"Net emissions {word}")
    (d / f"Online-Resources-{date}.qmd").write_text(
        (d / f"Online-Resources-{date}.qmd").read_text(encoding="utf8") + f"\n{word}\n", encoding="utf8")
    return [f"Title-page-{date}.docx", f"Online-Resources-{date}.qmd"]


def plant_2(d):
    docx_replace(d / f"Manuscript-{date}.docx", "85.6", "85.9")
    return ["abstract number 85.9"]


def plant_3(d):
    docx_replace(d / f"Manuscript-{date}.docx", "This study compared four treatments", "This study compared three treatments")
    return ["three treatments"]


def plant_4(d):
    (d / f"Manuscript-{date}.qmd").write_text(
        (d / f"Manuscript-{date}.qmd").read_text(encoding="utf8") + "\n\nPlanted sentence [@plantedkey2099].\n",
        encoding="utf8")
    text_replace(d / f"References-{date}.qmd", "@art2026trees3, ", "@art2026trees3, @plantedlisted2099, ")
    return ["not listed in References-" + date + ".qmd: @plantedkey2099", "never cited: @plantedlisted2099"]


def plant_5(d):
    docx_replace(d / f"Manuscript-{date}.docx", "This study compared four treatments", "This study (Table 2) compared four treatments")
    docx_replace(d / f"Manuscript-{date}.docx", "Online Resource 3", "Online Resource 4")
    return ["Table first cited in the order [2, 1]", "Online Resource 4 is cited but absent"]


def plant_6(d):
    docx_replace(d / f"Manuscript-{date}.docx", "The background level method", "The background level method of Table 2.4")
    return ["'Table 2.4' outside a citation bracket"]


def plant_7(d):
    (d / f"References-{date}.docx").unlink()
    return [f"missing References-{date}.docx"]


def plant_8(d):
    docx_replace(d / f"Manuscript-{date}.docx", "This study therefore compared", "word " * 700 + "This study therefore compared")
    return ["is over 10,000"]


base = audit(fresh("clean"))
print("clean copy:", ", ".join(f"{k} {v[0]}" for k, v in sorted(base.items())))
proved = 0
for n, plant in enumerate([plant_1, plant_2, plant_3, plant_4, plant_5, plant_6, plant_7, plant_8], start=1):
    d = fresh(f"plant-{n}")
    markers = plant(d)
    got = audit(d).get(str(n), ["MISSING", ""])
    named = all(mk in got[1] for mk in markers)
    flipped = base[str(n)][0] == "PASS"
    ok = got[0] == "FAIL" and named
    proved += ok
    print(f"check {n}: {'proved' if ok else 'NOT PROVED'}, planted fault {'named' if named else 'NOT NAMED'}, "
          f"{'passed clean and failed planted' if flipped and ok else 'already failing on the clean copy, planted fault named' if ok else ''}")
    if not ok:
        print(got[1])
print(f"{proved} of 8 checks proved able to fail")
sys.exit(0 if proved == 8 else 1)
