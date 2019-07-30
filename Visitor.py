from MineScriptVisitor import MineScriptVisitor
from MineScriptParser import MineScriptParser
import re


approved_attrs = [
    "append",
    "pop",
    "remove",
    "sort"
    ]


typeerror1 = """Traceback: Line %i
%s
TypeError: Variable '%s' should be of type int or float, not %s"""

typeerror2 = """Traceback: Line %i
%s
TypeError: Object of type %s has no length"""

typeerror3 = """Traceback: Line %i
%s
TypeError: Indices should be of type int, not %s"""

typeerror4 = """Traceback: Line %i
%s
TypeError: Object of type %s is not callable"""

typeerror5 = """Traceback: Line %i
%s
TypeError: Unsupported operand types for %s: '%s' and '%s'"""

typeerror6 = """Traceback: Line %i
%s
TypeError: '%s' not supported between instances of '%s' and '%s'"""

typeerror7 = """Traceback: Line %i
%s
TypeError: float() argument must be a string or a number, not '%s'"""

typeerror8 = """Traceback: Line %i
%s
TypeError: int() argument must be a string or a number, not '%s'"""

nameerror = """Traceback: Line %i
%s
NameError: Variable '%s' is not defined"""

syntaxerror = """Traceback: Line %i
%s
SyntaxError: invalid syntax"""

indexerror = """Traceback: Line %i
%s
IndexError: List index %i is out of range"""

attributeerror = """Traceback: Line %i
%s
AttributeError: Object of type %s has no attribute %s"""

valueerror1 = """Traceback: Line %i
%s
ValueError: Could not convert to float: '%s'"""

valueerror2 = """Traceback: Line %i
%s
ValueError: Could not convert to int: '%s'"""

valueerror3 = """Traceback: Line %i
%s
ValueError: Selector not formatted correctly"""


def add_to_selector(selector, args):
    tp = selector[:2]
    attributes = re.findall("\[([^]]+)\]", selector)[0].split(",")
    attributes = [attr.strip() for attr in attributes]
    for arg in args:
        if arg not in attributes:
            attributes.append(arg)
    return tp + "[" + ','.join(attributes) + "]"
    

class Visitor(MineScriptVisitor):
    def __init__(self, name, code):
        self.code = code
        self.memory = {}
        self.igfunctions = {}
        self.igmemory = {}
        self.igloops = {}
        self.loop = []
        self.execute = []
        self.loops = 0
        self.temp = 0
        self.tag = 0
        self.temp_arr = 0
        self._commands = []
        self.if_stat = None
        self.datapack_name = name

    def add_cmd(self, command):
        if self.if_stat is not None:
            command = self.if_stat + " run " + command
        if self.execute != []:
            for i in range(len(self.execute)):
                pre = ""
                pos = ""
                if i == len(self.execute)-1: pos = " run"
                if i == 0: pre = "execute "
                command = pre + self.execute[i] + pos + " " + command          
        if self.loop != []:
            self.igloops[self.loop[-1]].append(command)
        else:
            self._commands.append(command)

    def add_loop(self):
        self.loops += 1
        self.loop.append("_for%i"%self.loops)
        self.igloops[self.loop[-1]] = []

    def pop_loop(self):
        self.loop.pop()

    def add_exec(self, cmd):
        self.execute.append(cmd)

    def pop_exec(self):
        self.execute.pop()
         
    def visitIgAssign(self, ctx):  # Expression of type $var = expression
        name = ctx.ID().getText()
        value = self.visitChildren(ctx)
        if type(value) == int or type(value) == float:
            self.igmemory[name] = type(value)
            self.add_cmd("scoreboard players set MineScript %s %i"%(name, round(value)))
        elif type(value) == list:
            self.igmemory[name] = list
        else:
            print(typeerror1%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, value.__class__.__name__))
            raise Exception("Abort")
        return name

    def visitIgAssignIg(self, ctx):  # Expression of type $var = $expression
        name1 = ctx.ID().getText()
        name2 = self.visitChildren(ctx)

        if name2 not in self.igmemory:
            print(name2)
            raise Exception("Abort")
        
        self.igmemory[name1] = self.igmemory[name2]
        self.add_cmd("scoreboard players operation MineScript %s = MineScript %s"%(name1, name2))
        return name1

    def visitIgAssignUnit(self, ctx):  # Expression of type $var++
        name = ctx.ID().getText()

        if name not in self.igmemory:
            print(name)
            raise Exception("Abort")
                         
        if ctx.op.type == MineScriptParser.USUM: self.add_cmd("scoreboard players add MineScript %s 1"%name)
        elif ctx.op.type == MineScriptParser.USUB: self.add_cmd("scoreboard players remove MineScript %s 1"%name)
        return name

    def visitIgAssignOp(self, ctx):  # Expression of type $var (*/+-%)= expression
        name = ctx.ID().getText()
        value = self.visitChildren(ctx)

        if name not in self.igmemory:
            print(name)
            raise Exception("Abort")

        if not(type(value) == int or type(value) == float):
            print(typeerror5%(ctx.start.line, self.code[ctx.start.line-1].strip(), ctx.op.text, "int", value.__class__.__name__))
            raise Exception("Abort")
        
        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = int
        self.add_cmd("scoreboard players set MineScript _temp%i %i"%(self.temp, value))
        if ctx.op.type == MineScriptParser.PE: self.add_cmd("scoreboard players operation MineScript %s += MineScript _temp%i"%(name, self.temp))
        elif ctx.op.type == MineScriptParser.SE: self.add_cmd("scoreboard players operation MineScript %s -= MineScript _temp%i"%(name, self.temp))
        elif ctx.op.type == MineScriptParser.MLE: self.add_cmd("scoreboard players operation MineScript %s *= MineScript _temp%i"%(name, self.temp))
        elif ctx.op.type == MineScriptParser.MDE: self.add_cmd("scoreboard players operation MineScript %s %%= MineScript _temp%i"%(name, self.temp))
        elif ctx.op.type == MineScriptParser.DE: self.add_cmd("scoreboard players operation MineScript %s /= MineScript _temp%i"%(name, self.temp))
        return name

    def visitIgAssignIgOp(self, ctx):  # Expression of type $var (*/+-%)= $expression
        name1 = ctx.ID().getText()
        name2 = self.visitChildren(ctx)

        if name1 not in self.igmemory:
            print(name1)
            raise Exception("Abort")
        elif name2 not in self.igmemory:
            print(name2)
            raise Exception("Abort")            
        
        if ctx.op.type == MineScriptParser.PE: self.add_cmd("scoreboard players operation MineScript %s += MineScript %s"%(name1, name2))
        if ctx.op.type == MineScriptParser.SE: self.add_cmd("scoreboard players operation MineScript %s -= MineScript %s"%(name1, name2))
        if ctx.op.type == MineScriptParser.MLE: self.add_cmd("scoreboard players operation MineScript %s *= MineScript %s"%(name1, name2))
        if ctx.op.type == MineScriptParser.DE: self.add_cmd("scoreboard players operation MineScript %s /= MineScript %s"%(name1, name2))
        if ctx.op.type == MineScriptParser.MDE: self.add_cmd("scoreboard players operation MineScript %s %%= MineScript %s"%(name1, name2))
        

    def visitIgParens(self, ctx):  # Expression of type ( $expression )
        return self.visit(ctx.igexpr())

    def visitIgOpIg(self, ctx):  # Expression of type $var (*/+-%) $expression
        name1 = self.visit(ctx.igexpr(0))
        name2 = self.visit(ctx.igexpr(1))

        if name1 not in self.igmemory:
            print(name1)
            raise Exception("Abort")
        elif name2 not in self.igmemory:
            print(name2)
            raise Exception("Abort")
        
        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = 0
        self.add_cmd("scoreboard players operation MineScript _temp%i = MineScript %s"%(self.temp, name1))
        if ctx.op.type == MineScriptParser.ADD: self.add_cmd("scoreboard players operation MineScript _temp%i += MineScript %s"%(self.temp, name2))
        if ctx.op.type == MineScriptParser.SUB: self.add_cmd("scoreboard players operation MineScript _temp%i -= MineScript %s"%(self.temp, name2))
        if ctx.op.type == MineScriptParser.MUL: self.add_cmd("scoreboard players operation MineScript _temp%i *= MineScript %s"%(self.temp, name2))
        if ctx.op.type == MineScriptParser.DIV: self.add_cmd("scoreboard players operation MineScript _temp%i /= MineScript %s"%(self.temp, name2))
        if ctx.op.type == MineScriptParser.MOD: self.add_cmd("scoreboard players operation MineScript _temp%i %%= MineScript %s"%(self.temp, name2))
        return "_temp%i"%self.temp

    def visitIgOp(self, ctx):  # Expression of type $var (*/+-%) expression
        name = self.visit(ctx.igexpr())
        value = self.visit(ctx.expr())

        if not(type(value) == int or type(value) == float):
            print(typeerror1%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, value.__class__.__name__))
            raise Exception("Abort")
        
        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = 0
        self.add_cmd("scoreboard players operation MineScript _temp%i = MineScript %s"%(self.temp, name))
        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = 0
        self.add_cmd("scoreboard players set MineScript _temp%i %i"%(self.temp, value))
        if ctx.op.type == MineScriptParser.ADD: self.add_cmd("scoreboard players operation MineScript _temp%i += MineScript _temp%i"%(self.temp-1, self.temp))
        if ctx.op.type == MineScriptParser.SUB: self.add_cmd("scoreboard players operation MineScript _temp%i -= MineScript _temp%i"%(self.temp-1, self.temp))
        if ctx.op.type == MineScriptParser.MUL: self.add_cmd("scoreboard players operation MineScript _temp%i *= MineScript _temp%i"%(self.temp-1, self.temp))
        if ctx.op.type == MineScriptParser.DIV: self.add_cmd("scoreboard players operation MineScript _temp%i /= MineScript _temp%i"%(self.temp-1, self.temp))
        if ctx.op.type == MineScriptParser.MOD: self.add_cmd("scoreboard players operation MineScript _temp%i %%= MineScript _temp%i"%(self.temp-1, self.temp))
        return "_temp%i"%(self.temp-1)

    def visitIgComparison(self, ctx):  # Expression of type $expression (> < <= >= != ==) expression
        name = self.visit(ctx.igexpr())
        value = self.visit(ctx.expr())

        if not(type(value) == int or type(value) == float):
            print(typeerror1%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, value.__class__.__name__))
            raise Exception("Abort")
        
        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = 0
        self.add_cmd("scoreboard players set MineScript _temp%i %i"%(self.temp, value))
        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = 0
        self.add_cmd("scoreboard players set MineScript _temp%i 0"%self.temp)
        if ctx.op.type == MineScriptParser.GT: self.add_cmd("execute if score MineScript %s > MineScript _temp%i run scoreboard players set MineScript _temp%i 1"%(name, self.temp-1, self.temp))
        elif ctx.op.type == MineScriptParser.LT: self.add_cmd("execute if score MineScript %s < MineScript _temp%i run scoreboard players set MineScript _temp%i 1"%(name, self.temp-1, self.temp))
        elif ctx.op.type == MineScriptParser.GET: self.add_cmd("execute if score MineScript %s >= MineScript _temp%i run scoreboard players set MineScript _temp%i 1"%(name, self.temp-1, self.temp))
        elif ctx.op.type == MineScriptParser.LET: self.add_cmd("execute if score MineScript %s <= MineScript _temp%i run scoreboard players set MineScript _temp%i 1"%(name, self.temp-1, self.temp))
        elif ctx.op.type == MineScriptParser.EQ: self.add_cmd("execute if score MineScript %s = MineScript _temp%i run scoreboard players set MineScript _temp%i 1"%(name, self.temp-1, self.temp))
        elif ctx.op.type == MineScriptParser.DIF: self.add_cmd("execute unless score MineScript %s = MineScript _temp%i run scoreboard players set MineScript _temp%i 1"%(name, self.temp-1, self.temp))
        return "_temp%i"%self.temp

    def visitExecute(self, ctx):  # Expression of type $execute(execute){ stat }
        execute = str(self.visit(ctx.expr()))
        stat = ctx.stat()
        self.add_exec(execute)
        self.visit(stat)
        self.pop_exec()

    def visitIgComparisonIg(self, ctx):  # Expression of type $expression (> < <= >= != ==) $expression
        name1 = self.visit(ctx.igexpr(0))
        name2 = self.visit(ctx.igexpr(1))
        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = 0
        self.add_cmd("scoreboard players set MineScript _temp%i 0"%self.temp)
        if ctx.op.type == MineScriptParser.GT: self.add_cmd("execute if score MineScript %s > MineScript %s run scoreboard players set MineScript _temp%i 1"%(name1, name2, self.temp))
        elif ctx.op.type == MineScriptParser.LT: self.add_cmd("execute if score MineScript %s < MineScript %s run scoreboard players set MineScript _temp%i 1"%(name1, name2, self.temp))
        elif ctx.op.type == MineScriptParser.GET: self.add_cmd("execute if score MineScript %s >= MineScript %s run scoreboard players set MineScript _temp%i 1"%(name1, name2, self.temp))
        elif ctx.op.type == MineScriptParser.LET: self.add_cmd("execute if score MineScript %s <= MineScript %s run scoreboard players set MineScript _temp%i 1"%(name1, name2, self.temp))
        elif ctx.op.type == MineScriptParser.EQ: self.add_cmd("execute if score MineScript %s = MineScript %s run scoreboard players set MineScript _temp%i 1"%(name1, name2, self.temp))
        elif ctx.op.type == MineScriptParser.DIF: self.add_cmd("execute unless score MineScript %s = MineScript %s run scoreboard players set MineScript _temp%i 1"%(name1, name2, self.temp))
        return "_temp%i"%self.temp

    def visitIgIfElse(self, ctx):  # Expression of type $if ($expression) { stat } ($else { stat })?
        name = self.visit(ctx.igexpr())
        nested = False
        length = 0
        text = "execute if score MineScript %s matches 1"%name
        if self.if_stat is None:
            self.if_stat = text
        else:
            nested = True
            length = len(text)+5
            self.if_stat += " run " + text   
        self.visit(ctx.stat(0))

        text = "execute unless score MineScript %s matches 1"%name
        if nested:
            self.if_stat = self.if_stat[:-length]
            if ctx.stat(1) is not None:
                self.if_stat += " run " + text
                length = len(text) + 5
        else:
            if ctx.stat(1) is not None:
                self.if_stat = text
                
        if ctx.stat(1) is not None: self.visit(ctx.stat(1))

        if nested:
            self.if_stat = self.if_stat[:-length]
        else:
            self.if_stat = None

    def visitGetPos(self, ctx):  # Expression of type $pos(@selector; 'xyz')
        selector = str(self.visit(ctx.expr(0)))
        coord = self.visit(ctx.expr(1))

        if not type(coord) == int:
            print(typeerror3%(ctx.start.line, self.code[ctx.start.line-1].strip(), coord.__class__.__name__))
            raise Exception("Abort")
        
        if not selector.startswith("@"):
            print(valueerror3%(ctx.start.line, self.code[ctx.start.line-1].strip()))
            raise Exception("Abort")
        
        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = int

        if coord == 0: self.add_cmd("execute store result score MineScript _temp%i run data get entity %s Pos[0]"%(self.temp, selector))
        elif coord == 1: self.add_cmd("execute store result score MineScript _temp%i run data get entity %s Pos[1]"%(self.temp, selector))
        elif coord == 2: self.add_cmd("execute store result score MineScript _temp%i run data get entity %s Pos[2]"%(self.temp, selector))

        return "_temp%i"%self.temp

    def visitIsBlock(self, ctx):  # Expression of type $isblock(selector, pos, block)
        selector = str(self.visit(ctx.expr(0)))
        relpos = str(self.visit(ctx.expr(1)))
        block = str(self.visit(ctx.expr(2)))

        if not selector.startswith("@"):
            print(valueerror3%(ctx.start.line, self.code[ctx.start.line-1].strip()))
            raise Exception("Abort")

        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = int

        self.add_cmd("scoreboard players set MineScript _temp%i 0"%self.temp)
        self.add_cmd("execute at %s if block %s %s run scoreboard players set MineScript _temp%i 1"%(selector, relpos, block, self.temp))

        return "_temp%i"%self.temp

    def visitAddObj(self, ctx):
        name = str(self.visit(ctx.expr(0)))
        tp = str(self.visit(ctx.expr(1)))

        self.add_cmd("scoreboard objectives add %s %s"%(name, tp))

    def visitGetScore(self, ctx):  # Expression of type $getscore(selector, name)
        selector = str(self.visit(ctx.expr(0)))
        name = str(self.visit(ctx.expr(1)))

        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = int
        
        self.add_cmd("scoreboard players operation MineScript _temp%i = %s %s"%(self.temp, selector, name))
        
        return "_temp%i"%self.temp

    def visitSetScore(self, ctx):  # Expression of type $setscore(selector, name, value)
        selector = str(self.visit(ctx.expr(0)))
        name = str(self.visit(ctx.expr(1)))
        ge = ctx.genexpr()

        if ge.expr() is not None:
            value = self.visit(ge.expr())

            if not type(value) == int:
                print(typeerror1%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, value.__class__.__name__))
                raise Exception("Abort")
                                
            self.temp += 1
            self.igmemory["_temp%i"%self.temp] = int
            
            self.add_cmd("scoreboard players set MineScript _temp%i %i"%(self.temp, value))
            self.add_cmd("scoreboard players operation %s %s = MineScript _temp%i"%(selector, name, self.temp))
            
        elif ge.igexpr() is not None:
            name2 = self.visit(ge.igexpr())
            self.add_cmd("scoreboard players operation %s %s = MineScript %s"%(selector, name, name2))

    def visitAddTag(self, ctx):  # Expression of type $addtag(selector, tag)
        selector = str(self.visit(ctx.expr(0)))
        name = str(self.visit(ctx.expr(1)))

        self.add_cmd("tag %s add %s"%(selector, name))

    def visitRemTag(self, ctx):  # Expression of type $remtag(selector, tag)
        selector = str(self.visit(ctx.expr(0)))
        name = str(self.visit(ctx.expr(1)))

        self.add_cmd("tag %s remove %s"%(selector, name))

    def visitHasTag(self, ctx):  # Expression of type $hastag(selector, tag)
        selector = str(self.visit(ctx.expr(0)))
        name = str(self.visit(ctx.expr(1)))

        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = int

        self.add_cmd("scoreboard players set MineScript _temp%i 0"%self.temp)
        self.add_cmd("execute as %s at @s[tag=%s] run scoreboard players set MineScript _temp%i 1"%(selector, name, self.temp))

        return "_temp%i"%self.temp

    def visitCount(self, ctx):  # Expression of type $count(selector)
        selector = str(self.visit(ctx.expr()))
        
        if not selector.startswith("@"):
            print(valueerror3%(ctx.start.line, self.code[ctx.start.line-1].strip()))
            raise Exception("Abort")

        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = int

        self.add_cmd("scoreboard players set MineScript _temp%i 0"%self.temp)
        self.add_cmd("execute as %s run scoreboard players add MineScript _temp%i 1"%(selector, self.temp))

        return "_temp%i"%self.temp

    def visitIgFor(self, ctx):  # Expression of type $for ($forInit; $forTest; $forUpdate) { stat }
        stats = ctx.stat()
        init = ctx.igForControl().igForInit()
        expr = ctx.igForControl().igexpr()
        update = ctx.igForControl().igForUpdate()

        init_n = self.visit(init)
        expr_n = self.visit(expr)
        
        self.add_cmd("execute if score MineScript %s matches 1 run function %s:_for%i"%(expr_n, self.datapack_name, self.loops+1))
        
        self.add_loop()
        self.visit(stats)
        self.visit(update)
        expr_n = self.visit(expr)
        self.add_cmd("execute if score MineScript %s matches 1 run function %s:_for%i"%(expr_n, self.datapack_name, self.loops))
        self.pop_loop()

    def visitIgForEntity(self, ctx):  # Expression of type $forentity(selector; new_var) { stat }
        selector = str(self.visit(ctx.expr()))
        name = ctx.ID().getText()
        stats = ctx.stat()

        self.tag += 1
        value = add_to_selector(selector, ["limit=1", "tag=!_tag%i"%self.tag])
        self.memory[name] = value

        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = int
        self.add_cmd("scoreboard players set MineScript _temp%i 0"%self.temp)
        self.add_cmd("execute as %s run scoreboard players add MineScript _temp%i 1"%(selector, self.temp))
        
        self.temp += 1
        self.igmemory["_temp%i"%self.temp] = int
        self.add_cmd("scoreboard players set MineScript _temp%i 0"%self.temp)
        self.add_cmd("scoreboard players operation MineScript _temp%i = MineScript _temp%i"%(self.temp, self.temp-1))
        count = self.temp
              
        self.add_cmd("execute if score MineScript _temp%i matches 1.. run function %s:_for%i"%(count, self.datapack_name, self.loops+1))
        
        self.add_loop()
        self.visit(stats)
        self.add_cmd("tag %s add _tag%i"%(value, self.tag))

        self.add_cmd("scoreboard players remove MineScript _temp%i 1"%count)
        self.add_cmd("execute if score MineScript _temp%i matches 1.. run function %s:_for%i"%(count, self.datapack_name, self.loops))
        self.pop_loop()

        self.add_cmd("tag %s remove _tag%i"%(selector, self.tag))
        
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
                name = str(self.visit(e.igexpr()))
                text.append("{\"score\":{\"name\":\"MineScript\",\"objective\":\"%s\"},\"color\":\"%s\"}"%(name, color))
        self.add_cmd("tellraw @a ["+','.join(text)+"]")

    def visitTeleport(self, ctx):  # Expression of type $tp(selector, pos)
        selector = str(self.visit(ctx.expr(0)))
        pos = str(self.visit(ctx.expr(1)))
        self.add_cmd("execute as %s at @s run tp @s %s"%(selector, pos))

    def visitIgFuncDef(self, ctx):  # Expression of type $function func { stat }
        name = ctx.ID().getText()
        stats = ctx.stat()
        self.visit(stats)
        self.igfunctions[name] = self._commands[:]
        self._commands = []

    def visitIgFuncCall(self, ctx):  # Expression of type $func()
        name = ctx.ID().getText()
        self.add_cmd("function %s:%s"%(self.datapack_name, name))

    def visitIgId(self, ctx):  # Expression of type $var
        name = ctx.ID().getText()
        return name

    def visitAssign(self, ctx):  # Expression of type var = expression
        name = ctx.ID().getText()
        value = self.visit(ctx.expr())
        self.memory[name] = value
        return value

    def visitAssignUnit(self, ctx):  # Expression of type var++
        name = ctx.ID().getText()
        try:
            if ctx.op.type == MineScriptParser.USUM: self.memory[name] += 1
            elif ctx.op.type == MineScriptParser.USUB: self.memory[name] -= 1
        except TypeError:
            print(typeerror1%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, self.memory[name].__class__.__name__))
            raise Exception("Abort")
        except KeyError:
            print(nameerror%(ctx.start.line, self.code[ctx.start.line-1].strip(), name))
            raise Exception("Abort")

    def visitAssignOp(self, ctx):  # Expression of type var (*/+-%)= expression
        name = ctx.ID().getText()
        value = self.visit(ctx.expr())
        try:
            if ctx.op.type == MineScriptParser.PE: self.memory[name] += value
            elif ctx.op.type == MineScriptParser.SE: self.memory[name] -= value
            elif ctx.op.type == MineScriptParser.MLE: self.memory[name] *= value
            elif ctx.op.type == MineScriptParser.DE: self.memory[name] /= value
            elif ctx.op.type == MineScriptParser.MDE: self.memory[name] %= value
        except TypeError:
            print(typeerror1%(ctx.start.line, self.code[ctx.start.line-1].strip(), name, self.memory[name].__class__.__name__))
            raise Exception("Abort")
        except KeyError:
            print(nameerror%(ctx.start.line, self.code[ctx.start.line-1].strip(), name))
            raise Exception("Abort")

    def visitFuncDef(self, ctx):  # Expression of type function func { stat }
        name = ctx.ID().getText()
        value = ctx.stat()
        self.memory[name] = value

    def visitFuncCall(self, ctx):  # Expression of type func()
        name = ctx.ID().getText()
        if name in self.memory:
            return self.visit(self.memory[name])
        else:
            print(nameerror%(ctx.start.line, self.code[ctx.start.line-1].strip(), name))
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
            print(typeerror2%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__))
            raise Exception("Abort")

    def visitInt(self, ctx):  # Expression of type int(expression)
        value = self.visit(ctx.expr())
        try:
            return int(value)
        except TypeError:
            print(typeerror8%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__))
            raise Exception("Abort")
        except ValueError:
            print(valueerror2%(ctx.start.line, self.code[ctx.start.line-1].strip(), value))
            raise Exception("Abort")  

    def visitFloat(self, ctx):  # Expression of type float(expression)
        value = self.visit(ctx.expr())
        try:
            return float(value)
        except TypeError:
            print(typeerror7%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__))
            raise Exception("Abort")
        except ValueError:
            print(valueerror1%(ctx.start.line, self.code[ctx.start.line-1].strip(), value))
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
                print(syntaxerror%(ctx.start.line, self.code[ctx.start.line-1].strip()))
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
            print(indexerror%(ctx.start.line, self.code[ctx.start.line-1].strip(), index))
            raise Exception("Abort")
        except TypeError:
            print(typeerror3%(ctx.start.line, self.code[ctx.start.line-1].strip(), index.__class__.__name__))
            raise Exception("Abort")

    def visitAttribute(self, ctx):  # Expression of type expression.attr
        value = self.visit(ctx.expr())
        attr = ctx.ID().getText()
        try:
            return getattr(value, attr)
        except AttributeError:
            print(attributeerror%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__, attr))
            raise Exception("Abort")

    def visitAttributeCallEmpty(self, ctx):  # Expression of type expression.attr()
        value = self.visit(ctx.expr())
        attr = ctx.ID().getText()
        try:
            if attr not in approved_attrs:
                raise AttributeError()
            return getattr(value, attr)()
        except AttributeError:
            print(attributeerror%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__, attr))
            raise Exception("Abort")
        except TypeError:
            print(typeerror4%(ctx.start.line, self.code[ctx.start.line-1].strip(), getattr(value, attr).__class__.__name__))
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
            print(attributeerror%(ctx.start.line, self.code[ctx.start.line-1].strip(), value.__class__.__name__, attr))
            raise Exception("Abort")
        except TypeError:
            print(typeerror4%(ctx.start.line, self.code[ctx.start.line-1].strip(), getattr(value, attr).__class__.__name__))
            raise Exception("Abort")

    def visitId(self, ctx):  # Expression of type var
        name = ctx.ID().getText()
        if name in self.memory:
            return self.memory[name]
        else:
            print(nameerror%(ctx.start.line, self.code[ctx.start.line-1].strip(), name))
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
        except TypeError:
            print(typeerror5%(ctx.start.line, self.code[ctx.start.line-1].strip(), ctx.op.text, left.__class__.__name__, right.__class__.__name__))
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
            print(typeerror6%(ctx.start.line, self.code[ctx.start.line-1].strip(), ctx.op.text, left.__class__.__name__, right.__class__.__name__))
            raise Exception("Abort")

    def visitParens(self, ctx):  # Expression of type (expression)
        return self.visit(ctx.expr())

    def visitCommand(self, ctx):  # Expression of type /expression
        exp = str(self.visit(ctx.expr()))
        self.add_cmd(exp)

    def visitFor(self, ctx):  # Expression of type for (forInit; forTest; forUpdate) { stat }
        stats = ctx.stat()
        init = ctx.forControl().forInit()
        expr = ctx.forControl().expr()
        update = ctx.forControl().forUpdate()
        self.visit(init)
        while self.visit(expr):
            self.visit(stats)
            self.visit(update)

    def visitIfElse(self, ctx):  # Expression of type if (expression) { stat } (else { stat })?
        value = self.visit(ctx.expr())
        if value:
            self.visit(ctx.stat(0))
        elif ctx.stat(1) is not None:
            self.visit(ctx.stat(1))

    def visitSetDisplay(self, ctx):  # Expression of type $setdisplay(var, mode)
        name = self.visit(ctx.igexpr())
        mode = ctx.DSPL_MODE().getText()
        self.add_cmd("scoreboard objectives setdisplay %s %s"%(mode, name))
