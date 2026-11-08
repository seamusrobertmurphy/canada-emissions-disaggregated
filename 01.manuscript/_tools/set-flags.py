import sys, re, zipfile, shutil, pathlib
for src in sys.argv[1:]:
    zin = zipfile.ZipFile(src)
    st = zin.read('word/settings.xml').decode('utf8')
    add = [t for t in ('removePersonalInformation', 'removeDateAndTime') if '<w:%s' % t not in st]
    if add:
        ins = ''.join('<w:%s/>' % t for t in add)
        m = None
        for a in ('w:zoom', 'w:view', 'w:writeProtection'):
            m = re.search(r'<%s\b[^>]*/>|<%s\b[^>]*>.*?</%s>' % (a, a, a), st, re.S)
            if m: break
        if not m: m = re.search(r'<w:settings\b[^>]*>', st)
        st = st[:m.end()] + ins + st[m.end():]
        tmp = src + '.tmp'
        zout = zipfile.ZipFile(tmp, 'w')
        for i in zin.infolist():
            zout.writestr(i, st.encode('utf8') if i.filename == 'word/settings.xml' else zin.read(i.filename))
        zout.close(); zin.close(); shutil.move(tmp, src)
    else:
        zin.close()
    z = zipfile.ZipFile(src)
    core = z.read('docProps/core.xml').decode('utf8')
    c = re.search(r'<dc:creator>([^<]*)</dc:creator>', core); l = re.search(r'<cp:lastModifiedBy>([^<]*)</cp:lastModifiedBy>', core)
    print(pathlib.Path(src).name, '| flags added', add or 'none', '| creator', repr(c.group(1)) if c else 'absent', '| lastModifiedBy', repr(l.group(1)) if l else 'absent', '| zip ok', z.testzip() is None)
