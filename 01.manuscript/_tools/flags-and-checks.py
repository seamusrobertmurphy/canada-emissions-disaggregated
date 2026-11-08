import sys, re, zipfile, shutil, os
src = sys.argv[1]; tmp = sys.argv[2]
zin = zipfile.ZipFile(src)
st = zin.read('word/settings.xml').decode('utf8')
added = []
for tag in ('removePersonalInformation', 'removeDateAndTime'):
    if '<w:%s' % tag not in st:
        added.append(tag)
if added:
    ins = ''.join('<w:%s/>' % t for t in ('removePersonalInformation', 'removeDateAndTime') if t in added)
    m = None
    for anchor in ('w:zoom', 'w:view', 'w:writeProtection'):
        m = re.search(r'<%s\b[^>]*/>|<%s\b[^>]*>.*?</%s>' % (anchor, anchor, anchor), st, re.S)
        if m: break
    if m:
        st = st[:m.end()] + ins + st[m.end():]
    else:
        m = re.search(r'<w:settings\b[^>]*>', st)
        st = st[:m.end()] + ins + st[m.end():]
    zout = zipfile.ZipFile(tmp, 'w')
    for i in zin.infolist():
        data = st.encode('utf8') if i.filename == 'word/settings.xml' else zin.read(i.filename)
        zout.writestr(i, data)
    zout.close(); zin.close()
    shutil.copyfile(tmp, src)
else:
    zin.close()
print('flags added:', added or 'none needed')
z = zipfile.ZipFile(src)
st = z.read('word/settings.xml').decode('utf8')
print('flags present:', all('<w:%s' % t in st for t in ('removePersonalInformation', 'removeDateAndTime')))
core = z.read('docProps/core.xml').decode('utf8')
for f in ('dc:creator', 'cp:lastModifiedBy'):
    m = re.search(r'<%s[^>]*>(.*?)</%s>' % (f, f), core)
    print(f, 'empty' if not m or not m.group(1).strip() else 'HAS: ' + m.group(1))
doc = z.read('word/document.xml').decode('utf8')
print('sections', doc.count('<w:sectPr'), 'with line numbers', doc.count('<w:lnNumType'))
txt = ' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', doc))
paras = [''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)) for p in re.findall(r'<w:p[ >].*?</w:p>', doc, re.S)]
paras = [p for p in paras if p.strip()]
print('opens with:', paras[0][:110])
blob = ' '.join(z.read(n).decode('utf8', 'ignore') for n in z.namelist() if n.endswith('.xml'))
for s in ('Murphy', 'Seamus', 'seamusrobertmurphy', 'TUV', 'Comox', 'Vancouver', 'Independent researcher', 'canada-emissions-disaggregated', 'ipcc-uncertainties'):
    n = blob.count(s)
    if n: print('IDENTIFYING:', s, n, [p[:90] for p in paras if s in p][:2])
borrowed = re.findall(r'(?:Table|Tables|Fig\.|Figure|Box)\s+[0-9]+[.\-–][0-9]+', txt)
print('borrowed table/figure numbers:', len(borrowed), borrowed[:5])
caps = [p for p in paras if re.match(r'(Table [0-9]+|Fig\. [0-9]+)\s', p) and len(p) > 25]
print('captions in order:'); [print('   ', c[:80]) for c in caps]
first = []
for m in re.finditer(r'\b(Table|Fig\.)\s+([0-9]+)\b(?![.\-–][0-9])', txt):
    k = m.group(1) + ' ' + m.group(2)
    if k not in first: first.append(k)
print('first mention order:', first)
for bad in ('?@', '???', '(missing', 'Table ?', 'Fig. ?', '@tbl', '@fig', '@sec'):
    if bad in txt: print('BROKEN:', bad, txt.count(bad))
refs = [p for p in paras if re.search(r'\(\d{4}[a-z]?\)\.', p[:200]) or re.search(r'\(n\.d\.\)', p[:200])]
print('reference entries (approx):', len(refs))
print('TREES versions in text:', sorted(set(re.findall(r'Version [0-9.]+', txt))))
