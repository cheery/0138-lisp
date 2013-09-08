from block import Block, Builder, unbound
import analysis

# constructs the following program into memory:
# a = 1
# x = 12
# while x > 1
#     a *= x
#     x -= 1
# return a

b0 = Block('b0') # in bytecode, you can jump to the start of a block.
b1 = Block('b1')
b2 = Block('b2')
b3 = Block('b3')

bb0 = Builder(b0) # this thing is used to push instructions into the block.
bb1 = Builder(b1)
bb2 = Builder(b2)
bb3 = Builder(b3)

# bb0:
#     a = 1
#     x = 12
bb0.assign(1,  'a') # designed to be converted into static single assignment form. The label is used to connect the values together.
bb0.assign(12, 'x')
bb0.branch(bb1)

# bb1:
#     while x > 1
bb1.cbranch( # I replace strings with direct references to correct objects later.
    bb1.call('lt', unbound('x'), 1),
    bb2, bb3)
# bb2:
#     a *= x
#     x -= 1
bb2.assign(bb2.call('mul', unbound('a'), unbound('x')), 'a')
bb2.assign(bb2.call('sub', unbound('x'), 1), 'x')
bb2.branch(bb1)
# bb3:
#     return a
bb3.ret(unbound('a'))


flow = analysis.flow(b0)
liveness = analysis.liveness(flow)
dominance = analysis.dominance(flow)
frontiers = analysis.frontiers(flow, dominance)

print flow.blocks
print flow.succ
print flow.prec
for key, arg in liveness.intro.items():
    print 'def', key, arg
for key, lives in liveness.live.items():
    print key, lives
print dominance.idom
print dominance.domi
print frontiers

#import objects
#
#class Instruction(object):
#    def __init__(self, block, *args):
#        self.block = block
#        block.append(self)
#        self.args = []
#        self.uses = set()
#        for arg in args:
#            self.using(arg)
#            self.args.append(arg)
#
#    def __getitem__(self, index):
#        return self.args[index]
#
#    def using(self, arg):
#        if hasattr(arg, 'uses'):
#            arg.uses.add(self)
#    def drop_using(self, arg):
#        if hasattr(arg, 'uses'):
#            arg.uses.discard(self)
#
#    def replace(self, arg, other):
#        self.args[self.args.index(arg)] = other
#        self.drop_using(arg)
#        self.using(other)
#
#    def substitute(self, replacement):
#        for use in list(self.uses):
#            use.replace(self, replacement)
#        self.free()
#
#    def free(self):
#        assert len(self.uses) == 0
#        self.block.remove(self)
#        self.block = None
#        for arg in self.args:
#            self.drop_using(arg)
#
#    def __repr__(self):
#        which = self.__class__.__name__
#        return "%s(%s)" % (which, ', '.join(repr(a) for a in self.args))
#
#class Call(Instruction):
#    def is_supernumerary(self):
#        uniform = self[0].vm_uniform
#        for arg in self[1:]:
#            if isinstance(arg, Instruction):
#                uniform = False
#        return uniform
#
#entry = []
#
#a = Call(entry, objects.add, 5, 6)
#b = Call(entry, objects.mul, a, 2)
#c = Call(entry, objects.debug, b)
#
#
#
#
#print entry
#
## optimization
#loose = [instr for instr in entry if instr.is_supernumerary()]
#while len(loose) > 0:
#    instr = loose.pop()
#    uses = instr.uses.copy()
#    res = instr[0].vm_call(instr[1:])
#    instr.substitute(res)
#    loose.extend(use for use in uses if use.is_supernumerary())
#
#print 'after optimization'
#print entry
#
##main = defn()
##
##entry = main.block()
##cond  = main.block()
##end   = main.block()
##
##entry.call(f_print, ["hello"])
