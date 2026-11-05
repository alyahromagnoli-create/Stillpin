"""Local, portable reference library. No source files are modified."""
from pathlib import Path
import json
import shutil
import time
import uuid
from PIL import Image, ImageOps
import fitz

IMAGES = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif', '.tif', '.tiff', '.ico'}
TEXT = {'.txt', '.md', '.py', '.js', '.ts', '.json', '.csv', '.log', '.c', '.cpp', '.h', '.css', '.html', '.yaml', '.yml'}

class Library:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.assets = self.root / 'assets'
        self.assets.mkdir(parents=True, exist_ok=True)
        self.state = self.root / 'session.json'

    def import_file(self, source):
        source = Path(source)
        suffix = source.suffix.lower()
        if suffix in IMAGES:
            with Image.open(source) as image:
                image.verify()
            kind, pages = 'image', 1
        elif suffix == '.pdf':
            with fitz.open(source) as doc:
                if doc.is_encrypted:
                    raise ValueError('暂不支持加密 PDF，请先解密或截图。')
                pages = len(doc)
                if not pages:
                    raise ValueError('PDF 没有可预览的页面。')
            kind = 'pdf'
        elif suffix in TEXT:
            if source.stat().st_size > 4 * 1024 * 1024:
                raise ValueError('文本超过 4 MB，请截取需要的部分后导入。')
            kind, pages = 'text', 1
        else:
            raise ValueError('支持图片、PDF、TXT/Markdown/代码文本。Word、PPT 请截图后粘贴。')
        dest = self.assets / (uuid.uuid4().hex + suffix)
        shutil.copy2(source, dest)
        return dict(id=dest.stem, name=source.name, path=str(dest), kind=kind, pages=pages)

    def import_image(self, image, name='剪贴板图片'):
        dest = self.assets / (uuid.uuid4().hex + '.png')
        image.save(dest, 'PNG')
        return dict(id=dest.stem, name=name, path=str(dest), kind='image', pages=1)

    def text(self, item):
        data = Path(item['path']).read_bytes()
        for encoding in ('utf-8-sig', 'gb18030', 'utf-16'):
            try:
                return data.decode(encoding)
            except UnicodeError:
                pass
        return data.decode('utf-8', errors='replace')

    def page(self, item, number=0):
        if item['kind'] == 'pdf':
            with fitz.open(item['path']) as doc:
                if not 0 <= number < len(doc):
                    raise ValueError('PDF 页码超出范围。')
                page = doc[number]
                scale = min(2, 2400 / max(page.rect.width, page.rect.height))
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        with Image.open(item['path']) as image:
            image.seek(0)
            return ImageOps.exif_transpose(image).convert('RGBA')

    def save(self, items):
        # Relative asset paths make moving the entire portable folder safe.
        stored = []
        for item in items:
            row = dict(item)
            row['path'] = str(Path(row['path']).resolve().relative_to(self.root))
            stored.append(row)
        temporary = self.state.with_suffix('.new')
        temporary.write_text(json.dumps(stored, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(self.state)

    def load(self):
        if not self.state.exists():
            return []
        try:
            data = json.loads(self.state.read_text(encoding='utf-8'))
            if not isinstance(data, list):
                raise ValueError('bad state')
            valid = []
            for row in data:
                if not isinstance(row, dict):
                    continue
                path = (self.root / row.get('path', '')).resolve()
                if path.is_relative_to(self.assets) and path.is_file() and row.get('kind') in ('image', 'pdf', 'text'):
                    row['path'] = str(path)
                    valid.append(row)
            return valid
        except (OSError, ValueError, TypeError):
            backup = self.root / ('session.broken-' + str(time.time_ns()) + '.json')
            shutil.copy2(self.state, backup)
            return []
