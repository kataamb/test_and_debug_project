import os
import sys

# Папки, которые не обходим никогда
IGNORED_DIRS = {
    '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
    '.git', '.idea', '.vscode', 'allure-results', 'htmlcov',
    '.venv', 'venv', 'node_modules', 'dist', 'build', '.tox',
}

# Расширения, которые в текстовом режиме пропускаем
BINARY_EXTS = {
    '.pyc', '.pyo', '.so', '.pyd', '.dll', '.exe', '.bin',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp',
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.db', '.sqlite', '.sqlite3', '.mdb',
    '.woff', '.woff2', '.ttf', '.otf', '.eot',
    '.mp3', '.mp4', '.avi', '.mov', '.wav',
    '.pkl', '.pickle', '.npy', '.npz', '.h5', '.pt', '.pth',
}

# Файлы, которые никогда не включаем в дамп
IGNORED_FILES = {
    'poetry.lock', 'pytest.ini', 'pyproject.toml','.coverage',
}


def is_ignored_dir(dirname):
    """Проверяет, нужно ли пропустить папку (включая allure*)."""
    return dirname in IGNORED_DIRS or dirname.lower().startswith('allure')


def is_ignored_file(filename):
    """Проверяет, нужно ли пропустить файл."""
    return filename in IGNORED_FILES


def dump_tree(root_dir, output_file, binary_mode=False):
    root_dir = os.path.abspath(root_dir)
    output_file = os.path.abspath(output_file)

    mode = 'wb' if binary_mode else 'w'
    encoding = None if binary_mode else 'utf-8'

    with open(output_file, mode, encoding=encoding) as out:
        for dirpath, dirnames, filenames in os.walk(root_dir, onerror=lambda e: None):
            # 1) исключаем кэш-папки и allure* — НА МЕСТЕ, чтобы os.walk не заходил
            dirnames[:] = [d for d in dirnames if not is_ignored_dir(d)]

            # 2) убираем выходной файл, если он случайно попал в dirnames
            dirnames[:] = [
                d for d in dirnames
                if os.path.abspath(os.path.join(dirpath, d)) != output_file
            ]

            # 3) нет доступа к папке — пропускаем целиком
            if not os.access(dirpath, os.R_OK | os.X_OK):
                dirnames[:] = []
                continue

            rel_dir = os.path.relpath(dirpath, root_dir)
            header = f"\n\n{'='*80}\n[DIR] {rel_dir}\n{'='*80}\n"
            out.write(header.encode('utf-8') if binary_mode else header)

            for filename in sorted(filenames):
                # пропускаем файлы из чёрного списка
                if is_ignored_file(filename):
                    continue

                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root_dir)

                if os.path.abspath(full_path) == output_file:
                    continue
                if not os.access(full_path, os.R_OK):
                    continue

                # в ТЕКСТОВОМ режиме бинарники не пишем
                if not binary_mode:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in BINARY_EXTS:
                        continue

                if binary_mode:
                    out.write(f"\n--- FILE: {rel_path} ---\n".encode('utf-8'))
                    try:
                        with open(full_path, 'rb') as f:
                            out.write(f.read())
                    except (PermissionError, OSError):
                        continue
                    out.write(b"\n--- END FILE ---\n")
                else:
                    out.write(f"\n--- FILE: {rel_path} ---\n")
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                            out.write(f.read())
                    except (PermissionError, OSError):
                        continue
                    out.write("\n--- END FILE ---\n")


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--binary']
    binary = '--binary' in sys.argv

    root = args[0] if len(args) > 0 else '.'
    output = args[1] if len(args) > 1 else 'dump.txt'

    dump_tree(root, output, binary_mode=binary)
    print(f"Готово: {output}")
