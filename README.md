# MineScript

MineScript is a scripting language that allows you to easily create complex Minecraft datapacks without having to use the traditional Minecraft command syntax.
It's built using antlr4 and python3.

__How to build MineScript__

   1. Install [antlr4](https://www.antlr.org/download.html) and its [python targets](https://pypi.org/project/antlr4-python3-runtime/).
   2. Run the command `java org.antlr.v4.Tool -Dlanguage=Python3 -visitor -no-listener MineScript.g4` on the MineScript directory.
   3. To turn your code into a minecraft datapack, use `MineScript.py yourfile.ms`

__Documentation:__

   Not available yet
   
__Source code repository and issue tracker:__

   <https://github.com/ArmindoFlores/MineScript>

__License__

   MIT - see file `LICENSE` for details.
   
