#!/usr/bin/env python3
"""
Патчит ui/app.slint: подключает callback `pan(...)`, который мы добавили
в cad_tree_block.slint и cad_link_line.slint, к существующей функции
root.handle_mid_pan(...) — чтобы панорамирование средней кнопкой мыши
снова работало, когда курсор находится над деревом или над линией связи.

Как использовать:
    1. Положите этот файл в корень репозитория (рядом с Cargo.toml)
       либо укажите путь до app.slint первым аргументом:
           python patch_app_slint.py путь/до/ui/app.slint
    2. Запустите:
           python patch_app_slint.py
       (или python3 patch_app_slint.py — смотря что у вас установлено)
    3. Скрипт сам найдёт нужные два места и допишет туда одну строку.
       Если что-то не найдено (например, файл уже пропатчен или отличается
       от того, что мы видели) — скрипт НИЧЕГО не тронет и выведет
       понятную ошибку вместо того, чтобы сломать файл вслепую.

Скрипт идемпотентен: если запустить его дважды, второй раз он просто
скажет, что патч уже применён, и ничего не изменит.
"""

import re
import sys
from pathlib import Path

DEFAULT_PATH = Path("ui/app.slint")

# Каждый anchor — это ОДНА строка, которую мы гарантированно видели
# в исходном файле (в двух местах, где инстанцируются CADLinkLine и
# CADTreeBlock). После неё добавляем проброс pan(...) -> handle_mid_pan(...).
PATCHES = [
    {
        "name": "CADLinkLine (связи)",
        "anchor": r"clicked\(id\)\s*=>\s*\{\s*root\.selected_link_id\s*=\s*id;\s*\}",
        "new_line": "pan(btn, kind, x, y) => { root.handle_mid_pan(btn, kind, x, y); }",
    },
    {
        "name": "CADTreeBlock (дерево)",
        "anchor": r"select_item\(id,\s*text,\s*tree_id\)\s*=>\s*\{\s*root\.select_item\(id,\s*text,\s*tree_id\);\s*\}",
        "new_line": "pan(btn, kind, x, y) => { root.handle_mid_pan(btn, kind, x, y); }",
    },
]

MARKER = "root.handle_mid_pan(btn, kind, x, y)"


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    if not path.exists():
        print(f"Не найден файл: {path}")
        print("Укажите путь явно: python patch_app_slint.py путь/до/ui/app.slint")
        sys.exit(1)

    text = path.read_text(encoding="utf-8")

    if text.count(MARKER) >= 2:
        print("Похоже, патч уже применён (найдено 2+ вставки) — ничего не делаю.")
        sys.exit(0)

    applied = 0
    for patch in PATCHES:
        pattern = re.compile(
            r"^([ \t]*)(" + patch["anchor"] + r")[ \t]*$",
            re.MULTILINE,
        )
        matches = list(pattern.finditer(text))

        if len(matches) == 0:
            print(f"[ПРОПУСК] Не нашёл место для «{patch['name']}» — "
                  f"похоже, файл отличается от ожидаемого. Ничего не меняю здесь.")
            continue
        if len(matches) > 1:
            print(f"[СТОП] Для «{patch['name']}» нашлось {len(matches)} совпадений "
                  f"вместо одного — на всякий случай не трогаю файл вообще.")
            sys.exit(2)

        m = matches[0]
        indent = m.group(1)
        insertion = f"\n{indent}{patch['new_line']}"
        insert_pos = m.end()
        text = text[:insert_pos] + insertion + text[insert_pos:]
        print(f"[OK] Добавлена строка pan(...) после блока «{patch['name']}».")
        applied += 1

    if applied == 0:
        print("\nНичего не применено. Файл не изменён.")
        sys.exit(3)

    backup_path = path.with_suffix(path.suffix + ".bak")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(text, encoding="utf-8")

    print(f"\nГотово: применено патчей — {applied} из {len(PATCHES)}.")
    print(f"Резервная копия оригинала сохранена рядом: {backup_path}")
    if applied < len(PATCHES):
        print("\nВНИМАНИЕ: не все патчи применились — see [ПРОПУСК]/[СТОП] выше.")
        print("Пришлите мне полный текст app.slint, если нужно разобраться руками.")


if __name__ == "__main__":
    main()
