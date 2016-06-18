import re
import ast
import pdb
import inspect
import itertools



class ReDef(ast.NodeVisitor):
    def __init__(self, context_f):
        self.context_f = context_f

    def get_context_ast(self, context_f):
        context_src = _chop_src(inspect.getsource(context_f))
        context_ast = ast.parse(context_src)
        return context_ast.body[0]

    def visit_FunctionDef(self, node):
        context_ast = self.get_context_ast(self.context_f)
        node_body = node.body[0]
        self._replace(context_ast, ast.Yield, node_body)
        node.body = context_ast.body


    def _replace(self, ast_obj, old, new):
        if not hasattr(ast_obj, 'body'):
            return

        for idx, _ast in enumerate(ast_obj.body):
            if hasattr(_ast, 'value') and isinstance(_ast.value, old):
                ast_obj.body[idx] = new

            self._replace(_ast, old, new)

def redef(context_f):
    redef_obj = ReDef(context_f)

    def wrapper(func):
        func_src = _chop_src(inspect.getsource(func))
        func_ast = ast.parse(func_src)
        redef_obj.visit(func_ast)

        tmp_locals = {}
        exec(compile(func_ast, '', 'exec'), tmp_locals, tmp_locals)
        func.__code__ = tmp_locals[func.__name__].__code__
        return func

    return wrapper

def _chop_src(src):
    src_line = src.splitlines()
    decorator_regex = re.compile('^\s*@')
    code_line = itertools.ifilterfalse(decorator_regex.match, src_line)
    src_chopped = '\n'.join(code_line)
    return src_chopped

if __name__ == '__main__':
    pass

