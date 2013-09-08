from block import Instruction

class Flow(object):
    def __init__(self, entry, blocks, succ, prec):
        self.entry = entry
        self.blocks = blocks
        self.succ = succ
        self.prec = prec

def push(dct, key, item): # utility function
    if key in dct:
        dct[key].append(item)
    else:
        dct[key] = [item]

def flow(entry):
    succ = {}
    prec = {entry:[]}
    blocks = set([entry])
    unvisited = [entry]
    while len(unvisited) > 0:
        block = unvisited.pop()
        succ[block] = []
        for target in block.term[2:]:
            if not target in blocks:
                unvisited.append(target)
                blocks.add(target)
            push(succ, block, target)
            push(prec, target, block)
    return Flow(entry, blocks, succ, prec)

# utility function, again
def get_label(obj):
    return obj.label if isinstance(obj, Instruction) else None

def is_unbound(obj):
    return isinstance(obj, Instruction) and obj.name == 'unbound'

class Liveness(object):
    def __init__(self, live, intro):
        self.live = live
        self.intro = intro

def liveness(flow):
    live = dict((block, set()) for block in flow.blocks)
    livelen = {}
    defs = {}
    # initial setup
    for block in flow.blocks:
        liveset = set()
        defset  = set()
        if is_unbound(block.term[1]):
            liveset.add(block.term[1].label)
        for instr in reversed(block.instr):
            if instr.label:
                defset.add(instr.label)
                liveset.discard(instr.label)
            liveset.update(arg.label for arg in instr.args if is_unbound(arg))
        defs[block] = defset
        for prec in flow.prec[block]:
            live[prec].update(liveset)
    changing = True
    while changing:
        changing = False
        for block in flow.blocks:
            if len(live[block]) != livelen.get(block, 0):
                changing = True
            livelen[block] = len(live[block])
            liveset = live[block].copy()
            liveset.difference_update(defs[block])
            for prec in flow.prec[block]:
                live[prec].update(liveset)
    intro = {}
    for block in flow.blocks:
        liveset = live[block]
        introset = set()
        for instr in block.instr:
            if instr.label in liveset:
                introset.add(instr)
        intro[block] = introset
    return Liveness(live, intro)

class Dominance(object):
    def __init__(self, idom, domi):
        self.idom = idom
        self.domi = domi

def dominance(flow):
    idom = {flow.entry:None}
    layer = {flow.entry:0}
    domi = {}
    breath = [flow.entry]
    while len(breath) > 0:
        block = breath.pop(0)
        for successor in flow.succ[block]:
            if successor in idom:
                a, b = block, successor
                layer_a = layer[a]
                layer_b = layer[b]
                floor = min(layer_a, layer_b)
                for _ in range(floor, layer_a):
                    a = idom[a]
                for _ in range(floor, layer_b):
                    b = idom[b]
                while a is not b:
                    a = idom[a]
                    b = idom[b]
                dominator = a
            else:
                dominator = block
                breath.append(successor)
            if successor is not dominator:
                idom[successor] = dominator
                layer[successor] = layer[dominator] + 1
                print 'idom[%r] = %r (l%i)' % (successor, dominator, layer[dominator] + 1)
    for dst, src in idom.items():
        if src is not None:
            push(domi, src, dst)
    return Dominance(idom, domi)

def frontiers(flow, dominance):
    frontiers = dict((block,[]) for block in flow.blocks)
    for block in flow.blocks:
        if len(flow.prec[block]) >= 2:
            for runner in flow.prec[block]:
                while runner != dominance.idom[block]:
                    push(frontiers, runner, block)
                    runner = dominance.idom[runner]
    return frontiers
