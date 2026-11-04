#!/usr/bin/env python3
"""Rebuild the repository README from the rendered manuscript.

Seamus ruled on 4 November 2026 that the README hold only the manuscript's title and
subtitle, its abstract and its figures and tables, with no comments and no guidance, so
this script writes the whole file from the current render and nothing is kept by hand.
Wired into _quarto.yml as a post-render step, and runnable by hand:

    python3 01.manuscript/_tools/build-readme.py

Two things this script exists to handle:

1. GitHub does not render the Pandoc grid tables Quarto produces, so a paste of
   the render would print a wall of plus signs. Tables are emitted as raw HTML
   tables that fill the page column, see html_table(), with column alignment
   preserved.
2. Figures are decoded from the HTML render's embedded base64, which keeps them
   in document order and avoids picking up the Word reference template's own
   images.
"""
import base64
import html
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "01.manuscript" / "Manuscript.html"
QMD = ROOT / "01.manuscript" / "Manuscript.qmd"
FIGDIR = ROOT / "03.outputs" / "PNG"
OUT = ROOT / "README.md"

MIN_FIG_WIDTH = 1000  # anything narrower is interface furniture, not a figure


def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def front_matter() -> dict:
    """Pull title, subtitle and abstract from the qmd front matter.

    Read from the source rather than hardcoded, so editing the manuscript's
    title or framing cannot leave the README asserting the old one.
    """
    body = QMD.read_text(encoding="utf8").split("---", 2)[1]
    out, key, buf = {}, None, []
    for line in body.splitlines():
        m = re.match(r"^(title|subtitle|abstract):\s*(.*)$", line)
        if m:
            if key:
                out[key] = " ".join(buf).strip()
            key, buf = m.group(1), []
            rest = m.group(2).strip()
            if rest and rest != ">":
                buf.append(rest.strip('"').strip("'"))
            continue
        if key:
            if line and not line[0].isspace():
                out[key] = " ".join(buf).strip()
                key, buf = None, []
                continue
            buf.append(line.strip())
    if key:
        out[key] = " ".join(buf).strip()
    return {k: re.sub(r"\s+", " ", v).strip() for k, v in out.items()}


def to_pipe_table(chunk: str) -> tuple[str, str] | None:
    """Return the pipe table and its footnote, which is empty when there is none.

    A last row whose first cell begins with the # marker and whose other cells are
    empty is a table footnote, the form set by hand in the Word file on 2026-09-02 and
    merged across the table by format-tables.py. A pipe table has no merged cells, so
    left in place the note sits in the first column beside a row of empty cells; it is
    lifted out and printed under the table instead.
    """
    m = re.search(r"<table[^>]*>(.*?)</table>", chunk, re.S)
    if not m:
        return None
    tb = m.group(1)
    head = re.search(r"<thead>(.*?)</thead>", tb, re.S)
    body = re.search(r"<tbody>(.*?)</tbody>", tb, re.S)
    if not head or not body:
        return None
    heads = [clean(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", head.group(1), re.S)]
    aligns = []
    for attrs in re.findall(r"<th([^>]*)>", head.group(1)):
        if "text-align: right" in attrs:
            aligns.append("---:")
        elif "text-align: center" in attrs:
            aligns.append(":---:")
        else:
            aligns.append(":---")
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body.group(1), re.S):
        cells = [clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        if cells:
            rows.append(cells)
    if not heads or not rows:
        return None
    note = ""
    last = rows[-1]
    if last[0].startswith("#") and not any(c.strip() for c in last[1:]):
        note = last[0].lstrip("#").strip()
        rows = rows[:-1]
    while len(aligns) < len(heads):
        aligns.append(":---")
    return html_table(heads, aligns[: len(heads)], rows), note


# Every README table fills the page column and lets the browser size the cells. A pipe
# table cannot do that: GitHub's stylesheet sets `width: max-content` on tables, so a
# pipe table sits at the width of its text and `<table width="100%">` is overruled. The
# one mechanism that works, measured against GitHub's live stylesheet by the
# writing-readme skill, is an oversized pixel hint on every header cell,
# `<th width="2000">`: it pushes the intrinsic width past any viewport and GitHub's
# `max-width: 100%` clamps the table back to exactly the column, while the browser's
# automatic layout still shares that width among the columns by their content. The
# cost is raw HTML in the README instead of a pipe table.
TH_WIDTH = "2000"
ALIGN = {":---": "left", "---:": "right", ":---:": "center"}


def html_table(heads: list[str], aligns: list[str], rows: list[list[str]]) -> str:
    """Emit a full-width GitHub table from parsed header, alignment and body cells."""
    esc = lambda s: html.escape(s, quote=False)
    al = [ALIGN.get(a, "left") for a in aligns] + ["left"] * len(heads)
    out = ["<table>", "<thead>", "<tr>"]
    out += [f'<th width="{TH_WIDTH}" align="{al[i]}">{esc(h)}</th>' for i, h in enumerate(heads)]
    out += ["</tr>", "</thead>", "<tbody>"]
    for r in rows:
        r = (r + [""] * len(heads))[: len(heads)]
        out.append("<tr>" + "".join(f'<td align="{al[i]}">{esc(c)}</td>' for i, c in enumerate(r)) + "</tr>")
    out += ["</tbody>", "</table>"]
    return "\n".join(out)


def save_figure(chunk: str, slug: str) -> Path | None:
    for b64 in re.findall(r'<img[^>]*src="data:image/png;base64,([^"]+)"', chunk):
        data = base64.b64decode(b64)
        width = struct.unpack(">I", data[16:20])[0]
        if width < MIN_FIG_WIDTH:
            continue
        FIGDIR.mkdir(parents=True, exist_ok=True)
        path = FIGDIR / f"{slug}.png"
        path.write_bytes(data)
        return path.relative_to(ROOT)
    return None


def abstract_from_render(doc: str) -> str:
    """Read the Abstract section out of the HTML render.

    The manuscript carries its abstract as a `# Abstract` section rather than as YAML,
    because the journal wants it in the body, and because every figure in it is an
    inline expression that has to be evaluated before it can be read.
    """
    m = re.search(r'<h1[^>]*>(?:<span[^>]*>[^<]*</span>)?\s*Abstract\s*</h1>(.*?)<h1', doc, re.S)
    if not m:
        return ""
    paras = re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), re.S)
    return " ".join(clean(p) for p in paras).strip()


def main() -> None:
    if not HTML.exists():
        print(f"no {HTML.name} yet, README left unchanged")
        return
    doc = HTML.read_text(encoding="utf8")

    # Every float, in the order it appears in the document.
    floats = [(m.start(), m.group(1)) for m in
              re.finditer(r'<div id="((?:tbl|fig)-[^"]+)"', doc)]
    bounds = [p for p, _ in floats] + [len(doc)]

    # Numbered section headings, so each float can be placed in its section.
    heads = [(m.start(), clean(m.group(2))) for m in re.finditer(r"<h([12])[^>]*data-number[^>]*>(.*?)</h\1>", doc, re.S)]

    def section_of(pos: int) -> str:
        last = ""
        for p, h in heads:
            if p >= pos:
                break
            last = h
        return last

    fm = front_matter()
    n_fig = n_tbl = 0
    overview, body = [], []
    for i, (start, slug) in enumerate(floats):
        chunk = doc[start:bounds[i + 1]]
        cap = ""
        for c in re.findall(r"<figcaption[^>]*>(.*?)</figcaption>", chunk, re.S):
            c = clean(c)
            if re.match(r"^(Table|Fig\.|Figure)\s\d+", c):
                cap = c
                break
        # "Fig. 1 text" in the journal's form, or "Figure 1: text" before it was adopted
        m = re.match(r"^((?:Table|Fig\.|Figure)\s\d+):?\s*(.*)$", cap, re.S)
        label, text = (m.group(1).strip(), m.group(2).strip()) if m else ("", cap)
        first = re.split(r"(?<=[.?!])\s+(?=[A-Z])", text)[0].rstrip(".")

        if slug.startswith("fig-"):
            path = save_figure(chunk, slug)
            if not path:
                continue
            n_fig += 1
            body += [f"![{label}]({path.as_posix()})", "", f"*{label} {text}*", ""]
        else:
            got = to_pipe_table(chunk)
            if not got:
                continue
            table, note = got
            n_tbl += 1
            body += [f"*{label} {text}*", "", table, ""]
            if note:
                body += [f"*{note}*", ""]

    parts = [
        f"# {fm.get('title', 'Manuscript')}",
        "",
        f"*{fm['subtitle']}*" if fm.get("subtitle") else "",
        "",
        "## Abstract",
        "",
        fm.get("abstract") or abstract_from_render(doc),
        "",
        *body,
    ]
    OUT.write_text("\n".join(parts).rstrip("\n") + "\n", encoding="utf8")
    print(f"wrote {OUT.relative_to(ROOT)}: {n_fig} figures and {n_tbl} tables, in document order")


if __name__ == "__main__":
    main()
