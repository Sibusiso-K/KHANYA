import re, sys
BS = chr(92)
path = sys.argv[1]
s = open(path, encoding='utf-8').read()
body = re.sub(r'(?<!\\)%.*', '', s)

stack, ok = [], True
for m in re.finditer(r'\\(begin|end)\{([^}]+)\}', body):
    kind, env = m.groups()
    if kind == 'begin':
        stack.append(env)
    else:
        if not stack or stack[-1] != env:
            print('MISMATCH at line', body[:m.start()].count('\n') + 1, env, stack[-3:])
            ok = False
            break
        stack.pop()
print('env balanced' if ok and not stack else 'unclosed %s' % stack)

nv = re.sub(r'\\begin\{verbatim\}.*?\\end\{verbatim\}', '', body, flags=re.S)
d = 0
for i, ch in enumerate(nv):
    if ch == '{' and nv[i - 1] != BS:
        d += 1
    elif ch == '}' and nv[i - 1] != BS:
        d -= 1
    if d < 0:
        print('negative brace depth near line', nv[:i].count('\n') + 1)
        break
print('brace depth at end', d)

labels = set(re.findall(r'\\label\{([^}]+)\}', body))
refs = set(re.findall(r'\\ref\{([^}]+)\}', body))
print('missing labels', refs - labels)

cites = [c.strip() for g in re.findall(r'\\cite\{([^}]+)\}', body) for c in g.split(',')]
items = re.findall(r'\\bibitem\{([^}]+)\}', body)
print('uncited bibitems', set(items) - set(cites), '| missing bibitems', set(cites) - set(items))
order = []
for c in cites:
    if c not in order:
        order.append(c)
print('bib order matches first citation:', order == items)
if order != items:
    print(' cite order:', order)
    print(' bib order :', items)

print('VERIFY flags:', len(re.findall(r'\\verify\{', body)) - 1)
txt = re.sub(r'\\begin\{(tikzpicture|verbatim|thebibliography)\}.*?\\end\{\1\}', '', body, flags=re.S)
txt = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?', '', txt)
print('approx words (excl. tikz/bib/verbatim):', len(re.findall(r'[A-Za-z][A-Za-z\-]+', txt)))
