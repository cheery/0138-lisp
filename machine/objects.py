import operator

class MachineObject(object):
    vm_uniform = False
    def vm_call(self, args):
        raise Exception("cannot call this")
    def vm_getattr(self, name):
        raise Exception("cannot get attribute of this object")
    def vm_setattr(self, name, value):
        raise Exception("cannot set attribute of this object")

class Native(MachineObject):
    def __init__(self, uniform, fn):
        self.vm_uniform = uniform
        self.fn = fn
    def vm_call(self, args):
        return self.fn(*args)
    def __repr__(self):
        return 'native(uniform=%r)' % self.vm_uniform

def native(uniform):
    return (lambda fn: Native(uniform, fn))

# number operators
add = Native(True, operator.add)
sub = Native(True, operator.sub)
mul = Native(True, operator.mul)
div = Native(True, operator.div)
mod = Native(True, operator.mod)
pow = Native(True, operator.pow)

# boolean operators
lt = Native(True, operator.lt)
gt = Native(True, operator.gt)
le = Native(True, operator.le)
ge = Native(True, operator.ge)
ne = Native(True, operator.ne)
eq = Native(True, operator.eq)
and_ = Native(True, operator.and_)
or_ = Native(True, operator.or_)
not_ = Native(True, operator.not_)

# bit level operations
ior = Native(True, operator.ior)
ixor = Native(True, operator.ixor)
iand = Native(True, operator.iand)
inv = Native(True, operator.inv)
rshift = Native(True, operator.rshift)
lshift = Native(True, operator.lshift)

@native(False)
def debug(obj):
    print repr(obj)
