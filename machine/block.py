class Block(object):
    def __init__(self, label=None):
        self.label = label
        self.instr = []
        self.term = None
        self.phi = {} # label:block:arg where (block in prec[self])

    @property
    def successors(self):
        return self.term[2:]

    def __repr__(self):
        if self.label is not None:
            return self.label
        else:
            return "<block %x>" % id(self)

class Instruction(object):
    def __init__(self, name, args, label):
        self.name = name
        self.args = args
        self.label = label

    def __repr__(self):
        if self.label is not None:
            return "%s_%x" % (self.label, id(self))
        else:
            return "_%x" % id(self)

class Builder(object):
    def __init__(self, dst):
        self.dst = dst

    def emit(self, name, args, label):
        assert self.dst.term is None
        x = Instruction(name, args, label)
        self.dst.instr.append(x)
        return x

    def call(self, callee, *args):
        return self.emit('call', [callee] + list(args), None)

    def getattr(self, obj, name):
        return self.emit('getattr', [obj, name], None)

    def setattr(self, obj, name, value):
        return self.emit('setattr', [obj, name, value], None)

    def callattr(self, obj, name, *argv):
        return self.emit('callattr', [obj, name] + list(argv), None)

    def terminate(self, *term):
        assert self.dst.term is None
        self.dst.term = term

    def cbranch(self, cond, yes, no):
        yes = yes.dst if isinstance(yes, Builder) else yes
        no  = no.dst if isinstance(no, Builder) else no
        self.terminate('cbranch', cond, yes, no)

    def branch(self, target):
        target  = target.dst if isinstance(target, Builder) else target
        self.terminate('branch', None, target)

    def ret(self, arg):
        self.terminate('ret', arg)

    def assign(self, obj, label):
        if isinstance(obj, Instruction):
            instruction = obj
        else:
            instruction = self.emit('const', [obj], None)
        instruction.label = label
        return instruction

def unbound(label):
    return Instruction('unbound', [], label)
