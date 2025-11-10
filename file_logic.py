import os
import shutil
import json
import sqlite3
import zipfile
from datetime import datetime

from PyQt6.QtGui import QPixmap, QColor, QFont
from PyQt6.QtCore import QPointF

from document import Document


def pack(project_dir: str, zip_path: str):
    """
    Упаковывает содержимое prj (layers/, manifest.json, project.db)
    в zip-архив .pld (по сути zip).
    """
    prj_dir = project_dir
    layers_dir = os.path.join(prj_dir, "layers")
    manifest_file = os.path.join(prj_dir, "manifest.json")
    db_file = os.path.join(prj_dir, "project.db")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # layers/
        if os.path.isdir(layers_dir):
            for root, dirs, files in os.walk(layers_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel = os.path.relpath(full_path, prj_dir)
                    zf.write(full_path, rel)

        # manifest.json
        if os.path.isfile(manifest_file):
            zf.write(manifest_file, "manifest.json")

        # project.db
        if os.path.isfile(db_file):
            zf.write(db_file, "project.db")


def unpack(zip_path: str, project_dir: str):
    """
    Распаковывает содержимое архива (.pld/.zip) в prj/
    """
    prj_dir = project_dir

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if (member.startswith("layers/") or 
                member == "manifest.json" or 
                member == "project.db"):
                zf.extract(member, prj_dir)

def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path) 
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Не удалось удалить {file_path}. Причина: {e}')


class NotCorrectFolder(Exception):
    pass


class SaveDoc:
    def __init__(self, document, folder_path):
        self.doc = document
        self.tmp_folder = os.path.dirname(os.path.abspath(__file__))
        self.tmp_folder = os.path.join(self.tmp_folder, "prj")

        os.makedirs(self.tmp_folder, exist_ok=True)
        clear_folder(self.tmp_folder)

        self.save_manifest()

        self.db_path = os.path.join(self.tmp_folder, "project.db")
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

        self.save_layers()

        self.conn.commit()
        self.conn.close()

        pack(self.tmp_folder, folder_path)
        clear_folder(self.tmp_folder)


    # === 1. MANIFEST ===
    def save_manifest(self):
        data = {
            "version": self.doc.sys_version,
            "discription": self.doc.dsc,
            "project_name": self.doc.name,
            "canvas_width": self.doc.width,
            "canvas_height": self.doc.height,

            "instrument": self.doc.activeTool.type,
            "color": tuple(self.doc.color.getRgb()[:3]),

            "current_layer": 0,#self.doc.active_layer_index,

            "created": self.doc.created,
            "modified": datetime.now().timestamp()
        }

        with open(os.path.join(self.tmp_folder, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


    def create_tables(self):
        c = self.conn.cursor()

        c.execute("""
        CREATE TABLE layers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            type TEXT,
            visible INTEGER,
            locked INTEGER,
            opacity REAL,
            z_value INTEGER,
            scale REAL,
            pos_x INTEGER,
            pos_y INTEGER
        )
        """)

        c.execute("""
        CREATE TABLE layer_image (
            layer_id INTEGER PRIMARY KEY,
            pixmap_path TEXT
        )
        """)

        c.execute("""
        CREATE TABLE layer_solid (
            layer_id INTEGER PRIMARY KEY,
            color_r INTEGER,
            color_g INTEGER,
            color_b INTEGER
        )
        """)

        c.execute("""
        CREATE TABLE layer_text (
            layer_id INTEGER PRIMARY KEY,
            text TEXT,
            font_family TEXT,
            font_size INTEGER,
            color_r INTEGER,
            color_g INTEGER,
            color_b INTEGER
        )
        """)


    # === 3. СОХРАНЕНИЕ СЛОЁВ ===
    def save_layers(self):
        c = self.conn.cursor()

        # Каталог для изображений
        layers_dir = os.path.join(self.tmp_folder, "layers")
        os.makedirs(layers_dir, exist_ok=True)

        for i, layer in enumerate(self.doc.layers._layers):
            # === Запись в layers ===
            c.execute("""
                INSERT INTO layers (id, name, type, visible, locked, opacity, z_value, scale, pos_x, pos_y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                i,
                layer.name,
                layer.type,
                int(layer.visible),
                int(layer.locked),
                layer.opacity,
                layer.z_value,
                layer.scale,
                layer.pos().x(),
                layer.pos().y()
            ))

            if layer.type == "Image":
                filename = f"layer_{i}.png"
                save_path = os.path.join(layers_dir, filename)
                layer.pixmap.save(save_path, "PNG")

                c.execute("INSERT INTO layer_image (layer_id, pixmap_path) VALUES (?, ?)",
                          (i, f"layers/{filename}"))

            elif layer.type == "Solid":
                r, g, b, _ = layer.solid_color.getRgb()
                c.execute("INSERT INTO layer_solid (layer_id, color_r, color_g, color_b) VALUES (?, ?, ?, ?)",
                          (i, r, g, b))

            elif layer.type == "Text":
                r, g, b, _ = layer.text_color.getRgb()
                c.execute("""
                INSERT INTO layer_text(layer_id, text, font_family, font_size, color_r, color_g, color_b)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    i,
                    layer.text,
                    layer.font.family(),
                    layer.font.pixelSize(),
                    r, g, b
                ))


class OpenDoc:
    def __init__(self, file_path):
        self.tmp_folder = os.path.dirname(os.path.abspath(__file__))
        self.tmp_folder = os.path.join(self.tmp_folder, "prj")

        unpack(file_path, self.tmp_folder)

        try:
            self.db_path = os.path.join(self.tmp_folder, "project.db")
            self.manifest_path = os.path.join(self.tmp_folder, "manifest.json")
        except FileNotFoundError:
            raise NotCorrectFolder("Please select correct folder")

    def get_opened_document(self):
        # Чтение manifest
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise NotCorrectFolder("Please select correct folder")

        doc = Document(
            name=data["project_name"],
            width=data["canvas_width"],
            height=data["canvas_height"]
        )
        doc.color = QColor(*data["color"])
        doc.created = data["created"]
        doc.modified = data["modified"]
        doc.version = data["version"]
        if data["discription"]:
            doc.dsc = data["discription"]

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        #  layers
        c.execute("SELECT id, name, type, visible, locked, opacity, z_value, scale, pos_x, pos_y FROM layers")
        layers = c.fetchall()

        for layer_id, name, ltype, visible, locked, opacity, z_value, scale, pos_x, pos_y in layers:
            if ltype == "Layer":
                continue

            if ltype == "Solid":
                c.execute("SELECT color_r, color_g, color_b FROM layer_solid WHERE layer_id=?", (layer_id,))
                r, g, b = c.fetchone()
                doc.add_solid_layer(name, QColor(r, g, b))
                layer = doc.layers.get_active_layer()

            elif ltype == "Image":
                c.execute("SELECT pixmap_path FROM layer_image WHERE layer_id=?", (layer_id,))
                (pixmap_path,) = c.fetchone()
                pixmap = QPixmap(os.path.join(self.tmp_folder, pixmap_path))
                doc.add_pixmap_layer(name, pixmap)
                layer = doc.layers.get_active_layer()

            elif ltype == "Text":
                c.execute("SELECT text, font_family, font_size, color_r, color_g, color_b FROM layer_text WHERE layer_id=?", (layer_id,))
                text, font_family, font_size, r, g, b = c.fetchone()
                doc.add_text_layer(name, text)
                layer = doc.layers.get_active_layer()
                font = QFont()
                font.setFamily(font_family)
                font.setPixelSize(font_size)
                layer.set_font(font)
                layer.set_color(QColor(r, g, b))

            layer.set_visible(bool(visible))
            layer.set_locked(bool(locked))
            layer.set_opacity(opacity)
            layer.group.setZValue(z_value)
            layer.group.setPos(QPointF(pos_x, pos_y))
            layer.set_scale(scale / 100)

        conn.close()
        clear_folder(self.tmp_folder)
        for i, layer in enumerate(doc.layers._layers):
            layer.set_z(i)
        return doc, data["version"]
