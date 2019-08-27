from MineScriptVisitor import MineScriptVisitor


class IncludeVisitor(MineScriptVisitor):
    def __init__(self):
        self.modules = []

    def add_module(self, module, line):
        if module not in self.modules:
            self.modules.append((module, line))

    def visitInclude(self, ctx):
        name = ctx.ID().getText()
        self.add_module(name, ctx.start.line)
        
