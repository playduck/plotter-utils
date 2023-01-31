#!/usr/bin/env python3

import os
import sys
import subprocess

inFile = sys.argv[1]
print(inFile)
basename = os.path.basename(inFile)
name, extension = os.path.splitext(basename)
if "svg" not in extension:
    print("inFile is no svg")
    sys.exit()

outFileHpgl = f"./plots/hpgl/{name}-out.hpgl"
outFileSvg = f"./plots/svg/{name}-out.svg"

cmd = [
f"vpype",
f"--config ./config.toml",
f"read {inFile}",
# f"linemerge --tolerance 0.5mm",
# f"linesort",
# f"reloop",
# f"linesimplify",
# f"linesort --two-opt",
# f"scale 1.39 1.39",
f"scaleto 29.7cm 21cm",
f"pagesize --landscape a4",
f"frame",
f"write -f hpgl -d dxy1150 --page-size a3 --landscape -vs 8 {outFileHpgl}",
f"write {outFileSvg}",
f"show",
]

cmd_string = " ".join(cmd)
print("---")
print(cmd_string)
print("---")

os.system(cmd_string)
# subprocess.call(cmd, shell=True)
