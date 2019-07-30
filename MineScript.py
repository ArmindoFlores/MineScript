import sys
import os
import traceback
import shutil
from antlr4 import *
from MineScriptLexer import MineScriptLexer
from MineScriptParser import MineScriptParser
from Visitor import Visitor


packmeta = """{
  "pack": {
    "pack_format": 1,
    "description": "%s"
  }
}
"""

load_file = """{
    "values": [
        "%s:load"
    ]
}"""

tick_file = """{
    "values": [
        "%s:tick"
    ]
}"""

def parent(path):
    return os.path.abspath(os.path.join(path, os.pardir))

def check_EOF(file):
    with open(file, "r") as f:
        if not f.readlines()[-1].endswith("\n"):
            padded = False
        else:
            padded = True
    if not padded:
        with open(file, "a") as f:
            f.write("\n")            

def mkdir(*args):
    try:
        os.mkdir(*args)
    except FileExistsError:
        pass

def create_structure(name, description, path):
    mkdir(os.path.join(path, name))
    mkdir(os.path.join(path, name, "data"))
    with open(os.path.join(path, name, "pack.mcmeta"), "w") as file:
        file.write(packmeta%description)
    mkdir(os.path.join(path, name, "data", "minecraft"))
    mkdir(os.path.join(path, name, "data", name))
    mkdir(os.path.join(path, name, "data", "minecraft", "tags"))
    mkdir(os.path.join(path, name, "data", "minecraft", "tags", "functions"))
    mkdir(os.path.join(path, name, "data", name, "functions"))
    mkdir(os.path.join(path, name, "data", name, "tags"))
    with open(os.path.join(path, name, "data", "minecraft", "tags", "functions", "load.json"), "w") as file:
        file.write(load_file%name)
    with open(os.path.join(path, name, "data", "minecraft", "tags", "functions", "tick.json"), "w") as file:
        file.write(tick_file%name)
        
    
def main(file, name):
    with open(file, "r") as f:
        code = f.readlines()
    
    check_EOF(file)
    input = FileStream(file)
    lexer = MineScriptLexer(input)
    stream = CommonTokenStream(lexer)
    parser = MineScriptParser(stream)
    tree = parser.prog()

    visitor = Visitor(name, code)
    visitor.visit(tree)

    return (visitor.memory, visitor.igmemory, visitor.igfunctions, visitor.igloops)
    

def assemble_pack(name, memory, path):
    global commands
    # Setup scoreboard  variables
    with open(os.path.join(path, name, "data", name, "functions", "setup.mcfunction"), "w") as file:
        print("Setting up variables")
        for variable in memory[1]:
            if not variable.startswith("_"):
                print("Found ingame variable %s, adding it to the scoreboard"%variable)
                file.write("scoreboard objectives add %s dummy {\"text\":\"%s\"}\n"%(variable, variable.capitalize()))
                file.write("scoreboard players set MineScript %s 0\n"%variable)
                commands += 2

    # Setup "_temp%%" variables
    with open(os.path.join(path, name, "data", name, "functions", "temp.mcfunction"), "w") as file:
        print("\nSetting up temporary variables")
        for variable in memory[1]:
            if variable.startswith("_"):
                file.write("scoreboard objectives add %s dummy\n"%variable)
                file.write("scoreboard players set MineScript %s 0\n"%variable)
                commands += 2

    # Setup "_for%%" loops
    print("\nSetting up loops")
    for loop in memory[3]:
        with open(os.path.join(path, name, "data", name, "functions", "%s.mcfunction"%loop), "w") as file:
            for command in memory[3][loop]:
                file.write(command + "\n")
                commands += 1
                
    print("\nSetting up functions")
    
    # Build function files
    if "load" in memory[2]:
        print("Found load function, exporting")
        content = memory[2]["load"]
        with open(os.path.join(path, name, "data", name, "functions", "load.mcfunction"), "w") as file:
            file.write("function %s:setup\n"%name)
            file.write("function %s:temp\n"%name)
            commands += 2
            for line in content:
                file.write(line+"\n")
                commands += 1
        del memory[2]["load"]
    else:
        with open(os.path.join(path, name, "data", name, "functions", "load.mcfunction"), "w") as file:
            file.write("function %s:setup\n"%name)
            file.write("function %s:temp\n"%name)
            commands += 2
    
    if "tick" in memory[2]:
        print("Found tick function, exporting")
        content = memory[2]["tick"]
        with open(os.path.join(path, name, "data", name, "functions", "tick.mcfunction"), "w") as file:
            for line in content:
                file.write(line+"\n")
                commands += 1
        del memory[2]["tick"]


    if len(memory[2]): print("Exporting other functions...")
    for function in memory[2]:
        content = memory[2][function]
        with open(os.path.join(path, name, "data", name, "functions", "%s.mcfunction"%function), "w") as file:
            for line in content:
                file.write(line+"\n")
                commands += 1
        
try:
    commands = 0
    if sys.argv[0] == "python":
        filename = sys.argv[2]
    else:
        filename = sys.argv[1]

    path = '.'.join(filename.split(".")[:-1])+".info"
    if os.path.isfile(path):
        with open(path, "r") as file:
            f = file.readlines()
            name = f[0].strip()
            description = f[1].strip().replace("\"", "\\\"")
    else:
        print("Couldn't find the .info file! Using defaults...\n")
        name = "datapack"
        description = "A datapack created with minescript"

    path = parent(filename)
    path = os.path.join(path, "build")
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    
    distpath = os.path.join(parent(filename), "dist")
    try:
        os.mkdir(distpath)
    except FileExistsError:
        pass

    create_structure(name, description, path)
    memory = main(filename, name)
    
    assemble_pack(name, memory, path)

    shutil.make_archive(os.path.join(distpath, name), 'zip', os.path.join(path, name))
    print("\nFinished building %s."%name)
    print("Total: %i commands"%commands)
    input("Press enter to continue...")
    
except Exception as e:
    if str(e) != "Abort":
        traceback.print_exc()
    input()
