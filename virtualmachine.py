import machinecode

def run(closure, argv):
    root = frame = machinecode.Frame(None, closure)
    frame.pass_arguments(argv)
    while True:
        if frame.pc >= len(frame.block):
            if frame is root:
                return root, None
            else:
                frame = frame.ret.resume(None)
                continue
        instr = frame.block[frame.pc]
        frame.pc += 1
        name = instr[0]
        if name == 'call':
            frame.entryvar = instr[1]
            callee = frame.fetch(instr[2])
            argv = [frame.fetch(arg) for arg in instr[3:]]
            if isinstance(callee, machinecode.Closure):
                frame = machinecode.Frame(frame, callee)
                if not frame.pass_arguments(argv):
                    raise Exception("too few arguments")
            else:
                frame.store(frame.entryvar, callee.vm_call(argv))
        elif name == 'return':
            if frame is root:
                return root, None
            else:
                frame = frame.ret.resume(frame.fetch(instr[1]))
        elif name == 'getattr':
            obj = frame.fetch(instr[2])
            name = frame.fetch(instr[3])
            frame.store(instr[1], obj.vm_getattr(name))
        elif name == 'setattr':
            obj = frame.fetch(instr[1])
            name = frame.fetch(instr[2])
            obj.vm_setattr(name, frame.fetch(instr[3]))
        elif name == 'callattr':
            frame.entryvar = instr[1]
            obj = frame.fetch(instr[2])
            name = frame.fetch(instr[3])
            argv = [frame.fetch(arg) for arg in instr[4:]]
            callee = obj.vm_getattr(name)
            if isinstance(callee, machinecode.Closure):
                frame = machinecode.Frame(frame, callee)
                if not frame.pass_arguments(argv):
                    raise Exception("too few arguments")
            else:
                frame.store(frame.entryvar, callee.vm_call(argv))
        elif name == 'move':
            frame.store(instr[1], frame.fetch(instr[2]))
        elif name == 'closure':
            frame.store(instr[1], machinecode.Closure(frame, instr[2]))
        elif name == 'branch':
            frame.block = frame.closure.defn.blocks[instr[1]]
            frame.pc = 0
        elif name == 'cbranch':
            cond = frame.fetch(instr[1])
            if cond:
                frame.block = frame.closure.defn.blocks[instr[2]]
            else:
                frame.block = frame.closure.defn.blocks[instr[3]]
            frame.pc = 0
        else:
            raise Exception("no such instruction %s" % name)
