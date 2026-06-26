"""Génère les icônes PNG pour la PWA GEC sans dépendance externe."""
import struct, zlib, math

def make_png(size, bg=(30, 64, 175), letter_color=(255, 255, 255)):
    """Génère un PNG <size>x<size> avec fond bleu et lettre G centrée."""
    img = [bg] * (size * size)

    # Dessiner un rectangle arrondi simulé (coins arrondis ~15% du rayon)
    r = int(size * 0.18)
    for y in range(size):
        for x in range(size):
            # Coin supérieur gauche
            if x < r and y < r and (x - r) ** 2 + (y - r) ** 2 > r ** 2:
                img[y * size + x] = (255, 255, 255, 0)
                continue
            # Coin supérieur droit
            if x >= size - r and y < r and (x - (size - r - 1)) ** 2 + (y - r) ** 2 > r ** 2:
                img[y * size + x] = (255, 255, 255, 0)
                continue
            # Coin inférieur gauche
            if x < r and y >= size - r and (x - r) ** 2 + (y - (size - r - 1)) ** 2 > r ** 2:
                img[y * size + x] = (255, 255, 255, 0)
                continue
            # Coin inférieur droit
            if x >= size - r and y >= size - r and (x - (size - r - 1)) ** 2 + (y - (size - r - 1)) ** 2 > r ** 2:
                img[y * size + x] = (255, 255, 255, 0)
                continue
            img[y * size + x] = bg

    # Dessiner "G" simplifié (pixels blancs)
    cx, cy = size // 2, size // 2
    font_r = int(size * 0.28)
    stroke = max(2, size // 32)

    for y in range(size):
        for x in range(size):
            dx, dy = x - cx, y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            # Cercle extérieur
            if font_r - stroke <= dist <= font_r:
                # Masquer le quart supérieur droit (ouverture du G)
                if not (dx >= 0 and dy <= -stroke):
                    if not (dx >= -stroke and dy >= 0 and dist > font_r - stroke * 2.5):
                        img[y * size + x] = letter_color
            # Barre horizontale du G (milieu droit)
            if abs(dy) <= stroke and dx >= 0 and dx <= font_r:
                img[y * size + x] = letter_color

    # Encoder PNG
    def write_chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    raw = b""
    for y in range(size):
        raw += b"\x00"  # filter type None
        for x in range(size):
            px = img[y * size + x]
            if len(px) == 4 and px[3] == 0:
                raw += b"\x00\x00\x00\x00"
            else:
                raw += bytes([px[0], px[1], px[2], 255])

    png = b"\x89PNG\r\n\x1a\n"
    png += write_chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
    png += write_chunk(b"IDAT", zlib.compress(raw))
    png += write_chunk(b"IEND", b"")
    return png


import os
base = os.path.dirname(os.path.abspath(__file__))

for sz in [192, 512]:
    with open(os.path.join(base, f"icon-{sz}.png"), "wb") as f:
        f.write(make_png(sz))
    print(f"icon-{sz}.png généré")

# Favicon 32x32
with open(os.path.join(base, "..", "favicon.ico"), "wb") as f:
    png_32 = make_png(32)
    f.write(png_32)
print("favicon.ico généré")
