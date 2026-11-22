#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convierte las fotos del catalogo (webp) a JPG chicos para el iPad viejo (iOS 9).

USO (en la carpeta clonada del repo pelsas-distribuidora, donde estan data.json e img/):
    pip install pillow
    python convertir_fotos.py

Genera:
    img-ipad/p/<art>.jpg        foto de cada producto (500 px, lado mayor)
    img-ipad/b/<marca>.jpg      foto/logo de cada marca (500 px)

Es incremental: si lo volves a correr solo convierte lo que falta.
    python convertir_fotos.py --forzar    -> reconvierte todo
"""
import io, json, os, sys, urllib.request
from PIL import Image

SITIO = "https://pelsas-distribuidora.pages.dev/"
MAXPX = 500
CALIDAD = 72
FORZAR = "--forzar" in sys.argv
GEN = {"raw": "img/gen-raw.webp", "smoking": "img/gen-smoking.webp",
       "darkhorse": "img/gen-darkhorse.webp", "elements": "img/gen-elements.webp"}

def abrir(origen):
    """origen: URL http(s) o ruta relativa (disco local; si no esta, la baja del sitio)."""
    if origen.startswith("http"):
        url = origen
    else:
        if os.path.exists(origen):
            return Image.open(origen)
        url = SITIO + origen
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return Image.open(io.BytesIO(r.read()))

def guardar(img, destino):
    img.load()
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        fondo.paste(img, mask=img.split()[-1])
        img = fondo
    else:
        img = img.convert("RGB")
    img.thumbnail((MAXPX, MAXPX), Image.LANCZOS)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=CALIDAD, optimize=True)

def intentar(origenes, destino):
    if os.path.exists(destino) and not FORZAR:
        return "ya"
    for o in origenes:
        try:
            guardar(abrir(o), destino)
            return "ok"
        except Exception:
            continue
    return "falta"

def main():
    if not os.path.exists("data.json"):
        sys.exit("No encuentro data.json. Corre el script dentro de la carpeta del repo.")
    d = json.load(open("data.json", encoding="utf-8"))
    brands, products = d["brands"], d["products"]

    # misma logica que la app: los productos traidos de V2 tienen foto en Supabase (p.img)
    todos = [p for l in products.values() for p in l]
    locales = set(str(p["art"]) for p in todos if not p.get("v2") and p.get("art"))
    ext = {}
    for p in todos:
        if p.get("v2") and p.get("img") and p.get("art") and str(p["art"]) not in locales:
            ext[str(p["art"])] = p["img"]

    cont = {"ok": 0, "ya": 0, "falta": 0}
    faltan = []

    # marcas: preferimos la foto de vidriera (vid-<id>.webp), si no el logo
    for b in brands:
        orig = ["img/vid-%s.webp" % b["id"]]
        if b.get("logo"):
            orig.append(b["logo"])
        r = intentar(orig, "img-ipad/b/%s.jpg" % b["id"])
        cont[r] += 1
        if r == "falta":
            faltan.append("marca " + b["id"])

    # productos activos (uno por codigo de articulo)
    hechos = set()
    total = sum(1 for p in todos if p.get("activo"))
    n = 0
    for bid, lista in products.items():
        for p in lista:
            if not p.get("activo") or not p.get("art"):
                continue
            art = str(p["art"])
            n += 1
            if art in hechos:
                continue
            hechos.add(art)
            orig = []
            if art in ext:
                orig.append(ext[art])
            orig.append("img/%s.webp" % art)
            if bid in GEN:
                orig.append(GEN[bid])
            r = intentar(orig, "img-ipad/p/%s.jpg" % art)
            cont[r] += 1
            if r == "falta":
                faltan.append("%s (%s)" % (art, p["name"]))
            if n % 100 == 0:
                print("  %d / %d" % (n, total), flush=True)

    print("\nListo. Convertidas: %d | ya estaban: %d | sin foto: %d" % (cont["ok"], cont["ya"], cont["falta"]))
    if faltan:
        open("fotos_faltantes.txt", "w", encoding="utf-8").write("\n".join(faltan))
        print("Los productos sin foto salen con un icono. Lista en fotos_faltantes.txt")

if __name__ == "__main__":
    main()
