# Installation

To start using MineScript, you must first download either the [source code](https://github.com/ArmindoFlores/MineScript) or the [executable file](https://github.com/ArmindoFlores/MineScript/releases/download/v1.1.0-alpha/minescript.exe). MineScript is written in [Python 3](https://www.python.org/downloads/), so if you download the source code, you'll need it too.


__How to build MineScript__


   1. Install [antlr4](https://www.antlr.org/download.html) and its [python targets](https://pypi.org/project/antlr4-python3-runtime/);
   2. Run the command `java org.antlr.v4.Tool -Dlanguage=Python3 -visitor -no-listener MineScript.g4` on the MineScript directory.
   3. To turn your code into a minecraft datapack, use `MineScript.py yourfile.ms` on the command line.