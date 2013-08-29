class Scope(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.objects = {}

    def lookup(self, name):
        if name in self:
            return self[name]
        elif self.parent is not None:
            return self.parent.lookup(name)

    def __contains__(self, name):
        return name in self.objects
    def __getitem__(self, name):
        return self.objects[name]
    def __setitem__(self, name, value):
        self.objects[name] = value

class Defn(object):
    def __init__(self, scope):
        self.argc = 0
        self.registers = []
        self.blocks = []
        self.scope = scope

    def newreg(self):
        reg = VirtualRegister(self, len(self.registers))
        self.registers.append(reg)
        return reg

    def newblock(self):
        reg = Block(self, len(self.blocks))
        self.blocks.append(reg)
        return reg

class VirtualRegister(object):
    def __init__(self, defn, index):
        self.defn = defn
        self.index = index
    def __repr__(self):
        return 'r%i' % self.index

class Block(object):
    def __init__(self, defn, index):
        self.defn = defn
        self.index = index
        self.instructions = []
        self.sourcemap = []
    def __iter__(self):
        return iter(self.instructions)
    def __len__(self):
        return len(self.instructions)
    def __setitem__(self, index, instruction):
        self.instructions[index] = instruction
    def __getitem__(self, index):
        return self.instructions[index]
    def append(self, instruction, location=None):
        self.instructions.append(instruction)
        self.sourcemap.append(location)
    def __repr__(self):
        return ( '%3i:    ' % self.index
               + '\n        '.join(repr(i) for i in self.instructions) )

class Closure(object):
    def __init__(self, frame, defn):
        self.frame = frame
        self.defn  = defn

class Frame(object):
    def __init__(self, ret, closure):
        self.ret = ret
        self.closure = closure
        self.defn = closure.defn
        self.entryvar = None
        self.registers = [None for _ in closure.defn.registers]
        self.block = closure.defn.blocks[0]
        self.pc = 0

    def pass_arguments(self, argv):
        if self.defn.argc < len(argv):
            return False
        for i in range(self.defn.argc):
            self.registers[i] = argv[i]
        return True

    def fetch(self, arg):
        if isinstance(arg, VirtualRegister):
            if self.defn is arg.defn:
                return self.registers[arg.index]
            else:
                return self.closure.frame.fetch(arg)
        else:
            return arg

    def store(self, arg, value):
        if arg is None:
            return
        assert isinstance(arg, VirtualRegister)
        if self.defn is arg.defn:
            self.registers[arg.index] = value
        else:
            self.closure.frame.store(arg, value)

    def resume(self, value):
        self.store(self.entryvar, value)
        return self

    def lookup(self, name):
        arg = self.defn.scope.lookup(name)
        if arg is not None:
            return self.fetch(arg)

class Builder(object):
    def __init__(self, defn, macros):
        self.defn   = defn
        self.macros = macros
        self.flag   = None
        self.block  = defn.newblock()
        self.location = None

    def emit(self, *args):
        self.block.append(args, self.location)

    def emit_call(self, res, callee, argv):
        self.emit('call', res, callee, *argv)
        return res

    def emit_return(self, value):
        self.emit('return', value)

    def emit_getattr(self, res, obj, name):
        self.emit('getattr', res, obj, name)
        return res

    def emit_setattr(self, obj, name, value):
        self.emit('setattr', obj, name, value)
        return value

    def emit_callattr(self, res, obj, name, argv):
        self.emit('callattr', res, obj, name, *argv)
        return res

    def emit_move(self, dst, value):
        self.emit('move', dst, value)
        return dst

    def emit_closure(self, res, defn):
        self.emit('closure', res, defn)
        return res

    def emit_branch(self, target):
        assert target.defn is self.defn
        self.emit('branch', target.index)

    def emit_cbranch(self, cond, yes, no):
        assert yes.defn is self.defn
        assert no.defn is self.defn
        self.emit('cbranch', cond, yes.index, no.index)


def build_term(builder, expr):
    if expr.name == 'number':
        return int(expr.value)
    if expr.name == 'string':
        return expr.value[1:-1]
    if expr.name == 'symbol':
        symbol = expr.value
        if symbol == 'true':
            return True
        if symbol == 'false':
            return False
        if symbol == 'null':
            return None
        obj = builder.defn.scope.lookup(symbol)
        if obj is None:
            raise Exception("%s not in scope" % symbol)
        return obj
    raise Exception('unimplemented %s' % expr.name)

def build_call(builder, expr, res):
    first = expr[0]
    if first.name == 'symbol' and first.value in builder.macros:
        return builder.macros[first.value](builder, expr)
    argv = [build_expr(builder, arg) for arg in expr[1:]]
    if first.name == 'attribute':
        name = first[0]
        obj = build_expr(builder, first[1])
        return builder.emit_callattr(res, obj, name, argv)
    else:
        callee = build_expr(builder, first)
        return builder.emit_call(res, callee, argv)

def build_expr(builder, expr, res=None):
    builder.location = expr.location
    if expr.name == 'attribute':
        name = expr[0]
        obj = build_expr(builder, expr[1])
        res = builder.defn.newreg() if res is None else res
        return builder.emit_getattr(res, obj, name)
    if expr.name == 'list':
        res = builder.defn.newreg() if res is None else res
        return build_call(builder, expr, res)
    if res is None:
        return build_term(builder, expr)
    return builder.emit_move(res, build_term(builder, expr))

def build_stmt(builder, expr):
    builder.location = expr.location
    if expr.name == 'list':
        return build_call(builder, expr, None)
    raise Exception('nonsensical %s' % expr.name)

def build_defn(args, body, scope, macros):
    defn = Defn(Scope(scope))
    builder = Builder(defn, macros)
    for arg in args:
        defn.scope[arg] = defn.newarg()
    defn.argc = len(args)
    for stmt in body:
        build_stmt(builder, stmt)
    return defn

def build(body, scope, macros):
    return Closure(None, build_defn([], body, scope, macros))

def toint(expr):
    assert expr.name == 'number'
    return int(expr.value)

def tosymbol(expr):
    assert expr.name == 'symbol'
    return expr.value

def tostring(expr):
    assert expr.name == 'string'
    return expr.value[1:-1]

def tolist(expr):
    assert expr.name == 'list'
    return expr.value


def m_def(builder, expr):
    name = tosymbol(expr[1])
    args = [tosymbol(arg) for arg in tolist(expr[2])]
    res = builder.defn.scope[name] = builder.defn.newreg()
    defn = build_defn(args, expr[3:], builder.defn.scope, builder.macros)
    return builder.emit_closure(res, defn)

def m_lambda(builder, expr):
    args = [tosymbol(arg) for arg in tolist(expr[1])]
    res = builder.defn.newreg()
    defn = build_defn(args, expr[2:], builder.defn.scope, builder.macros)
    return builder.emit_closure(res, defn)

def m_return(builder, expr):
    builder.emit_return(build_expr(builder, expr[1]))

def m_assign(builder, expr):
    scope = builder.defn.scope
    lhs = expr[1]
    if lhs.name == 'attribute':
        rhs = build_expr(builder, expr[2])
        name = lhs[0]
        obj = build_expr(builder, lhs[1])
        return builder.emit_setattr(obj, name, value)
    if lhs.name == 'symbol':
        name = tosymbol(lhs)
        arg = scope.lookup(name)
        assert isinstance(arg, VirtualRegister)
        return build_expr(builder, expr[2], arg)
    raise Exception('unimplemented assign %s' % lhs.name)

def m_let(builder, expr):
    scope = builder.defn.scope
    lhs = expr[1]
    if lhs.name == 'attribute':
        rhs = build_expr(builder, expr[2])
        name = lhs[0]
        obj = build_expr(builder, lhs[1])
        return builder.emit_setattr(obj, name, value)
    if lhs.name == 'symbol':
        name = tosymbol(lhs)
        if name in scope:
            arg = scope[name]
        else:
            arg = scope[name] = builder.defn.newreg()
        return build_expr(builder, expr[2], arg)
    raise Exception('unimplemented let %s' % lhs.name)

def m_if(builder, expr):
    defn = builder.defn
    thenblock = defn.newblock()
    contblock = defn.newblock()
    flag = build_expr(builder, expr[1])
    builder.emit_cbranch(flag, thenblock, contblock)
    builder.block = thenblock
    for stmt in expr[2:]:
        build_stmt(builder, stmt)
    builder.emit_branch(contblock)
    builder.block = contblock
    builder.flag = flag

def m_elif(builder, expr):
    defn = builder.defn
    condblock = defn.newblock()
    thenblock = defn.newblock()
    contblock = defn.newblock()

    flag = builder.flag
    builder.emit_cbranch(builder.flag, contblock, condblock)

    builder.block = condblock
    build_expr(builder, expr[1], flag)
    builder.emit_cbranch(flag, thenblock, contblock)

    builder.block = thenblock
    for stmt in expr[2:]:
        build_stmt(builder, stmt)
    builder.emit_branch(contblock)
    builder.block = contblock
    builder.flag = flag

def m_else(builder, expr):
    defn = builder.defn
    thenblock = defn.newblock()
    contblock = defn.newblock()
    builder.emit_cbranch(builder.flag, contblock, thenblock)
    builder.block = thenblock
    for stmt in expr[1:]:
        build_stmt(builder, stmt)
    builder.emit_branch(contblock)
    builder.block = contblock
    builder.flag = None

def m_while(builder, expr):
    defn = builder.defn
    condblock = defn.newblock()
    loopblock = defn.newblock()
    contblock = defn.newblock()
    builder.emit_branch(condblock)

    builder.block = condblock
    flag = build_expr(builder, expr[1])
    builder.emit_cbranch(flag, loopblock, contblock)

    builder.block = loopblock
    for stmt in expr[2:]:
        build_stmt(builder, stmt)
    builder.emit_branch(condblock)
    builder.block = contblock

macros = {
    'def': m_def,
    'lambda': m_lambda,
    'return': m_return,
    #'yield': m_yield,
    ':=': m_assign,
    '=': m_let,
    'if': m_if,
    'elif': m_elif,
    'else': m_else,
    'while': m_while,
    #'for': m_for,
}
