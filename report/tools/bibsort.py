r"""Reorder \bibitem entries by first citation and drop uncited ones. Run from report/."""
import re

P = 'main.tex'
s = open(P, encoding='utf-8').read()
bs = s.index(r'\bibitem{')
be = s.index(r'\end{thebibliography}')
items = [x.rstrip() for x in re.split(r'(?=\\bibitem\{)', s[bs:be]) if x.strip()]
by = {re.match(r'\\bibitem\{([^}]+)\}', x).group(1): x for x in items}
body = re.sub(r'(?<!\\)%.*', '', s[:bs] + s[be:])
order = []
for g in re.findall(r'\\cite\{([^}]+)\}', body):
    for c in g.split(','):
        c = c.strip()
        if c not in order:
            order.append(c)
s = s[:bs] + '\n'.join(by[k] for k in order) + '\n' + s[be:]
print('dropped', [k for k in by if k not in order])
open(P, 'w', encoding='utf-8').write(s)
