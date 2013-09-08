class Instruction(object):
    def __init__(self, block, args, label=None):
        self.args  = list(args)
        self.label = label
        self.uses = set()
        for arg in args:
            arg.uses.add(self)
        block.append(self)

    def __setitem__(self, index, arg):
        assert not isinstance(index, slice)
        self.args[index] = arg
        if isinstance(arg, Instruction):
            arg.uses.add(self)

    def __getitem__(self, index):
        return self.args[index]

    def __len__(self):
        return len(self.args)

    def __iter__(self):
        return iter(self.args)

    def index(self, arg):
        return self.args.index(arg)

    def free(self):
        for arg in self:
            arg.uses.discard(self)
        assert len(self.uses) == 0
        block.remove(self)

    def propagate(self, value):
        for use in list(self.uses):
            use.replace(self, value)
        self.free()
