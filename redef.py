import re
import ast
import pdb
import inspect
import itertools



class FuncRedef(ast.NodeVisitor):
    def __init__(self, context_ast):
        self.context_ast = context_ast

    @classmethod
    def create_by_func(cls, context_f):
        context_src = _chop_src(inspect.getsource(context_f))
        context_ast = ast.parse(context_src).body[0]
        return cls(context_ast)

    def visit_FunctionDef(self, node):
        context_ast = self.context_ast
        node_body = node.body
        self._replace(context_ast, ast.Yield, node_body)
        node.body = context_ast.body

    def _replace(self, ast_obj, old, new):
        if not hasattr(ast_obj, 'body'):
            return

        for idx, _ast in enumerate(ast_obj.body):
            if hasattr(_ast, 'value') and isinstance(_ast.value, old):
                ast_obj.body[idx:idx+1] = new
            self._replace(_ast, old, new)

class ContextRedef(ast.NodeVisitor):
    RETURN_STATE = 'return {0}'

    def __init__(self, func):
        self.func = func

    def visit_FunctionDef(self, context_ast):
        func_redefer = FuncRedef(context_ast)
        func_src = _chop_src(inspect.getsource(self.func))
        func_ast = ast.parse(func_src).body[0]
        func_redefer.visit(func_ast)
        return_state = self.RETURN_STATE.format(func_ast.name)
        return_ast = ast.parse(return_state)
        context_ast.body = [func_ast] + return_ast.body


def context_enhancer(context_f):
    context_src = _chop_src(inspect.getsource(context_f))
    context_ast = ast.parse(context_src)
    def context_wrapper(*context_args, **context_kws):
        def _enhance(func):
            context_redefer = ContextRedef(func)
            context_redefer.visit(context_ast)
            tmp_locals = {}
            exec(compile(context_ast, '', 'exec'), tmp_locals, tmp_locals)
            context_f.__code__ = tmp_locals[context_f.__name__].__code__
            return context_f(*context_args, **context_kws)
        return _enhance
    return context_wrapper

def func_enhancer(context_f):
    func_redefer = FuncRedef.create_by_func(context_f)
    def _enhance(func):
        func_src = _chop_src(inspect.getsource(func))
        func_ast = ast.parse(func_src)
        func_redefer.visit(func_ast)
        tmp_locals = {}
        exec(compile(func_ast, '', 'exec'), tmp_locals, tmp_locals)
        func.__code__ = tmp_locals[func.__name__].__code__
        return func

    return _enhance

def redef(context_f):
    argspec = inspect.getargspec(context_f)
    if any(getattr(argspec, f) for f in argspec._fields):
        return context_enhancer(context_f)
    else:
        return func_enhancer(context_f)

def _chop_src(src):
    src_line = src.splitlines()
    decorator_regex = re.compile('^\s*@')
    code_line = itertools.ifilterfalse(decorator_regex.match, src_line)
    src_chopped = '\n'.join(code_line)
    return src_chopped

@redef
def tag(name, fp='sc'):
    print '<%s>' % name
    yield
    print '</%s>' % name
    print str(x) + y

@tag('head')
def g(x, y='as'):
    print 'g invoking %s' % x
    print 'this is ' + y
    print fp


if __name__ == '__main__':
    g(1111)

