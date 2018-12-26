import sys
import os
from CompilationEngine import CompilationEngine
from pathlib import Path


def analyze_dir(arg):
    dir_path = Path(arg)
    for file in os.listdir(arg):
        if file.endswith(".jack"):
            file_path = str(dir_path / file)

            analyze_file(file_path)


def analyze_file(address):
    engine = CompilationEngine(address)
    engine.write_file()


def main():
    # verify input files correctness:
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if os.path.isdir(arg):
            analyze_dir(arg)
        else:
            analyze_file(arg)


if __name__ == '__main__':
    main()
