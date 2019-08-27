from re import findall
from colorama import init, Style, Fore
from MineScriptVisitor import MineScriptVisitor
from MineScriptParser import MineScriptParser
import tags


approved_attrs = [
    "append",
    "pop",
    "remove",
    "sort"
    ]

error = f"{Fore.RED}Traceback: Line %i\n%s\n"
end = f"{Style.RESET_ALL}"
typeerror1 = "TypeError: Variable '%s' should be of type int or float, not %s"
typeerror2 = "TypeError: Object of type %s has no length"
typeerror3 = "TypeError: Indices should be of type int, not %s"
typeerror4 = "TypeError: Object of type %s is not callable"
typeerror5 = "TypeError: Unsupported operand types for %s: '%s' and '%s'"
typeerror6 = "TypeError: '%s' not supported between instances of '%s' and '%s'"
typeerror7 = "TypeError: float() argument must be a string or a number, not '%s'"
typeerror8 = "TypeError: Function argument must be a string or a number, not '%s'"
typeerror9 = "TypeError: Invalid type"
typeerror10 = "TypeError: Function %s() requires %s arguments, but %s were given"
nameerror = "NameError: Variable '%s' is not defined"
syntaxerror1 = "SyntaxError: invalid syntax"
syntaxerror2 = "SyntaxError: 'return' outside of function"
indexerror = "IndexError: List index %i is out of range"
attributeerror = "AttributeError: Object of type %s has no attribute %s"
valueerror1 = "ValueError: Could not convert to float: '%s'"
valueerror2 = "ValueError: Could not convert to int: '%s'"
valueerror3 = "ValueError: Selector not formatted correctly"

def add_to_selector(selector, args):
    tp = selector[:2]
    attributes = findall("\[([^]]+)\]", selector)[0].split(",")
    attributes = [attr.strip() for attr in attributes]
    for arg in args:
        if arg not in attributes:
            attributes.append(arg)
    return tp + "[" + ','.join(attributes) + "]"
    

class Visitor(MineScriptVisitor):
    def __init__(self, name, code):
        self.code = code            # The actual code
        self.datapack_name = name   # Name of the datapack
        self._commands = []         # List of commands to be added to the current function
        self.warnings = []          # List of warnings
        
        self.memory = {}            # Stores variables
        self.localmemory = {}       # Stores local variables
        self.functionargs = {}      # Stores the args a function takes
        self.func = None            # Current function
        self.r_value = None         # Stores the return variable of the current function

        self.igmemory = []          # Stores the in-game variable names
        self.igfunctionargs = {}    # Stores the args an igfunction takes
        self.igfunctionreturn = {}  # Stores the name of the return variable of a function
        self.igfunctions = {}       # Stores the functions to be turned into .mcfunction files
        self.igfunc = None          # Current igfunction

        self.vars = []              # Stores all the temporary variables currently in use
        self.nreusable = []         # Stores all non reusable variables
        self.igloops = {}           # Stores the loops to be turned into .mcfunction files
        self.loop = []              # Keeps track of loops
        self.prefixes = []          # Keeps track of if/else and execute statements
        self.loops = 0              # Loop ID
        self.tag = 0                # Tag ID     
        
        self.get_tags()             # Get all tags from file

    def add_var(self, name):  # Add a new in-game variable
        if name not in self.igmemory:
            self.igmemory.append(name)

    def mark_unused(self, var):  # Mark an in-game variable as unused
        name = int(var[4:])
        if var not in self.nreusable and name in self.vars:
            self.vars.remove(name)

    def mark_not_reusable(self, var):  # Mark an in-game variable as not reusable
        if var not in self.nreusable:
            self.nreusable.append(var)

    def get_var(self):  # Generate and return a new temporary variable
        n = self.get_next_var_id()
        name = f"_var{n}"
        self.add_var(name)
        self.vars.append(n)
        return name

    def get_next_var_id(self):  # Get the id of the next available variable
        if len(self.vars):
            for i in range(len(self.vars)):
                if self.vars[i] != i:
                    self.vars.insert(i, i)
                    return i
            return len(self.vars)
        return 0

    def add_func_arg(self, func, var, arg):
        if var not in self.igfunctionargs[func][0]:
            self.igfunctionargs[func][0].append(var)
        if var not in self.igfunctionargs[func][1]:
            self.igfunctionargs[func][1].append(arg)

    def add_warning(self, warning):  # Add a warning
        if warning not in self.warnings:
            self.warnings.append(warning)

    def get_tags(self):  # Get and load all tags
        for tag in tags.tags:
            self.memory[tag] = tags.tags[tag]

    def add_cmd(self, command, func=None):  # Add a command to the current function
        if self.prefixes != []:
            command = "execute " + ' '.join(self.prefixes) + " run " + command
        if self.loop != []:
            self.igloops[self.loop[-1]].append(command)
        elif func:
            self.igfunctions[func].append(command)
        else:
            self._commands.append(command)

    def add_loop(self, tp):  # Add a loop
        self.loops += 1
        self.loop.append(f"_{tp}{self.loops}")
        self.igloops[self.loop[-1]] = []

    def pop_loop(self):  # Pop latest loop
        self.loop.pop()

    def get_var_name(self, name):
        if self.igfunc:
            if name in self.igfunctionargs[self.igfunc][1]:
                index = self.igfunctionargs[self.igfunc][1].index(name)
                return self.igfunctionargs[self.igfunc][0][index]
            else:
                return name
        else:
            return name

    def add_prefix(self, cmd):  # Add prefix (if/else/execute statement)
        self.prefixes.append(cmd)

    def pop_prefix(self):  # Pop latest prefix
        self.prefixes.pop()
 
    def set_var(self, name, value):  # Set an in-game variable
        self.add_cmd(f"scoreboard players set MineScript {name} {value}")

    def igBoolOp(self, operation, left, right):
        unused = []
        
        if left[1] == "rt":
            l = self.get_var()
            unused.append(l)
            self.set_var(l, int(left[0]))
        elif left[1] == "ig": l = left[0]
        
        if right[1] == "rt":
            r = self.get_var()
            unused.append(r)
            self.set_var(r, int(right[0]))
        elif right[1] == "ig": r = right[0]

        result = self.get_var()
        self.set_var(result, 0)
        if operation == "&&":
            self.add_cmd(f"execute if score MineScript {l} matches 1.. if score MineScript {r} matches 1.. run scoreboard players set MineScript {result} 1")
        elif operation == "||":
            self.add_cmd(f"execute if score MineScript {l} matches 1.. run scoreboard players set MineScript {result} 1")
            self.add_cmd(f"execute if score MineScript {r} matches 1.. run scoreboard players set MineScript {result} 1")
            
        for var in unused:
            self.mark_unused(var)
            
        return result

    def igComparison(self, comparison, left, right):  # genexpr (< > <= >= == !=) genexpr
        unused = []
        if left[1] == "rt":
            l = self.get_var()
            unused.append(l)
            self.set_var(l, int(left[0]))
        elif left[1] == "ig": l = left[0]
        
        if right[1] == "rt":
            r = self.get_var()
            unused.append(r)
            self.set_var(r, int(right[0]))
        elif right[1] == "ig": r = right[0]

        result = self.get_var()
        if comparison == "==": comparison = "="
        if comparison == "!=":
            self.set_var(result, 0)
            self.add_cmd(f"execute unless score MineScript {l} = MineScript {r} run scoreboard players set MineScript {result} 1")
        else:
            self.set_var(result, 0)
            self.add_cmd(f"execute if score MineScript {l} {comparison} MineScript {r} run scoreboard players set MineScript {result} 1")

        for var in unused:
            self.mark_unused(var)
                             
        return result

    def igOperation(self, operation, left, right, result=None):  # genexpr (+-/*%) genexpr
        unused = []
        if result != None: self.set_var(result, 0)
        
        if operation == "^":
            if result is None: result = self.get_var()
            
            if right[1] == "rt" and left[1] == "ig":
                if right[0] == 0: self.set_var(result, 1)
                else:
                    self.add_cmd(f"scoreboard players operation MineScript {result} = MineScript {left[0]}")
                    for _ in range(right[0]-1):
                        self.add_cmd(f"scoreboard players operation MineScript {result} *= MineScript {left[0]}")
            elif right[1] == "ig":
                r = right[0]
                if left[1] == "rt":
                    l = self.get_var()
                    unused.append(l)
                    self.add_cmd(f"scoreboard players set MineScript {l} {int(left[0])}")
                elif left[1] == "ig": l = left[0]
                self.add_cmd(f"scoreboard players operation MineScript {result} = MineScript {l}")

                count = self.get_var()
                negative = self.get_var()
                unused.append(count)
                unused.append(negative)
                self.set_var(negative, -1)
                
                self.add_cmd(f"scoreboard players operation MineScript {count} = MineScript {r}")
                self.add_cmd(f"execute if score MineScript {count} matches ..-1 run scoreboard players operation MineScript {count} *= MineScript {negative}")
                
                self.add_cmd(f"scoreboard players remove MineScript {count} 1")
                loop = "_pow" + str(self.loops+1)
                self.add_cmd(f"execute if score MineScript {count} matches 1.. run function {self.datapack_name}:{loop}")
                self.add_loop("pow")
                self.add_cmd(f"scoreboard players operation MineScript {result} *= MineScript {l}")
                self.add_cmd(f"scoreboard players remove MineScript {count} 1")
                self.add_cmd(f"execute if score MineScript {count} matches 1.. run function {self.datapack_name}:{loop}")
                self.pop_loop()
                self.add_cmd(f"execute if score MineScript {r} matches 0 run scoreboard players set MineScript {result} 1")

                unit = self.get_var()
                unused.append(unit)
                self.set_var(unit, 1)
                
                self.add_cmd(f"execute if score MineScript {r} matches ..-1 run scoreboard players operation MineScript {unit} /= MineScript {result}")
                self.add_cmd(f"execute if score MineScript {r} matches ..-1 run scoreboard players operation MineScript {result} = MineScript {unit}")                   
        else:
            if left[1] == "rt":
                l = self.get_var()
                unused.append(l)
                self.set_var(l, int(left[0]))
            elif left[1] == "ig": l = left[0]
            
            if right[1] == "rt":
                r = self.get_var()
                unused.append(r)
                self.set_var(r, int(right[0]))
            elif right[1] == "ig": r = right[0]

            if result is None: result = self.get_var()
            self.add_cmd(f"scoreboard players operation MineScript {result} = MineScript {l}")
            self.add_cmd(f"scoreboard players operation MineScript {result} {operation}= MineScript {r}")

        for var in unused:
            self.mark_unused(var)

        return result
         
    def visitIgAssign(self, ctx):  # Expression of type $var = expression
        name = ctx.ID().getText()
        value = self.visitChildren(ctx)
        if type(value) == int or type(value) == float:
            self.add_var(name)
            self.add_cmd(f"scoreboard players set MineScript {name} {round(value)}")
        else:
            print((error+typeerror+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, value.__class__.__name__))
            raise Exception("Abort")
        return name

    def visitIgAssignIg(self, ctx):  # Expression of type $var = $expression
        name1 = self.get_var_name(ctx.ID().getText())
        name2 = self.get_var_name(self.visitChildren(ctx))

        if not name1.startswith("_") and name1 not in self.igmemory:
            self.add_warning(f"{Fore.YELLOW}Warning: Variable {name1} referenced without assignement in line {ctx.start.line}{Style.RESET_ALL}")
        if not name2.startswith("_") and name2 not in self.igmemory:
            self.add_warning(f"{Fore.YELLOW}Warning: Variable {name2} referenced without assignement in line {ctx.start.line}{Style.RESET_ALL}")
            
        self.add_var(name1)
        self.add_cmd(f"scoreboard players operation MineScript {name1} = MineScript {name2}")
        
        if name2.startswith("_"): self.mark_unused(name2)
        
        return name1

    def visitIgAssignUnit(self, ctx):  # Expression of type $var++
        name = self.get_var_name(ctx.ID().getText())
        
        if not name.startswith("_") and name not in self.igmemory:
            self.add_warning(f"{Fore.YELLOW}Warning: Variable {name} referenced without assignement in line {ctx.start.line}{Style.RESET_ALL}")
                         
        if ctx.op.type == MineScriptParser.USUM: self.add_cmd(f"scoreboard players add MineScript {name} 1")
        elif ctx.op.type == MineScriptParser.USUB: self.add_cmd(f"scoreboard players remove MineScript {name} 1")
        return name

    def visitIgAssignOp(self, ctx):  # Expression of type $var (*/+-%)= expression
        name = self.get_var_name(ctx.ID().getText())
        value = self.visitChildren(ctx)

        if not name.startswith("_") and name not in self.igmemory:
            self.add_warning(f"{Fore.YELLOW}Warning: Variable {name} referenced without assignement in line {ctx.start.line}{Style.RESET_ALL}")

        if not(type(value) == int or type(value) == float):
            print((error+typeerror5+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), ctx.op.text, "int", value.__class__.__name__))
            raise Exception("Abort")
    
        self.igOperation(ctx.op.text[0], (name, "ig"), (value, "rt"), name)
                
        return name

    def visitIgAssignIgOp(self, ctx):  # Expression of type $var (*/+-%)= $expression
        name1 = self.get_var_name(ctx.ID().getText())
        name2 = self.get_var_name(self.visitChildren(ctx))

        if not name1.startswith("_") and name1 not in self.igmemory:
            self.add_warning(f"{Fore.YELLOW}Warning: Variable {name1} referenced without assignement in line {ctx.start.line}{Style.RESET_ALL}")
        if not name2.startswith("_") and name2 not in self.igmemory:
            self.add_warning(f"{Fore.YELLOW}Warning: Variable {name2} referenced without assignement in line {ctx.start.line}{Style.RESET_ALL}")
        
        self.igOperation(ctx.op.text[0], (name1, "ig"), (name2, "ig"), name1)
        
        if name2.startswith("_"): self.mark_unused(name2)

    def visitIgParens(self, ctx):  # Expression of type ( $expression )
        return self.visit(ctx.igexpr())

    def visitIgOpIg(self, ctx):  # Expression of type $expression (*/+-%^) $expression
        name1 = self.get_var_name(self.visit(ctx.igexpr(0)))
        name2 = self.get_var_name(self.visit(ctx.igexpr(1)))

        if not name1.startswith("_") and name1 not in self.igmemory:
            self.add_warning(f"{Fore.YELLOW}Warning: Variable {name1} referenced without assignement in line {ctx.start.line}{Style.RESET_ALL}")
        if not name2.startswith("_") and name2 not in self.igmemory:
            self.add_warning(f"{Fore.YELLOW}Warning: Variable {name2} referenced without assignement in line {ctx.start.line}{Style.RESET_ALL}")
        
        result = self.igOperation(ctx.op.text, (name1, "ig"), (name2, "ig"))

        if name1.startswith("_"): self.mark_unused(name1)
        if name2.startswith("_"): self.mark_unused(name2)

        return result

    def visitIgOp(self, ctx, reverse=False):  # Expression of type $expression (*/+-%^) expression
        name = self.get_var_name(self.visit(ctx.igexpr()))
        value = self.visit(ctx.expr())

        if not(type(value) == int or type(value) == float):
            print((error+typeerror1+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, value.__class__.__name__))
            raise Exception("Abort")

        if not reverse: result = self.igOperation(ctx.op.text, (name, "ig"), (value, "rt"))
        else: result = self.igOperation(ctx.op.text, (value, "rt"), (name, "ig"))

        if name.startswith("_"): self.mark_unused(name)
            
        return result

    def visitIgOpM(self, ctx):  # Expression of type expression (*/+-%^) $var
        return self.visitIgOp(ctx, True)

    def visitIgNot(self, ctx):  # Expression of type !$expression
        name = self.get_var_name(self.visit(ctx.igexpr()))
        result = self.get_var()
        self.set_var(result, 0)
        self.add_cmd(f"execute unless score MineScript {name} matches 1.. run scoreboard players set MineScript {result} 1")

        if name.startswith("_"): self.mark_unused(name)
        
        return result

    def visitIgBoolOp(self, ctx):  # Expression of type genexpr &&/|| genexpr
        if len(ctx.igexpr()) == 1:
            expr1 = self.visit(ctx.igexpr(0)), "ig"
            expr2 = self.visit(ctx.expr()), "rt"
        else:
            expr1 = self.visit(ctx.igexpr(0)), "ig"
            expr2 = self.visit(ctx.igexpr(1)), "ig"
        result = self.igBoolOp(ctx.op.text, expr1, expr2)

        if expr1[0].startswith("_"): self.mark_unused(expr1[0])
        if len(ctx.igexpr()) > 1 and expr2[0].startswith("_"): self.mark_unused(expr2[0])
        
        return result

    def visitIgComparison(self, ctx, reverse=False):  # Expression of type $expression (> < <= >= != ==) expression
        name = self.get_var_name(self.visit(ctx.igexpr()))
        value = self.visit(ctx.expr())

        if not(type(value) == int or type(value) == float):
            print((error+typeerror1+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, value.__class__.__name__))
            raise Exception("Abort")
        
        if not reverse:
            result = self.igComparison(ctx.op.text, (name, "ig"), (value, "rt"))
        else:
            result = self.igComparison(ctx.op.text, (value, "rt"), (name, "ig"))

        if name.startswith("_"): self.mark_unused(name)
        
        return result

    def visitIgComparisonM(self, ctx):  # Expression of type expression (> < <= >= != ==) $expression
        return self.visitIgComparison(ctx, reverse=True)

    def visitExecute(self, ctx):  # Expression of type $execute(execute){ stat }
        execute = str(self.visit(ctx.expr()))
        stat = ctx.stat()
        self.add_prefix(execute)
        self.visit(stat)
        self.pop_prefix()

    def visitIgComparisonIg(self, ctx):  # Expression of type $expression (> < <= >= != ==) $expression
        name1 = self.get_var_name(self.visit(ctx.igexpr(0)))
        name2 = self.get_var_name(self.visit(ctx.igexpr(1)))

        if not name1.startswith("_") and name1 not in self.igmemory:
            self.add_warning(f"{Fore.YELLOW}Warning: Variable {name1} referenced without assignement in line {ctx.start.line}{Style.RESET_ALL}")
        if not name2.startswith("_") and name2 not in self.igmemory:
            self.add_warning(f"{Fore.YELLOW}Warning: Variable {name2} referenced without assignement in line {ctx.start.line}{Style.RESET_ALL}")
        
        result = self.igComparison(ctx.op.text, (name1, "ig"), (name2, "ig"))

        if name1.startswith("_"): self.mark_unused(name1)
        if name2.startswith("_"): self.mark_unused(name2)
        
        return result

    def visitIgIfElse(self, ctx):  # Expression of type $if ($expression) { stat } ($else { stat })?
        name = self.get_var_name(self.visit(ctx.igexpr()))
        
        self.add_prefix(f"if score MineScript {name} matches 1..")
        self.visit(ctx.stat(0))
        self.pop_prefix()
        
        if ctx.stat(1) is not None:
            self.add_prefix(f"unless score MineScript {name} matches 1..")
            self.visit(ctx.stat(1))
            self.pop_prefix()

        if name.startswith("_"): self.mark_unused(name)

    def visitGetPos(self, ctx):  # Expression of type $pos(selector, index)
        selector = str(self.visit(ctx.expr(0)))
        coord = self.visit(ctx.expr(1))

        if not type(coord) == int:
            print((error+typeerror3+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), coord.__class__.__name__))
            raise Exception("Abort")
        
        result = self.get_var()
        self.set_var(result, 0)

        if coord == 0: self.add_cmd(f"execute store result score MineScript {result} run data get entity {selector} Pos[0]")
        elif coord == 1: self.add_cmd(f"execute store result score MineScript {result} run data get entity {selector} Pos[1]")
        elif coord == 2: self.add_cmd(f"execute store result score MineScript {result} run data get entity {selector} Pos[2]")

        return result

    def visitGetData(self, ctx):  # Expression of type $getdata(selector, path, scale?)
        selector = str(self.visit(ctx.expr(0)))
        path = str(self.visit(ctx.expr(1)))

        result = self.get_var()
        self.set_var(result, 0)

        if ctx.expr(2) is not None:
            scale = self.visit(ctx.expr(2))
            
            if type(scale) == int or type(scale) == float:
                value = int(scale)
            else:
                print((error+s+end)%(ctx.start.line, self.code[ctx.start.line-1]))
                raise Exception("Abort")
            
            self.add_cmd(f"execute store result score MineScript {result} run data get entity {selector} {path} {scale}")
        else:
            self.add_cmd(f"execute store result score MineScript {result} run data get entity {selector} {path}")

        return result

    def visitSetData(self, ctx):
        selector = str(self.visit(ctx.expr(0)))
        selector = add_to_selector(selector, ["limit=1"])
        path = str(self.visit(ctx.expr(1)))

        if ctx.genexpr().expr() is not None:
            value = self.visit(ctx.genexpr().expr())
            self.add_cmd(f"data modify entity {selector} {path} set value {value}")
        else:
            name = self.get_var_name(self.visit(ctx.genexpr().igexpr()))
            self.add_cmd(f"execute store result entity {selector} {path} double 1 run scoreboard players get MineScript {name}")
            if name.startswith("_"): self.mark_unused(name)

    def visitIsBlock(self, ctx):  # Expression of type $isblock(selector, pos, block)
        selector = str(self.visit(ctx.expr(0)))
        relpos = str(self.visit(ctx.expr(1)))
        block = str(self.visit(ctx.expr(2)))
        
        result = self.get_var()
        self.set_var(result, 0)
        self.add_cmd(f"execute at {selector} if block {relpos} {block} run scoreboard players set MineScript {result} 1")

        return result

    def visitAddObj(self, ctx):
        name = str(self.visit(ctx.expr(0)))
        tp = str(self.visit(ctx.expr(1)))

        self.add_cmd(f"scoreboard objectives add {name} {tp}")

    def visitGetScore(self, ctx):  # Expression of type $getscore(selector, name)
        selector = str(self.visit(ctx.expr(0)))
        name = str(self.visit(ctx.expr(1)))

        result = self.get_var()        
        self.add_cmd(f"scoreboard players operation MineScript {result} = {selector} {name}")
        
        return result

    def visitSetScore(self, ctx):  # Expression of type $setscore(selector, name, value)
        selector = str(self.visit(ctx.expr(0)))
        name = str(self.visit(ctx.expr(1)))
        ge = ctx.genexpr()

        if ge.expr() is not None:
            value = self.visit(ge.expr())

            if not type(value) == int:
                print((error+typeerror1+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, value.__class__.__name__))
                raise Exception("Abort")
                                
            v = self.get_var()
            
            self.add_cmd(f"scoreboard players set MineScript {v} {value}")
            self.add_cmd(f"scoreboard players operation {selector} {name} = MineScript {v}")
            
        elif ge.igexpr() is not None:
            name2 = self.get_var_name(self.visit(ge.igexpr()))
            self.add_cmd(f"scoreboard players operation {selector} {name} = MineScript {name2}")
            if name2.startswith("_"): self.mark_unused(name2)

    def visitAddTag(self, ctx):  # Expression of type $addtag(selector, tag)
        selector = str(self.visit(ctx.expr(0)))
        name = str(self.visit(ctx.expr(1)))

        self.add_cmd(f"tag {selector} add {name}")

    def visitRemTag(self, ctx):  # Expression of type $remtag(selector, tag)
        selector = str(self.visit(ctx.expr(0)))
        name = str(self.visit(ctx.expr(1)))

        self.add_cmd(f"tag {selector} remove {name}")

    def visitHasTag(self, ctx):  # Expression of type $hastag(selector, tag)
        selector = str(self.visit(ctx.expr(0)))
        name = str(self.visit(ctx.expr(1)))

        result = self.get_var()
        self.set_var(result, 0)

        self.add_cmd(f"scoreboard players set MineScript {result} 0")
        self.add_cmd(f"execute as {selector} at @s[tag={name}] run scoreboard players set MineScript {result} 1")

        return result

    def visitCount(self, ctx):  # Expression of type $count(selector)
        selector = str(self.visit(ctx.expr()))
        
        if not selector.startswith("@"):
            print((error+valueerror3+end)%(ctx.start.line, self.code[ctx.start.line-1].strip()))
            raise Exception("Abort")

        result = self.get_var()
        self.set_var(result, 0)
        self.add_cmd(f"execute as {selector} run scoreboard players add MineScript {result} 1")

        return result

    def visitIgWhile(self, ctx): # Expression of type $while (genexpr) { stat }
        stats = ctx.stat()
        expr = ctx.genexpr()

        if expr.expr() is not None:
            value = self.visit(expr.expr())
            if type(value) == int or type(value) == float or type(value) == bool:
                value = int(value)
            else:
                print((error+s+end)%(ctx.start.line, self.code[ctx.start.line-1]))
                raise Exception("Abort")
            
            v = self.get_var()
            self.add_cmd(f"scoreboard players set MineScript {v} {value}")
            expr_n = self.visit(expr.expr())

            loop = "_while" + str(self.loops+1)
            self.add_cmd(f"execute if score MineScript {expr_n} matches 1.. run function {self.datapack_name}:{loop}")

            self.add_loop("while")
            self.visit(stats)
            
        elif expr.igexpr() is not None:           
            expr_n = self.get_var_name(self.visit(expr.igexpr()))

            loop = "_while" + str(self.loops+1)
            self.add_cmd(f"execute if score MineScript {expr_n} matches 1.. run function {self.datapack_name}:{loop}")
            self.add_loop("while")
            self.visit(stats)
            expr_n = self.visit(expr.igexpr())
            
        self.add_cmd(f"execute if score MineScript {expr_n} matches 1.. run function {self.datapack_name}:{loop}")
        self.pop_loop()
        if expr.igexpr() is not None and expr_n.startswith("_"): self.mark_unused(expr_n)        

    def visitIgFor(self, ctx):  # Expression of type $for ($forInit; $forTest; $forUpdate) { stat }
        stats = ctx.stat()
        init = ctx.igForControl().igForInit()
        expr = ctx.igForControl().igexpr()
        update = ctx.igForControl().igForUpdate()
        init_n = self.visit(init)
        expr_n = self.get_var_name(self.visit(expr))

        loop = "_for" + str(self.loops+1)
        self.add_cmd(f"execute if score MineScript {expr_n} matches 1.. run function {self.datapack_name}:{loop}")
        
        self.add_loop("for")
        self.visit(stats)
        self.visit(update)
        expr_n = self.visit(expr)
        self.add_cmd(f"execute if score MineScript {expr_n} matches 1.. run function {self.datapack_name}:{loop}")
        self.pop_loop()
        if expr_n.startswith("_"): self.mark_unused(expr_n) 

    def visitIgForEntity(self, ctx):  # Expression of type $forentity(selector; new_var) { stat }
        unused = []
        
        selector = str(self.visit(ctx.expr()))
        name = ctx.ID().getText()
        stats = ctx.stat()

        self.tag += 1
        value = add_to_selector(selector, ["limit=1", f"tag=!_tag{self.tag}"])
        self.memory[name] = value

        count_d = self.get_var()
        unused.append(count_d)
        self.add_cmd(f"scoreboard players set MineScript {count_d} 0")
        self.add_cmd(f"execute as {selector} run scoreboard players add MineScript {count_d} 1")
        
        count = self.get_var()
        unused.append(count)
        self.add_cmd(f"scoreboard players set MineScript {count} 0")
        self.add_cmd(f"scoreboard players operation MineScript {count} = MineScript {count_d}")

        loop = "_for" + str(self.loops+1)
        self.add_cmd(f"execute if score MineScript {count} matches 1.. run function {self.datapack_name}:{loop}")
        
        self.add_loop("for")
        self.visit(stats)
        self.add_cmd(f"tag {value} add _tag{self.tag}")

        self.add_cmd(f"scoreboard players remove MineScript {count} 1")
        self.add_cmd(f"execute if score MineScript {count} matches 1.. run function {self.datapack_name}:{loop}")
        self.pop_loop()

        self.add_cmd(f"tag {selector} remove _tag{self.tag}")

        for var in unused:
            self.mark_unused(var)
            
    def visitSetDisplay(self, ctx):  # Expression of type $setdisplay(var, mode)
        name = self.get_var_name(self.visit(ctx.igexpr()))
        mode = ctx.DSPL_MODE().getText()
        self.add_cmd(f"scoreboard objectives setdisplay {mode} {name}")
        if name.startswith("_"): self.mark_unused(name)

    def visitCommand(self, ctx):  # Expression of type $mc(expression)
        exp = str(self.visit(ctx.expr()))
        self.add_cmd(exp)
        
    def visitIgPrint(self, ctx):  # Expression of type $print(genexpression,...| COLOR)
        text = []
        for child in ctx.igPrintControl().igPrintArg():
            e = child.genexpr()
            if child.COLOR() is not None: color = child.COLOR().getText()
            else: color = "white"
            
            if e.expr() is not None:
                value = str(self.visit(e.expr()))
                text.append("{\"text\":\"%s\",\"color\":\"%s\"}"%(value, color))
            elif e.igexpr() is not None:
                name = self.get_var_name(self.visit(e.igexpr()))
                text.append("{\"score\":{\"name\":\"MineScript\",\"objective\":\"%s\"},\"color\":\"%s\"}"%(name, color))
                if name.startswith("_"): self.mark_unused(name)
                
        self.add_cmd("tellraw @a ["+','.join(text)+"]")

    def visitTeleport(self, ctx):  # Expression of type $tp(selector, pos)
        selector = str(self.visit(ctx.expr(0)))
        pos = str(self.visit(ctx.expr(1)))
        self.add_cmd(f"execute as {selector} at @s run tp @s {pos}")

    def visitIgFuncDef(self, ctx):  # Expression of type $function func { stat }        
        name = ctx.ID(0).getText()
        stats = ctx.stat()
        args = ctx.ID()[1:]
        self.igfunctionargs[name] = [[], []]
        r_var = self.get_var()
        self.mark_not_reusable(r_var)
        self.igfunctionreturn[name] = r_var
        
        for arg in args:
            var = self.get_var()
            self.mark_not_reusable(var)
            self.add_func_arg(name, var, arg.getText())
            
        self.igfunc = name
        self.visit(stats)
        self.igfunc = None
        self.igfunctions[name] = self._commands[:]
        self._commands = []

    def visitIgFuncCall(self, ctx):  # Expression of type $func()
        name = ctx.ID().getText()
        variables = ctx.genexpr()
        
        if not name in self.igfunctions:
            print((error+nameerror+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name))
            raise Exception("Abort")

        if len(variables) != len(self.igfunctionargs[name][0]):
            print((error+typeerror10+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, len(self.igfunctionargs[name]), len(variables)))
            raise Exception("Abort")
        
        for var in range(len(variables)):
            if variables[var].expr():
                self.set_var(self.igfunctionargs[name][0][var], int(self.visit(variables[var])))
            else:
                n = self.visit(variables[var])
                if not n.startswith("_") and n not in self.igmemory:
                    self.add_warning(f"{Fore.YELLOW}Warning: Variable {n} referenced without assignement in line {ctx.start.line}{Style.RESET_ALL}")
                self.add_cmd(f"scoreboard players operation MineScript {self.igfunctionargs[name][0][var]} = MineScript {n}")
        self.add_cmd(f"function {self.datapack_name}:{name}")

        return self.igfunctionreturn[name]

    def visitIgReturn(self, ctx):
        if self.igfunc:
            r_value = self.get_var_name(self.visit(ctx.igexpr()))
            self.add_cmd(f"scoreboard players operation MineScript {self.igfunctionreturn[self.igfunc]} = MineScript {r_value}")
        else:
            print((error+syntaxerror2+end)%(ctx.start.line, self.code[ctx.start.line-1].strip()))
            raise Exception("Abort")

    def visitIgId(self, ctx):  # Expression of type $var
        name = self.get_var_name(ctx.ID().getText())
        return name

    def visitAssign(self, ctx):  # Expression of type var = expression
        name = ctx.ID().getText()
        value = self.visit(ctx.expr())
        if self.func: self.localmemory[name] = value
        else: self.memory[name] = value
        return value

    def visitAssignUnit(self, ctx):  # Expression of type var++
        name = ctx.ID().getText()
        try:
            if ctx.op.type == MineScriptParser.USUM: self.localmemory[name] += 1
            elif ctx.op.type == MineScriptParser.USUB: self.localmemory[name] -= 1
        except TypeError:
            print((error+typeerror1+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, self.localmemory[name].__class__.__name__))
            raise Exception("Abort")
        except KeyError:
            try:
                if ctx.op.type == MineScriptParser.USUM: self.memory[name] += 1
                elif ctx.op.type == MineScriptParser.USUB: self.memory[name] -= 1
            except TypeError:
                print((error+typeerror1+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, self.memory[name].__class__.__name__))
                raise Exception("Abort")
            except KeyError:
                print((error+nameerror+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name))
                raise Exception("Abort")

    def visitAssignOp(self, ctx):  # Expression of type var (*/+-%^)= expression
        name = ctx.ID().getText()
        value = self.visit(ctx.expr())
        try:
            if ctx.op.type == MineScriptParser.PE: self.localmemory[name] += value
            elif ctx.op.type == MineScriptParser.SE: self.localmemory[name] -= value
            elif ctx.op.type == MineScriptParser.MLE: self.localmemory[name] *= value
            elif ctx.op.type == MineScriptParser.DE: self.localmemory[name] /= value
            elif ctx.op.type == MineScriptParser.MDE: self.localmemory[name] %= value
            elif ctx.op.type == MineScriptParser.PWE: self.localmemory[name] = self.localmemory[name] ** value
        except TypeError:
            print((error+typeerror1+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, self.localmemory[name].__class__.__name__))
            raise Exception("Abort")
        except KeyError:
            try:
                if ctx.op.type == MineScriptParser.PE: self.memory[name] += value
                elif ctx.op.type == MineScriptParser.SE: self.memory[name] -= value
                elif ctx.op.type == MineScriptParser.MLE: self.memory[name] *= value
                elif ctx.op.type == MineScriptParser.DE: self.memory[name] /= value
                elif ctx.op.type == MineScriptParser.MDE: self.memory[name] %= value
                elif ctx.op.type == MineScriptParser.PWE: self.memory[name] = self.memory[name] ** value
            except TypeError:
                print((error+typeerror1+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, self.memory[name].__class__.__name__))
                raise Exception("Abort")
            except KeyError:
                print((error+nameerror+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name))
                raise Exception("Abort")

    def visitNegative(self, ctx):
        return -int(ctx.number().getText())

    def visitNot(self, ctx):  # Expression of type !var
        value = self.visit(ctx.expr())
        return not value

    def visitFuncDef(self, ctx):  # Expression of type function func() { stat }
        name = ctx.ID(0).getText()
        value = ctx.stat()
        self.functionargs[name] = []
        for arg in ctx.ID()[1:]:
            self.functionargs[name].append(arg.getText())
        if self.func: self.localmemory[name] = value
        else: self.memory[name] = value

    def visitFuncCall(self, ctx):  # Expression of type func()
        self.r_value = None
        name = ctx.ID().getText()
        args = ctx.expr()
        if len(args) != len(self.functionargs[name]):
            print((error+typeerror10+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, len(self.functionargs[name]), len(args)))
            raise Exception("Abort")
        for arg in range(len(args)):
            self.localmemory[self.functionargs[name][arg]] = self.visit(args[arg])
        if name in self.memory:
            self.func = name
            r = self.visit(self.memory[name])
            self.localmemory = {}
            self.func = None
            return self.r_value
        else:
            print((error+nameerror+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name))
            raise Exception("Abort")

    def visitReturn(self, ctx):
        if self.func:
            self.r_value = self.visit(ctx.expr())
            return self.r_value
        else:
            print((error+syntaxerror2+end)%(ctx.start.line, self.code[ctx.start.line-1].strip()))
            raise Exception("Abort")

    def visitPrint(self, ctx):  # Expression of type print(expression,...)
        exprs = ctx.expr()
        values = []
        for expr in exprs:
            values.append(str(self.visit(expr)))
        print(' '.join(values))

    def visitLen(self, ctx):  # Expression of type len(expression)
        value = self.visit(ctx.expr())
        try:
            return len(value)
        except TypeError:
            print((error+typeerror2+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__))
            raise Exception("Abort")

    def visitAbs(self, ctx):  # Expression of type abs(expression)
        value = self.visit(ctx.expr())
        try:
            return abs(value)
        except TypeError:
            print((error+typeerror8+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__))
            raise Exception("Abort")

    def visitInt(self, ctx):  # Expression of type int(expression)
        value = self.visit(ctx.expr())
        try:
            return int(value)
        except TypeError:
            print((error+typeerror8+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__))
            raise Exception("Abort")
        except ValueError:
            print((error+valueerror2+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), value))
            raise Exception("Abort")  

    def visitFloat(self, ctx):  # Expression of type float(expression)
        value = self.visit(ctx.expr())
        try:
            return float(value)
        except TypeError:
            print((error+typeerror7+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__))
            raise Exception("Abort")
        except ValueError:
            print((error+valueerror1+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), value))
            raise Exception("Abort")            

    def visitStr(self, ctx):  # Expression of type str(expression)
        value = self.visit(ctx.expr())
        return str(value)

    def visitConstant(self, ctx):  # Expression of type int, float, string or boolean
        value = ctx.literal().getText()
        if value.isdigit():
            return int(value)
        elif value == "true":
            return True
        elif value == "false":
            return False
        elif value[0] == "\"" and value[-1] == "\"":
            return value[1:-1]
        else:
            try:
                value = float(value)
                return value
            except ValueError:
                print((error+syntaxerror1+end)%(ctx.start.line, self.code[ctx.start.line-1].strip()))
                raise Exception("Abort")

    def visitConstantArray(self, ctx):  # Expression of type array (=list) [expression,...]
        values = []
        exprs = ctx.array().expr()
        for expr in exprs:
            values.append(self.visit(expr))
        return values

    def visitArrayIndex(self, ctx):  # Expression of type array[expression]
        index = self.visit(ctx.expr(1))
        value = self.visit(ctx.expr(0))
        try:
            return value[index]
        except IndexError:
            print((error+indexerror+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), index))
            raise Exception("Abort")
        except TypeError:
            print((error+typeerror3+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), index.__class__.__name__))
            raise Exception("Abort")

    def visitAttribute(self, ctx):  # Expression of type expression.attr
        value = self.visit(ctx.expr())
        attr = ctx.ID().getText()
        try:
            return getattr(value, attr)
        except AttributeError:
            print((error+attributeerror+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__, attr))
            raise Exception("Abort")

    def visitAttributeCallEmpty(self, ctx):  # Expression of type expression.attr()
        value = self.visit(ctx.expr())
        attr = ctx.ID().getText()
        try:
            if attr not in approved_attrs:
                raise AttributeError()
            return getattr(value, attr)()
        except AttributeError:
            print((error+attributeerror+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__, attr))
            raise Exception("Abort")
        except TypeError:
            print((error+typeerror4+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), getattr(value, attr).__class__.__name__))
            raise Exception("Abort")

    def visitAttributeCall(self, ctx):  # Expression of type expression.attr(expression)
        value = self.visit(ctx.expr(0))
        attr = ctx.ID().getText()
        expr = self.visit(ctx.expr(1))
        try:
            if attr not in approved_attrs:
                raise AttributeError()
            return getattr(value, attr)(expr)
        except AttributeError:
            print((error+attributeerror+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__, attr))
            raise Exception("Abort")
        except TypeError:
            print((error+typeerror4+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), getattr(value, attr).__class__.__name__))
            raise Exception("Abort")

    def visitId(self, ctx):  # Expression of type var
        name = ctx.ID().getText()
        if name in self.localmemory:
            return self.localmemory[name]
        elif name in self.memory:
            return self.memory[name]
        else:
            print((error+nameerror+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), name))
            raise Exception("Abort")
        return 0

    def visitOp(self, ctx):  # Expression of type expression (+-/*%) expression
        left = self.visit(ctx.expr(0))
        right = self.visit(ctx.expr(1))
        try:
            if ctx.op.type == MineScriptParser.MUL: return left * right
            elif ctx.op.type == MineScriptParser.DIV: return left / right
            elif ctx.op.type == MineScriptParser.ADD: return left + right
            elif ctx.op.type == MineScriptParser.SUB: return left - right
            elif ctx.op.type == MineScriptParser.MOD: return left % right
            elif ctx.op.type == MineScriptParser.POW: return left ** right
        except TypeError:
            print((error+typeerror5+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), ctx.op.text, left.__class__.__name__, right.__class__.__name__))
            raise Exception("Abort")

    def visitComparison(self, ctx):  # Expression of type expression (> < <= >= != ==) expression
        left = self.visit(ctx.expr(0))
        right = self.visit(ctx.expr(1))
        try:
            if ctx.op.type == MineScriptParser.GT:
                return left > right
            elif ctx.op.type == MineScriptParser.LT:
                return left < right
            elif ctx.op.type == MineScriptParser.GET:
                return left >= right
            elif ctx.op.type == MineScriptParser.LET:
                return left <= right
            elif ctx.op.type == MineScriptParser.DIF:
                return left != right
            elif ctx.op.type == MineScriptParser.EQ:
                return left == right
        except TypeError:
            print((error+typeerror6+end)%(ctx.start.line, self.code[ctx.start.line-1].strip(), ctx.op.text, left.__class__.__name__, right.__class__.__name__))
            raise Exception("Abort")

    def visitParens(self, ctx):  # Expression of type (expression)
        return self.visit(ctx.expr())

    def visitFor(self, ctx):  # Expression of type for (forInit; forTest; forUpdate) { stat }
        stats = ctx.stat()
        init = ctx.forControl().forInit()
        expr = ctx.forControl().expr()
        update = ctx.forControl().forUpdate()
        self.visit(init)
        while self.visit(expr):
            self.visit(stats)
            self.visit(update)

    def visitWhile(self, ctx):  # Expression of type while ($expression) { stat }
        stats = ctx.stat()
        expr = ctx.expr()

        while self.visit(expr):
            self.visit(stats)

    def visitIfElse(self, ctx):  # Expression of type if (expression) { stat } (else { stat })?
        value = self.visit(ctx.expr())
        if value:
            self.visit(ctx.stat(0))
        elif ctx.stat(1) is not None:
            self.visit(ctx.stat(1))
