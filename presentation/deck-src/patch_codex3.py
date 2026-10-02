import os
D = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(D, "build_deck.py")
s = open(p, encoding="utf-8").read()
old = '''pl = ch.plots[0]; pl.has_data_labels = True
pl.data_labels.number_format = '0"%"'; pl.data_labels.number_format_is_linked = False
pl.data_labels.position = XL_LABEL_POSITION.ABOVE; pl.data_labels.font.size = Pt(8.5)
va = ch.value_axis; va.maximum_scale = 100; va.minimum_scale = 0; va.has_major_gridlines = True'''
new = '''va = ch.value_axis; va.maximum_scale = 100; va.minimum_scale = 0; va.has_major_gridlines = True'''
assert old in s
s = s.replace(old, new)
anchor = "box(s, 9.45, 1.95, 3.3, 4.6, fill=NAVY, radius=0.14)"
assert anchor in s
cap = '''text(s, 5.1, 5.02, 4.1, 0.3, "  ·  ".join(f"{lbl} {KIN['R'][k]*100:.0f}%" for lbl, k in [("15 s", "0.25"), ("30 s", "0.5"), ("1 min", "1"), ("3 min", "3"), ("20 min", "20")]), size=9, color=MUTED)
'''
s = s.replace(anchor, cap + anchor)
open(p, "w", encoding="utf-8").write(s)
print("ok")
