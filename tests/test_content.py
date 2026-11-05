import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import pytest
from PIL import Image
import fitz
from content import Library

def test_copy_survives_original_deletion(tmp_path):
    p = tmp_path / '原图.png'
    Image.new('RGB', (123, 77), 'red').save(p)
    lib = Library(tmp_path / 'data')
    item = lib.import_file(p)
    p.unlink()
    assert lib.page(item, 0).size == (123, 77)
    assert Path(item['path']).is_relative_to(tmp_path / 'data')

def test_pdf_pages(tmp_path):
    p = tmp_path / 'two.pdf'
    doc = fitz.open()
    doc.new_page(width=200, height=100)
    doc.new_page(width=300, height=200)
    doc.save(p)
    doc.close()
    lib = Library(tmp_path / 'data')
    item = lib.import_file(p)
    assert item['pages'] == 2
    assert lib.page(item, 1).width > lib.page(item, 0).width
    with pytest.raises(ValueError):
        lib.page(item, 2)

def test_text_and_reject_bad(tmp_path):
    p = tmp_path / '中文.txt'
    p.write_bytes('参考内容'.encode('gb18030'))
    lib = Library(tmp_path / 'data')
    item = lib.import_file(p)
    assert lib.text(item) == '参考内容'
    bad = tmp_path / 'bad.exe'
    bad.write_bytes(b'broken')
    with pytest.raises(ValueError):
        lib.import_file(bad)

def test_state_recovery_and_alpha_image(tmp_path):
    lib = Library(tmp_path / 'data')
    item = lib.import_image(Image.new('RGBA', (20, 30), (0, 0, 0, 0)))
    lib.save([dict(item, geometry='400x300+10+20', opacity=.7)])
    assert lib.load()[0]['opacity'] == .7
    lib.state.write_text('{bad', encoding='utf-8')
    assert lib.load() == []
    assert list(lib.root.glob('session.broken-*.json'))

def test_move_portable_folder(tmp_path):
    import shutil
    lib = Library(tmp_path / 'old' / 'data')
    item = lib.import_image(Image.new('RGB', (12, 16)))
    lib.save([item])
    shutil.move(str(tmp_path / 'old'), str(tmp_path / '新的 位置'))
    moved = Library(tmp_path / '新的 位置' / 'data')
    assert moved.page(moved.load()[0]).size == (12, 16)

def test_session_rejects_outside_asset_paths(tmp_path):
    import json
    lib = Library(tmp_path / 'data')
    outside = tmp_path / 'secret.txt'
    outside.write_text('not a library asset')
    lib.state.write_text(json.dumps([dict(path=str(outside), kind='text')]), encoding='utf-8')
    assert lib.load() == []
