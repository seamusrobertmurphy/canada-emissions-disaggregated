"""Empty the creator and last-modified-by fields of a docx's core properties, leaving everything else as it is."""
import re, sys, zipfile, shutil
for src in sys.argv[1:]:
    zin = zipfile.ZipFile(src)
    core = zin.read("docProps/core.xml").decode("utf8")
    new = re.sub(r"<dc:creator>[^<]*</dc:creator>", "<dc:creator></dc:creator>", core)
    new = re.sub(r"<cp:lastModifiedBy>[^<]*</cp:lastModifiedBy>", "<cp:lastModifiedBy></cp:lastModifiedBy>", new)
    if new != core:
        tmp = src + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for i in zin.infolist():
                zout.writestr(i, new.encode("utf8") if i.filename == "docProps/core.xml" else zin.read(i.filename))
        zin.close(); shutil.move(tmp, src)
    else:
        zin.close()
    print(src.split("/")[-1], "core properties", "cleared" if new != core else "already clear")
