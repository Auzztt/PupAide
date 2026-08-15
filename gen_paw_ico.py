import sys
sys.path.insert(0, r'd:\PycharmProjects\PupAide\PupAide')
from PyQt6.QtWidgets import QApplication
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPixmap, QPainter, QImage
from PyQt6.QtCore import QByteArray, QRectF, Qt, QBuffer
import struct

app = QApplication(sys.argv)

_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">'
    '<rect width="256" height="256" fill="#FF6B35"/>'
    '<circle cx="212" cy="108" r="20" fill="none" stroke="#FFFFFF" '
    'stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/>'
    '<circle cx="44" cy="108" r="20" fill="none" stroke="#FFFFFF" '
    'stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/>'
    '<circle cx="92" cy="60" r="20" fill="none" stroke="#FFFFFF" '
    'stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/>'
    '<circle cx="164" cy="60" r="20" fill="none" stroke="#FFFFFF" '
    'stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/>'
    '<path d="M128,104A36,36,0,0,0,93.43,130a43.49,43.49,0,0,1-20.67,25.9,32,32,0,0,0,27.73,57.62,72.49,72.49,0,0,1,55,0,32,32,0,0,0,27.73-57.62A43.46,43.46,0,0,1,162.57,130,36,36,0,0,0,128,104Z" '
    'fill="none" stroke="#FFFFFF" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/>'
    '</svg>'
)

def render_image(size):
    renderer = QSvgRenderer(QByteArray(_SVG.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)

def img_to_png_bytes(img):
    buf = QBuffer()
    buf.open(QBuffer.OpenModeFlag.ReadWrite)
    img.save(buf, 'PNG')
    data = bytes(buf.data())
    buf.close()
    return data

def save_ico(path, sizes):
    images = [render_image(s) for s in sizes]
    count = len(images)
    with open(path, 'wb') as f:
        f.write(struct.pack('<HHH', 0, 1, count))
        offset = 6 + count * 16
        for img in images:
            data = img_to_png_bytes(img)
            w = img.width()
            h = img.height()
            w_byte = w if w < 256 else 0
            h_byte = h if h < 256 else 0
            f.write(struct.pack('<BBBBHHII', w_byte, h_byte, 0, 0, 1, 32, len(data), offset))
            offset += len(data)
        for img in images:
            f.write(img_to_png_bytes(img))

out = r'd:\PycharmProjects\PupAide\PupAide\paw.ico'
save_ico(out, [256, 128, 64, 48, 32, 16])
print("Done:", out)
