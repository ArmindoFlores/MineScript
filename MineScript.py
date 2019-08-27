import os
import traceback
import shutil
import argparse
from colorama import init, Style, Fore
from antlr4 import *
from MineScriptLexer import MineScriptLexer
from MineScriptParser import MineScriptParser
from MappingVisitor import MVisitor
from Visitor import Visitor


init(convert=True)

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

def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="", help="File to be compiled.")
    parser.add_argument("--verbose", type=int, default=2, help="Verbose level.")
    parser.add_argument("--info_file", type=str, default="", help="Info file location.")
    parser.add_argument("--name", type=str, default="datapack", help="Name of the datapack.")
    parser.add_argument("--description", type=str, default="A datapack created with minescript", help="Description of the datapack.")
    return parser    

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
    try:
        os.mkdir(os.path.join(path, name))
    except FileExistsError:
        shutil.rmtree(os.path.join(path, name))
        os.mkdir(os.path.join(path, name))
        
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
    
    m_visitor = MVisitor(name, code)
    m_visitor.visit(tree)

    visitor = Visitor(name, code)
    visitor.igmemory = [var for var in m_visitor.igmemory if not var.startswith("_")]
    visitor.igfunctionargs = m_visitor.igfunctionargs
    visitor.igfunctionreturn = m_visitor.igfunctionreturn
    visitor.igfunctions = m_visitor.igfunctions
    visitor.visit(tree)

    if verbose >= 1:
        for warning in visitor.warnings:
            print(warning)
        if len(visitor.warnings): print()
    
    return (visitor.memory, visitor.igmemory, visitor.igfunctions, visitor.igloops)
    

def assemble_pack(name, memory, path):
    global commands
    # Setup scoreboard  variables
    with open(os.path.join(path, name, "data", name, "functions", "_setup.mcfunction"), "w") as file:
        if verbose >= 2: print("Setting up variables")
        for variable in memory[1]:
            if not variable.startswith("_"):
                if verbose >= 2: print("Found ingame variable %s, adding it to the scoreboard"%variable)
                file.write("scoreboard objectives add %s dummy {\"text\":\"%s\"}\n"%(variable, variable.capitalize()))
                file.write("scoreboard players set MineScript %s 0\n"%variable)
                commands += 2

    # Setup "_var%%" variables
    with open(os.path.join(path, name, "data", name, "functions", "_vars.mcfunction"), "w") as file:
        if verbose >= 2: print("\nSetting up temporary variables")
        for variable in memory[1]:
            if variable.startswith("_"):
                file.write("scoreboard objectives add %s dummy\n"%variable)
                file.write("scoreboard players set MineScript %s 0\n"%variable)
                commands += 2

    # Setup loops
    if verbose >= 2: print("\nSetting up loops")
    for loop in memory[3]:
        with open(os.path.join(path, name, "data", name, "functions", "%s.mcfunction"%loop), "w") as file:
            for command in memory[3][loop]:
                file.write(command + "\n")
                commands += 1
                
    if verbose >= 2: print("\nSetting up functions")
    
    # Build function files
    if "load" in memory[2]:
        if verbose >= 2: print("Found load function, exporting")
        content = memory[2]["load"]
        with open(os.path.join(path, name, "data", name, "functions", "load.mcfunction"), "w") as file:
            file.write("function %s:_setup\n"%name)
            file.write("function %s:_vars\n"%name)
            commands += 2
            for line in content:
                file.write(line+"\n")
                commands += 1
        del memory[2]["load"]
    else:
        with open(os.path.join(path, name, "data", name, "functions", "load.mcfunction"), "w") as file:
            file.write("function %s:_setup\n"%name)
            file.write("function %s:_vars\n"%name)
            commands += 2
    
    if "tick" in memory[2]:
        if verbose >= 2: print("Found tick function, exporting")
        content = memory[2]["tick"]
        with open(os.path.join(path, name, "data", name, "functions", "tick.mcfunction"), "w") as file:
            for line in content:
                file.write(line+"\n")
                commands += 1
        del memory[2]["tick"]


    if len(memory[2]) and verbose >= 2: print("Exporting other functions...")
    for function in memory[2]:
        content = memory[2][function]
        with open(os.path.join(path, name, "data", name, "functions", "%s.mcfunction"%function), "w") as file:
            for line in content:
                file.write(line+"\n")
                commands += 1
        
try:
    commands = 0
    
    argparser = get_argparser()
    args, unparsed = argparser.parse_known_args()
    if args.file == "":
        print(f"{Fore.RED}Error: no file specified{Style.RESET_ALL}")
        raise Exception("Abort")
    
    filename = args.file
    name = args.name
    description = args.description
    verbose = args.verbose
    
    if args.info_file != "":
        path = args.info_file
        if os.path.isfile(path):
            with open(path, "r") as file:
                config = {}
                for line in file.readlines():
                    split = line.replace("\n", "").split("=")
                    config[split[0]] = split[1]
                if "name" in config: name = config["name"]
                elif verbose >= 1: print(f"{Fore.YELLOW}Couldn't find 'name' parameter! Using default...\n{Style.RESET_ALL}")
                
                if "description" in config: description = config["description"].replace("\"", "\\\"")
                elif verbose >= 1: print(f"{Fore.YELLOW}Couldn't find 'description' parameter! Using default...\n{Style.RESET_ALL}")
        elif verbose >= 1:
            print(f"{Fore.YELLOW}Couldn't find the .info file! Using defaults...\n{Style.RESET_ALL}")

    path = parent(filename)
    path = os.path.join(path, "build")
    mkdir(path)
    
    distpath = os.path.join(parent(filename), "dist")
    mkdir(distpath)

    create_structure(name, description, path)
    memory = main(filename, name)
    
    assemble_pack(name, memory, path)

    shutil.make_archive(os.path.join(distpath, name), 'zip', os.path.join(path, name))
    if verbose >= 2:
        print("\nFinished building %s."%name)
        print("Total: %i commands"%commands)
    input("Press enter to continue...")
    
except Exception as e:
    if str(e) != "Abort":
        traceback.print_exc()
    input()
