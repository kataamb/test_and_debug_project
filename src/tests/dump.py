import os
import sys

def dump_tree(root_dir, output_file, binary_mode=False):
    root_dir = os.path.abspath(root_dir)
    output_file = os.path.abspath(output_file)
    
    mode = 'wb' if binary_mode else 'w'
    encoding = None if binary_mode else 'utf-8'
    
    with open(output_file, mode, encoding=encoding) as out:
        for dirpath, dirnames, filenames in os.walk(root_dir, onerror=lambda e: None):
            # пропускаем выходной файл
            dirnames[:] = [
                d for d in dirnames
                if os.path.abspath(os.path.join(dirpath, d)) != output_file
            ]
            
            # проверяем доступ к папке — если нет, пропускаем целиком
            if not os.access(dirpath, os.R_OK | os.X_OK):
                dirnames[:] = []
                continue
            
            rel_dir = os.path.relpath(dirpath, root_dir)
            
            if binary_mode:
                out.write(f"\n\n{'='*80}\n[DIR] {rel_dir}\n{'='*80}\n".encode('utf-8'))
            else:
                out.write(f"\n\n{'='*80}\n[DIR] {rel_dir}\n{'='*80}\n")
            
            for filename in sorted(filenames):
                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root_dir)
                
                if os.path.abspath(full_path) == output_file:
                    continue
                
                # проверяем доступ к файлу
                if not os.access(full_path, os.R_OK):
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
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    output = sys.argv[2] if len(sys.argv) > 2 else 'dump.txt'
    binary = '--binary' in sys.argv
    
    dump_tree(root, output, binary_mode=binary)
    print(f"Готово: {output}")
