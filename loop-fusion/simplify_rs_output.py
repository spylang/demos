#!/usr/bin/env python3

import sys

from pathlib import Path

input_text = sys.stdin.read()

files = {}

lines_file = []
name = None

for line in input_text.split("\n"):
    if line.startswith("# ") and line.endswith(".spy"):
        # new file
        if name is not None:
            files[name] = "\n".join(lines_file)

        name = line[2:-4]
    else:
        lines_file.append(line)

if name is None:
    start = input_text.split("::", 1)[0]
    name = start.split("`")[1]

if name not in files:
    files[name] = "\n".join(lines_file)


for name, content in files.items():
    files[name] = content.replace(name + "::", "").replace(str(Path.cwd()), ".")

for name, content in files.items():
    print(f"# {name}.spy")
    print(files[name])
