from lisp import read, sourcelines
import machinecode, virtualmachine, ffi
import sys

class Native(object):
    def __init__(self, fn):
        self.fn = fn

    def vm_call(self, args):
        return self.fn(*args)

scope = machinecode.Scope()
scope['cdll'] = Native(ffi.CDLL)
scope['length'] = Native(len)
scope['pointer'] = Native(ffi.ctypes.pointer)
scope['byref'] = Native(ffi.byref)

import operator

scope['!='] = Native(operator.ne)
scope['=='] = Native(operator.eq)
scope['<='] = Native(operator.le)
scope['>='] = Native(operator.ge)
scope['<'] = Native(operator.lt)
scope['>'] = Native(operator.gt)

def debug(*args):
    print ' '.join(repr(a) for a in args)
scope['debug'] = Native(debug)

source = read.file(sys.argv[1])

#print sourcelines.color(out.location)

closure = machinecode.build(source, scope, machinecode.macros)

print closure
for block in closure.defn.blocks:
    print block

frame, res = virtualmachine.run(closure, [])

closure = frame.lookup('main')
print closure
for block in closure.defn.blocks:
    print block
