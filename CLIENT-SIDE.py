import subprocess
import sys
import os

SOURCE_DIRS = [
    '/home/pc/Desktop/test_dir'
]


def upload_file(filename, path):
    command = (f"curl -X POST -H \"Content-Disposition: attachment; filename=\\\"{filename}\\\"; path=\\\"{path}\\\"\""+
               f" --data-binary \"@{path}/{filename}\" http://192.168.43.52:1030/")
    subprocess.call(command, shell=True)


for path in SOURCE_DIRS:
    os.makedirs(f'BACKUP/{path}', exist_ok=True)
    files = sorted(os.listdir(path))
    for file in files:
        print(file)
        upload_file(f'{file}', f'{path}')
