#!/usr/bin/env python3
"""Apply the table geometry a Quarto reference document cannot carry.

Runs over a rendered .docx and sets, on every data table:
  * total width  16.5 cm, written as an explicit dxa so it does not drift
    with the page margins
  * column width shared in proportion to what each column needs to hold its
    widest body cell, or the longest word of its header, on one line, measured
    in the table font. A year column stays narrow and a long label column gets
    the room. Asked by Seamus on 2026-11-01 so that every body row is one line.
  * landscape    a table whose one-line needs exceed 16.5 cm is given its own
    section on a landscape page, the full text width wide, with the sections
    before and after it portrait. Every added section keeps the default footer
    and drops the title page footer and the page number start, so the numbers
    run on through every page. Two wide tables with only blank paragraphs
    between them share one landscape section. Asked by Seamus on 2026-11-01.
    A table too wide even for landscape is scaled down, its body rows let wrap,
    and named in the run's output.
  * row height   0.6 cm on every body row as an exact height, one line of 8 pt,
    and on the header row the height its wrapped words need, as a minimum
  * cell text    left justified, overriding the per-cell alignment knitr
    writes as direct formatting
  * table font   8 pt, belt and braces over the Table style

Caption paragraphs are left alone; their 10 pt comes from the Caption styles in
style-formal.docx. Figures are untouched: Quarto wraps each float in a
single-cell table, and those wrappers are skipped by the nested-table test.

Since 2026-09-02 a per-table specification, table-format.json beside this script, records
the geometry Seamus set by hand in Word: column widths, row heights and their rule, header
bold, vertical centring, per-column justification and font size. A table whose number
matches a specification entry takes that geometry; any other table takes the defaults
below. Regenerate the file from a hand-formatted render with capture-table-format.py.

Idempotent, so re-running on an already-formatted file changes nothing.

Run:  python3 01.manuscript/_tools/format-tables.py <file.docx> [more.docx ...]
Wired into _quarto.yml as a post-render step, so every render comes out formatted.
"""

import sys
import copy
import json
import re
import zipfile
import pathlib
import shutil
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f"{{{W}}}{tag}"

TABLE_WIDTH_CM = 16.5
HEADER_ROW_CM = 1.1
BODY_ROW_CM = 0.6
TABLE_PT = 8
JUSTIFY = "left"

cm_to_twips = lambda cm: int(round(cm * 1440 / 2.54))

# Word's default cell margins, 0.19 cm each side, plus a little slack
CELL_MARGIN_TWIPS = 2 * 108 + 40
LINE_TWIPS = 200          # one line of 8 pt text with its leading
TABLE_FONT = "/System/Library/Fonts/Helvetica.ttc"

try:
    from PIL import ImageFont
    _FONT = ImageFont.truetype(TABLE_FONT, 100)
except Exception:
    _FONT = None


def text_twips(text, pt):
    """Width of text set in the table font at pt points, in twips."""
    if _FONT is not None:
        return int(round(_FONT.getlength(text) / 100 * pt * 20))
    return int(round(len(text) * 0.55 * pt * 20))


def cell_lines(tc):
    return ["".join(t.text or "" for t in p.iter(w("t"))) for p in tc.findall(w("p"))]


def is_footnote(tr):
    """A last row whose first cell begins with a footnote marker and whose other cells are empty."""
    tcs = tr.findall(w("tc"))
    first = "".join(x.text or "" for x in tcs[0].iter(w("t"))).strip()
    rest = "".join("".join(x.text or "" for x in tc.iter(w("t"))).strip() for tc in tcs[1:])
    return len(tcs) > 1 and first[:1] in "#†‡" and not rest


def ensure_grid(tbl):
    """The column grid, built from the first row when flextable wrote none. Word adds
    the grid on save, so a file saved in Word has one and a fresh render does not."""
    grid = tbl.find(w("tblGrid"))
    if grid is None:
        ncols = len(tbl.find(w("tr")).findall(w("tc")))
        grid = etree.Element(w("tblGrid"))
        for _ in range(ncols):
            etree.SubElement(grid, w("gridCol")).set(w("w"), str(cm_to_twips(TABLE_WIDTH_CM) // ncols))
        tblPr = tbl.find(w("tblPr"))
        tbl.insert(tbl.index(tblPr) + 1 if tblPr is not None else 0, grid)
    return grid


def content_needs(tbl, pt):
    """Per column, the twips needed to hold the widest body cell, or the longest word
    of the header, on one line. The footnote row is merged later and may wrap."""
    rows = tbl.findall(w("tr"))
    ncols = len(ensure_grid(tbl).findall(w("gridCol")))
    need = [0] * ncols
    for i, tr in enumerate(rows):
        if i == len(rows) - 1 and i > 0 and is_footnote(tr):
            continue
        for k, tc in enumerate(tr.findall(w("tc"))[:ncols]):
            for line in cell_lines(tc):
                for piece in (line.split() if i == 0 else [line]):
                    need[k] = max(need[k], text_twips(piece, pt))
    return [n + CELL_MARGIN_TWIPS for n in need]


def header_lines(tbl, widths, pt):
    """Lines the tallest header cell needs when its words wrap in the given widths."""
    most = 1
    for tc, width in zip(tbl.findall(w("tr"))[0].findall(w("tc")), widths):
        room = width - CELL_MARGIN_TWIPS
        for line in cell_lines(tc):
            lines, cur = 1, 0
            for word in line.split():
                wd, sp = text_twips(word, pt), text_twips(" ", pt)
                if cur and cur + sp + wd > room:
                    lines, cur = lines + 1, wd
                else:
                    cur = cur + sp + wd if cur else wd
            most = max(most, lines)
    return most

SPEC_PATH = pathlib.Path(__file__).with_name("table-format.json")
SPEC = json.loads(SPEC_PATH.read_text()) if SPEC_PATH.exists() else []


def spec_for(caption, ncols):
    """The hand-set geometry for a table, matched on its number, or None.

    Matched by caption text until 2026-09-02, when a caption edit dropped every table to
    the defaults and cost Seamus his hand layout. The number is the stable key. When the
    column count has changed since the capture, the first column keeps its width and its
    cell style and the remaining columns share the rest, so an added or removed column
    degrades the layout gracefully instead of discarding it."""
    m = re.match(r"Table[\s\u00a0](S?\d+)", caption or "")
    num = m.group(1) if m else None
    s = next((s for s in SPEC if str(s.get("table")) == num), None)
    if s is None:
        key = re.sub(r"^Table[\s\u00a0]S?\d+[:.]?\s*", "", caption or "")[:60]
        s = next((s for s in SPEC if key and s["caption_key"] and key[:40] == s["caption_key"][:40]), None)
    if s is None or ncols < 2:
        return s
    if s["cols"] != ncols:
        s = dict(s); g = list(s["grid"]); hc, bc = s["header_cells"], s["body_cells"]
        rest = s["tblW"] - g[0]; each = [rest // (ncols - 1)] * (ncols - 1); each[-1] += rest - sum(each)
        s.update(grid=[g[0]] + each, cols=ncols,
                 header_cells=[hc[0]] + [hc[1] if len(hc) > 1 else hc[0]] * (ncols - 1),
                 body_cells=[bc[0]] + [bc[1] if len(bc) > 1 else bc[0]] * (ncols - 1))
    return s


def sub(parent, tag, index=0):
    """Get or create a child element, inserted at index."""
    el = parent.find(w(tag))
    if el is None:
        el = etree.SubElement(parent, w(tag))
        parent.remove(el)
        parent.insert(index, el)
    return el


def sub_rpr(pPr):
    """The paragraph-mark run properties, which must sit last inside w:pPr."""
    rPr = pPr.find(w("rPr"))
    if rPr is None:
        rPr = etree.SubElement(pPr, w("rPr"))
    return rPr


def props(el, tag):
    """Get or create the properties element (tblPr/trPr/pPr/rPr) first in order."""
    pr = el.find(w(tag))
    if pr is None:
        pr = etree.Element(w(tag))
        el.insert(0, pr)
    return pr


def format_table(tbl, spec=None, width=None):
    """Set one table's geometry. width is the table width in twips, the portrait default
    or the landscape text width when the caller has given the table its own page."""
    target = spec["tblW"] if spec else (width or cm_to_twips(TABLE_WIDTH_CM))
    fits = True
    # width, as an exact dxa rather than a percentage
    tblPr = props(tbl, "tblPr")
    for old in tblPr.findall(w("tblW")):
        tblPr.remove(old)
    tblW = etree.SubElement(tblPr, w("tblW"))
    tblW.set(w("w"), str(target))
    tblW.set(w("type"), "dxa")
    # fixed layout so Word honours the widths instead of autofitting
    for old in tblPr.findall(w("tblLayout")):
        tblPr.remove(old)
    etree.SubElement(tblPr, w("tblLayout")).set(w("type"), "fixed")

    # share the total width in proportion to what each column's content needs, or take
    # the hand-set widths from the specification when this table has one
    grid = ensure_grid(tbl)
    new = None
    if grid is not None:
        cols = grid.findall(w("gridCol"))
        if spec and len(spec["grid"]) == len(cols):
            old = list(spec["grid"])
        else:
            old = content_needs(tbl, TABLE_PT)
            fits = sum(old) <= target
            if not fits:
                print(f"    a table needs {sum(old) * 2.54 / 1440:.1f} cm and has {target * 2.54 / 1440:.1f} cm, so its body rows may wrap")
        tot = sum(old)
        if tot > 0:
            new = [int(round(v * target / tot)) for v in old]
            new[-1] += target - sum(new)          # absorb rounding
            for c, v in zip(cols, new):
                c.set(w("w"), str(v))
            # cell widths follow the grid
            for tr in tbl.findall(w("tr")):
                for tc, v in zip(tr.findall(w("tc")), new):
                    tcPr = props(tc, "tcPr")
                    for old in tcPr.findall(w("tcW")):
                        tcPr.remove(old)
                    tcW = etree.Element(w("tcW")); tcW.set(w("w"), str(v)); tcW.set(w("type"), "dxa")
                    tcPr.insert(0, tcW)

    rows = tbl.findall(w("tr"))
    for i, tr in enumerate(rows):
        trPr = props(tr, "trPr")
        for old in trPr.findall(w("trHeight")):
            trPr.remove(old)
        h = etree.SubElement(trPr, w("trHeight"))
        rh = (spec or {}).get("header_height" if i == 0 else "body_height")
        if rh:
            h.set(w("val"), str(rh["val"]))
            h.set(w("hRule"), rh["hRule"])
        elif i == 0:
            lines = header_lines(tbl, new, TABLE_PT) if new else 3
            h.set(w("val"), str(lines * LINE_TWIPS + 80))
            h.set(w("hRule"), "atLeast")
        else:
            h.set(w("val"), str(cm_to_twips(BODY_ROW_CM)))
            h.set(w("hRule"), "exact" if fits else "atLeast")

        cellspec = (spec or {}).get("header_cells" if i == 0 else "body_cells") or []
        for k, tc in enumerate(tr.findall(w("tc"))):
            cs = cellspec[k] if k < len(cellspec) else None
            if cs and cs.get("vAlign"):
                tcPr = props(tc, "tcPr")
                for old in tcPr.findall(w("vAlign")):
                    tcPr.remove(old)
                etree.SubElement(tcPr, w("vAlign")).set(w("val"), cs["vAlign"])
            for p in tc.findall(w("p")):
                pPr = props(p, "pPr")
                for old in pPr.findall(w("jc")):
                    pPr.remove(old)
                etree.SubElement(pPr, w("jc")).set(w("val"), (cs or {}).get("jc") or JUSTIFY)
                if cs and cs.get("bold"):
                    for r in p.findall(w("r")):
                        rPr = props(r, "rPr")
                        if rPr.find(w("b")) is None:
                            rPr.insert(0, etree.Element(w("b")))
                # the paragraph mark carries its own rPr; leaving it at the
                # old size is harmless under an exact row height but untidy
                for holder in [pPr] + p.findall(w("r")):
                    rPr = props(holder, "rPr") if holder is not pPr else sub_rpr(pPr)
                    for tag in ("sz", "szCs"):
                        for old in rPr.findall(w(tag)):
                            rPr.remove(old)
                        etree.SubElement(rPr, w(tag)).set(w("val"), str((cs or {}).get("sz") or TABLE_PT * 2))


    # A last row whose first cell begins with a footnote marker and whose other cells are
    # empty is a table footnote, the form Seamus set by hand on 2026-09-02; it is merged
    # across the table and allowed to wrap.
    if len(rows) > 1:
        tcs = rows[-1].findall(w("tc"))
        first = "".join(x.text or "" for x in tcs[0].iter(w("t"))).strip()
        rest = "".join("".join(x.text or "" for x in tc.iter(w("t"))).strip() for tc in tcs[1:])
        if len(tcs) > 1 and first[:1] in "#\u2020\u2021" and not rest:
            tcPr = props(tcs[0], "tcPr")
            for old in tcPr.findall(w("gridSpan")):
                tcPr.remove(old)
            gs = etree.Element(w("gridSpan")); gs.set(w("val"), str(len(tcs)))
            tcPr.insert(1 if tcPr.find(w("tcW")) is not None else 0, gs)
            tcW = tcPr.find(w("tcW"))
            if tcW is not None:
                tcW.set(w("w"), str(sum(int(c.get(w("w"))) for c in tbl.find(w("tblGrid")).findall(w("gridCol")))))
            for tc in tcs[1:]:
                rows[-1].remove(tc)
            trPr = props(rows[-1], "trPr")
            for old in trPr.findall(w("trHeight")):
                trPr.remove(old)
            hh = etree.SubElement(trPr, w("trHeight")); hh.set(w("val"), "340"); hh.set(w("hRule"), "atLeast")


def section_props(base, landscape, first):
    """A copy of the document's section properties for one more section. Only the first
    section in the document keeps the title page footer and the page number start, so
    the numbering runs on through every later section and every page carries its number."""
    sp = copy.deepcopy(base)
    for tag in ("rsidR", "rsidSect"):
        sp.attrib.pop(w(tag), None)
    if not first:
        for el in sp.findall(w("titlePg")) + sp.findall(w("pgNumType")):
            sp.remove(el)
        for ref in sp.findall(w("footerReference")) + sp.findall(w("headerReference")):
            if ref.get(w("type")) == "first":
                sp.remove(ref)
    pgSz = sp.find(w("pgSz"))
    if landscape:
        wv, hv = pgSz.get(w("w")), pgSz.get(w("h"))
        if int(wv) < int(hv):
            pgSz.set(w("w"), hv)
            pgSz.set(w("h"), wv)
        pgSz.set(w("orient"), "landscape")
    else:
        pgSz.attrib.pop(w("orient"), None)
    return sp


def section_break(sectpr):
    """An empty paragraph carrying the properties of the section it ends."""
    p = etree.Element(w("p"))
    etree.SubElement(p, w("pPr")).append(sectpr)
    return p


def is_blank(el):
    return el.tag == w("p") and not "".join(t.text or "" for t in el.iter(w("t"))).strip() \
        and el.find(f".//{w('sectPr')}") is None and el.find(f".//{w('drawing')}") is None


def own_landscape_pages(body, base, wrappers):
    """Give each wide table its own landscape section, portrait on both sides. Two wide
    tables with nothing but blank paragraphs between them share one landscape section,
    so no empty portrait page is left between them."""
    first = True
    last_break = None
    for outer in wrappers:
        i = body.index(outer)
        between = body[body.index(last_break) + 1:i] if last_break is not None else None
        if between is not None and all(is_blank(el) for el in between):
            body.remove(last_break)
        else:
            body.insert(i, section_break(section_props(base, False, first)))
            first = False
        last_break = section_break(section_props(base, True, False))
        body.insert(body.index(outer) + 1, last_break)
    if wrappers:
        for el in base.findall(w("titlePg")) + base.findall(w("pgNumType")):
            base.remove(el)
        for ref in base.findall(w("footerReference")) + base.findall(w("headerReference")):
            if ref.get(w("type")) == "first":
                base.remove(ref)


def process(path):
    path = pathlib.Path(path)
    if not path.exists():
        print(f"  skipped, not found: {path}")
        return
    zin = zipfile.ZipFile(path)
    parts = {n: zin.read(n) for n in zin.namelist()}
    zin.close()

    root = etree.fromstring(parts["word/document.xml"])
    body = root.find(w("body"))
    base = body.find(w("sectPr"))
    pgSz, pgMar = base.find(w("pgSz")), base.find(w("pgMar"))
    portrait_width = cm_to_twips(TABLE_WIDTH_CM)
    landscape_width = max(int(pgSz.get(w("w"))), int(pgSz.get(w("h")))) \
        - int(pgMar.get(w("left"))) - int(pgMar.get(w("right")))
    wide = []
    # Quarto wraps every float, figures included, in a single-cell table. A real
    # data table is the innermost one, holds no image, and has more than one
    # cell. Without the last two tests a figure wrapper would be given an exact
    # 0.6 cm row height, which crops the image, and 8 pt, which shrinks its caption.
    n = 0
    for tbl in list(root.iter(w("tbl"))):
        if tbl.find(f".//{w('tbl')}") is not None:
            continue
        if tbl.find(f".//{w('drawing')}") is not None or tbl.find(f".//{w('pict')}") is not None:
            continue
        if len(tbl.findall(f".//{w('tc')}")) < 2:
            continue
        outer = next(tbl.iterancestors(w("tbl")), None)
        caption = ""
        if outer is not None:
            for para in outer.iter(w("p")):
                if tbl in para.iterancestors():
                    continue
                t = "".join(x.text or "" for x in para.iter(w("t"))).strip()
                if re.match(r"Table[\s\u00a0]\d+", t):
                    caption = t
                    break
        spec = spec_for(caption, len(ensure_grid(tbl).findall(w("gridCol"))))
        # a table whose one-line needs exceed the portrait width goes on its own landscape page
        landscape = (spec is None and outer is not None and outer.getparent() is body
                     and sum(content_needs(tbl, TABLE_PT)) > portrait_width)
        format_table(tbl, spec, landscape_width if landscape else portrait_width)
        if landscape:
            wide.append(outer)
            print(f"    {caption[:40] or 'a table'}: landscape page, {landscape_width * 2.54 / 1440:.1f} cm wide")
        n += 1
    own_landscape_pages(body, base, wide)
    parts["word/document.xml"] = etree.tostring(root, xml_declaration=True,
                                                encoding="UTF-8", standalone=True)

    tmp = path.with_suffix(".docx.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in parts.items():
            zout.writestr(name, data)
    shutil.move(tmp, path)
    print(f"  {path.name}: {n} tables set to {TABLE_WIDTH_CM} cm, columns shared by content, "
          f"{BODY_ROW_CM} cm body rows, {TABLE_PT} pt, {JUSTIFY}-justified")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        # Quarto sets this to the newline-separated list of files it just wrote,
        # which is what the post-render hook in _quarto.yml relies on.
        import os
        args = [f for f in os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").split("\n")
                if f.strip().endswith(".docx")]
    if not args:
        print("no .docx to format (no argument, no QUARTO_PROJECT_OUTPUT_FILES)")
        sys.exit(0)
    for a in args:
        process(a.strip())
