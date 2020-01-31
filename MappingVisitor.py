from Visitor import Visitor
from MineScriptParser import MineScriptParser
import tags


class MVisitor(Visitor):
    def __init__(self, name, code, file):
        self.code = code            # The actual code
        self.file = file            # Filename
        self.datapack_name = name   # Name of the datapack
        self._commands = []         # List of commands to be added to the current function
        self.warnings = []          # List of warnings
        
        self.memory = {}            # Stores variables
        self.localmemory = {}       # Stores local variables
        self.functionargs = {}      # Stores the args a function takes
        self.func = None            # Current function
        self.r_value = None         # Stores the return variable of the current function

        self.igmemory = {}          # Stores the in-game variable names
        self.igfunctionargs = {}    # Stores the args an igfunction takes
        self.igfunctionreturn = {}  # Stores the name of the return variable of a function
        self.igfunctions = {}       # Stores the functions to be turned into .mcfunction files
        self.igfunc = None          # Current igfunction
        self.ig_r_value = None      # Stores the return variable of the current igfunc

        self.vars = []              # Stores all the temporary variables currently in use
        self.nreusable = []         # Stores all non reusable variables
        self.igloops = {}           # Stores the loops to be turned into .mcfunction files
        self.loop = []              # Keeps track of loops
        self.prefixes = []          # Keeps track of if/else and execute statements
        self.loops = 0              # Loop ID
        self.tag = 0                # Tag ID
        
        self.get_tags()             # Get all tags from file
        self.memory["dpname"] = name
         
    def visitIgAssign(self, ctx):  # Expression of type $var = expression
        name = ctx.ID().getText()
        self.visitChildren(ctx)

    def visitIgFirstAssign(self, ctx):
        name = ctx.ID().getText()
        tp = ctx.tp.text
        self.visitChildren(ctx)
        if tp == "int":
            self.add_int_var(name)
        elif tp == "float":
            self.add_float_var(name)

    def visitIgAssignIg(self, ctx):  # Expression of type $var = $expression
        name1 = self.get_var_name(ctx.ID().getText())
        name2 = self.get_var_name(self.visitChildren(ctx))
        if name2.startswith("_"): self.mark_unused(name2)
        self.add_var(name1)
        return name1

    def visitIgFirstAssignIg(self, ctx):  # Expression of type $var = $expression
        name1 = self.get_var_name(ctx.ID().getText())
        name2 = self.get_var_name(self.visitChildren(ctx))
        tp = ctx.tp.text
        if name2.startswith("_"): self.mark_unused(name2)
        if tp == "int":
            self.add_int_var(name1)
        elif tp == "float":
            self.add_float_var(name1)
        return name1

    def visitIgAssignUnit(self, ctx):  # Expression of type $var++
        name = ctx.ID().getText()
        return name

    def visitIgAssignOp(self, ctx):  # Expression of type $var (*/+-%)= expression
        name = ctx.ID().getText()
        self.visitChildren(ctx)
        return name

    def visitIgAssignIgOp(self, ctx):  # Expression of type $var (*/+-%)= $expression
        name2 = self.visitChildren(ctx)
        if name2.startswith("_"): self.mark_unused(name2)

    def visitIgParens(self, ctx):  # Expression of type ( $expression )
        return self.visit(ctx.igexpr())

    def visitIgOpIg(self, ctx):  # Expression of type $expression (*/+-%^) $expression
        name1 = self.visit(ctx.igexpr(0))
        name2 = self.visit(ctx.igexpr(1))
        if name1.startswith("_"): self.mark_unused(name1)
        if name2.startswith("_"): self.mark_unused(name2)
        result = self.get_int_var()
        return result

    def visitIgOp(self, ctx):  # Expression of type $expression (*/+-%^) expression
        name = self.visit(ctx.igexpr())
        self.visit(ctx.expr())
        if name.startswith("_"): self.mark_unused(name)
        result = self.get_int_var()
        return result

    def visitIgOpM(self, ctx):  # Expression of type expression (*/+-%^) $expression
        return self.visitIgOp(ctx)

    def visitIgNot(self, ctx):  # Expression of type !$expression
        name = self.get_var_name(self.visit(ctx.igexpr()))
        if name.startswith("_"): self.mark_unused(name)
        result = self.get_int_var()
        return result

    def visitIgBoolOp(self, ctx):  # Expression of type genexpr &&/|| genexpr
        if len(ctx.igexpr()) == 1:
            expr1 = self.visit(ctx.igexpr(0))
            if expr1.startswith("_"): self.mark_unused(expr1)
            expr2 = self.visit(ctx.expr())
        else:
            expr1 = self.visit(ctx.igexpr(0))
            expr2 = self.visit(ctx.igexpr(1))
            if expr1.startswith("_"): self.mark_unused(expr1)
            if expr2.startswith("_"): self.mark_unused(expr2)
        result = self.get_int_var()
        return result

    def visitIgComparison(self, ctx):  # Expression of type $expression (> < <= >= != ==) expression
        name = self.visit(ctx.igexpr())
        self.visit(ctx.expr())
        if name.startswith("_"): self.mark_unused(name)
        result = self.get_int_var()
        return result

    def visitIgComparisonM(self, ctx):  # Expression of type expression (> < <= >= != ==) $expression
        return self.visitIgComparison(ctx)

    def visitExecute(self, ctx):  # Expression of type $execute(execute){ stat }
        self.visit(ctx.expr())
        stat = ctx.stat()
        self.visit(stat)

    def visitIgComparisonIg(self, ctx):  # Expression of type $expression (> < <= >= != ==) $expression
        name1 = self.get_var_name(self.visit(ctx.igexpr(0)))
        name2 = self.get_var_name(self.visit(ctx.igexpr(1)))
        if name1.startswith("_"): self.mark_unused(name1)
        if name2.startswith("_"): self.mark_unused(name2)
        result = self.get_int_var()      
        return result

    def visitIgIfElse(self, ctx):  # Expression of type $if ($expression) { stat } ($else { stat })?
        name = self.visit(ctx.igexpr())
        self.visit(ctx.stat(0))
        if ctx.stat(1) is not None:
            self.visit(ctx.stat(1))
        if name.startswith("_"): self.mark_unused(name)

    def visitGetPos(self, ctx):  # Expression of type $pos(selector, index)
        self.visitChildren(ctx)
        result = self.get_int_var()
        return result

    def visitGetData(self, ctx):  # Expression of type $getdata(selector, path, scale?)
        self.visitChildren(ctx)
        result = self.get_int_var()
        return result

    def visitSetData(self, ctx):  # Expression of type $setdata(selector, path, value)
        self.visit(ctx.expr(0))
        self.visit(ctx.expr(1))
        if ctx.genexpr().igexpr() is not None:
            name = self.get_var_name(self.visit(ctx.genexpr().igexpr()))
            if name.startswith("_"): self.mark_unused(name)

    def visitIsBlock(self, ctx):  # Expression of type $isblock(selector, pos, block)
        self.visitChildren(ctx)
        result = self.get_int_var()
        return result

    def visitAddObj(self, ctx):
        self.visitChildren(ctx)

    def visitEnableTrigger(self, ctx):
        self.visitChildren(ctx)

    def visitRename(self, ctx):
        self.visitChildren(ctx)

    def visitGetScore(self, ctx):  # Expression of type $getscore(selector, name)
        self.visitChildren(ctx)
        result = self.get_int_var()
        return result

    def visitSetScore(self, ctx):  # Expression of type $setscore(selector, name, value)
        self.visit(ctx.expr(0))
        self.visit(ctx.expr(1))
        ge = ctx.genexpr()

        if ge.expr() is not None:                 
            self.get_int_var()    
        elif ge.igexpr() is not None:
            name2 = self.get_var_name(self.visit(ge.igexpr()))
            if name2.startswith("_"): self.mark_unused(name2)

    def visitAddTag(self, ctx):  # Expression of type $addtag(selector, tag)
        self.visitChildren(ctx)

    def visitRemTag(self, ctx):  # Expression of type $remtag(selector, tag)
        self.visitChildren(ctx)

    def visitHasTag(self, ctx):  # Expression of type $hastag(selector, tag)
        self.visitChildren(ctx)
        result = self.get_int_var()
        return result

    def visitCount(self, ctx):  # Expression of type $count(selector)
        self.visitChildren(ctx)
        result = self.get_int_var()
        return result

    def visitIgWhile(self, ctx): # Expression of type $while (genexpr) { stat }
        stats = ctx.stat()
        expr = ctx.genexpr()
        if expr.igexpr() is not None:
            expr_n = self.visit(expr.igexpr())
            expr_n = self.visit(expr.igexpr())
        else:
            self.visit(expr.expr())
        self.visit(stats)
        if expr.igexpr() is not None and expr_n.startswith("_"): self.mark_unused(expr_n)

    def visitIgFor(self, ctx):  # Expression of type $for ($forInit; $forTest; $forUpdate) { stat }
        stats = ctx.stat()
        init = ctx.igForControl().igForInit()
        expr = ctx.igForControl().igexpr()
        update = ctx.igForControl().igForUpdate()
        self.visit(init)
        expr_n = self.visit(expr)
        self.visit(stats)
        self.visit(update)
        expr_n = self.visit(expr)
        if expr_n.startswith("_"): self.mark_unused(expr_n)

    def visitIgForEntity(self, ctx):  # Expression of type $forentity(selector; new_var) { stat }
        name = ctx.ID().getText()
        self.visit(ctx.expr())
        self.memory[name] = ""
        stats = ctx.stat()
        self.visit(stats)

    def visitIgPrint(self, ctx):  # Expression of type $print(genexpression,...| COLOR)
        for child in ctx.igPrintControl().igPrintArg():
            e = child.genexpr()
            if e.expr() is not None: self.visit(e.expr())
            if e.igexpr() is not None:
                self.visit(e.igexpr())
                name = self.get_var_name(self.visit(e.igexpr()))
                if name.startswith("_"): self.mark_unused(name)

    def visitTeleport(self, ctx):  # Expression of type $tp(selector, pos)
        self.visitChildren(ctx)

    def visitIgFuncDef(self, ctx):  # Expression of type $function func { stat }
        name = ctx.ID(0).getText()
        stats = ctx.stat()
        args = ctx.ID()[1:]
        self.igfunctionargs[name] = [[], []]
        r_var = self.get_int_var()
        self.mark_not_reusable(r_var)
        self.igfunctionreturn[name] = r_var
        
        for arg in args:
            var = self.get_int_var()
            self.mark_not_reusable(var)
            self.add_func_arg(name, var, arg.getText())
            
        self.igfunctions[name] = []
        self.visit(stats)

    def visitIgFuncCall(self, ctx):  # Expression of type $func()
        return ""

    def visitIgReturn(self, ctx):
        self.visitChildren(ctx)

    def visitIgId(self, ctx):  # Expression of type $var
        name = self.get_var_name(ctx.ID().getText())
        return name

    def visitSetDisplay(self, ctx):  # Expression of type $setdisplay(var, mode)
        name = self.visit(ctx.igexpr())
        if name.startswith("_"): self.mark_unused(name)

    def visitCommand(self, ctx):  # Expression of type $mc(expression)
        self.visitChildren(ctx)

    def visitPrint(self, ctx):
        self.visitChildren(ctx)
        
del Visitor
