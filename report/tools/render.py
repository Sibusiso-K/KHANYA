import os, sys
sys.path.insert(0, os.path.join(os.environ["TEMP"], "claude", "pdfrender"))
import pypdfium2 as pdfium

pdf_path, out_dir = sys.argv[1], sys.argv[2]
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.6
pages = sys.argv[4] if len(sys.argv) > 4 else None
os.makedirs(out_dir, exist_ok=True)
pdf = pdfium.PdfDocument(pdf_path)
print("pages", len(pdf))
sel = range(len(pdf))
if pages:
    a, b = pages.split("-")
    sel = range(int(a) - 1, min(int(b), len(pdf)))
for i in sel:
    img = pdf[i].render(scale=scale).to_pil()
    out = os.path.join(out_dir, f"page{i + 1:02d}.png")
    img.save(out)
print("rendered", list(sel)[0] + 1, "to", list(sel)[-1] + 1)
