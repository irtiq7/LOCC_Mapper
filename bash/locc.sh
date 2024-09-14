import os
import sys

def count_lines_of_code(directory)
    file_types = {}
    file_counts = {}

    for root, _, files in os.walk(directory)
        for file in files
            file_type = file.split('.')[-1]
            file_path = os.path.join(root, file)
            try
                with open(file_path, 'r', encoding='utf-8') as f
                    lines = f.readlines()
            except UnicodeDecodeError
                try
                    with open(file_path, 'r', encoding='latin-1') as f
                        lines = f.readlines()
                except UnicodeDecodeError
                    continue  # Skip files that can't be read

            line_count = len(lines)
            file_types[file_type] = file_types.get(file_type, 0) + line_count
            file_counts[file_type] = file_counts.get(file_type, 0) + 1

    print(-------------------------------------------------------------------------------)
    print(File type                    files          lines)
    print(-------------------------------------------------------------------------------)
    for file_type in file_types
        print(f{file_type28} {file_counts[file_type]14} {file_types[file_type]14})
    print(-------------------------------------------------------------------------------)

if __name__ == __main__
    if len(sys.argv) != 2
        print(Usage python count_lines.py directory)
        sys.exit(1)

    directory = sys.argv[1]
    count_lines_of_code(directory)
