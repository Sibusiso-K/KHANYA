import io, os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_deck.py")
s = io.open(p, encoding="utf-8").read()
a = 'headline(s, f"Taught by QEMSCAN, the camera predicted unseen composites:\\n{n_win} of {n_t} minerals beat the average guess.", y=1.15, size=26)'
b = 'headline(s, f"Taught by QEMSCAN, the camera read unseen feed:\\n{n_win} of {n_t} minerals beat the average guess.", y=1.15, size=28)'
assert s.count(a) == 1, "miss"
s = s.replace(a, b)
io.open(p, "w", encoding="utf-8").write(s)
print("ok")
