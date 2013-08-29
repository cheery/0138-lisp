class Failure(Exception):
    def __init__(self, message, location):
        self.message = message
        self.location = location

class Node(object):
    def __init__(self, name, value, location):
        self.name = name
        self.value = value
        self.location = location

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        return iter(self.value)

    def __getitem__(self, index):
        return self.value[index]

    def __repr__(self):
        return 'Node(%r, %r, %r)' % (self.name, self.value, self.location)

class Reader(object):
    def create(self, name, location, value=None):
        value = self.value if value is None else value
        self.parent.value.append(Node(name, value, location))
        return self.parent

class List(Reader):
    def __init__(self, parent, start):
        self.parent = parent
        self.start = start
        self.value = []

    def __call__(self, index, ch, loc):
        if ch.isdigit():
            return Number(self, index, ch)
        if ch in ('"', "'"):
            return String(self, index, ch)
        if ch == '(':
            return List(self, index)
        if ch == ')':
            if self.parent is None:
                raise Failure('missing left parenthesis', loc(index, index+1))
            return self.create('list', loc(self.start, index+1))
        if ch == '#':
            return Comment(self, index)
        if ch == '.':
            return Attribute(self, index, '')
        if ch.isspace():
            return self
        return Symbol(self, index, ch)

    def done(self, index, loc):
        if self.parent is None:
            return Node('list', self.value, loc(self.start, index))
        raise Failure('missing right parenthesis', loc(self.start, self.start+1))

class Number(Reader):
    def __init__(self, parent, start, value):
        self.parent = parent
        self.start = start
        self.value = value

    def __call__(self, index, ch, loc):
        if ch.isalnum() or ch == '.':
            self.value += ch
            return self
        else:
            location = loc(self.start, index)
            return self.create('number', location)(index, ch, loc)

    def done(self, index, loc):
        location = loc(self.start, index)
        return self.create('number', location).done(index, loc)

class String(Reader):
    def __init__(self, parent, start, value):
        self.parent = parent
        self.start = start
        self.value = value

    def __call__(self, index, ch, loc):
        self.value += ch
        if ch == self.value[0]:
            return self.create('string', loc(self.start, index+1))
        return self

    def done(self, index, loc):
        raise Failure("unterminated string", loc(self.start, index))

class Symbol(Reader):
    def __init__(self, parent, start, value):
        self.parent = parent
        self.start = start
        self.value = value

    def __call__(self, index, ch, loc):
        if not ch.isspace() and ch not in ('#', '(', ')', '"', "'", "."):
            self.value += ch
            return self
        else:
            location = loc(self.start, index)
            return self.create('symbol', location)(index, ch, loc)

    def done(self, index, loc):
        location = loc(self.start, index)
        return self.create('symbol', location).done(index, loc)

class Attribute(Reader):
    def __init__(self, parent, start, value):
        self.parent = parent
        self.start = start
        self.value = value

    def capture(self):
        if len(self.parent.value) > 0:
            return self.parent.value.pop(-1)

    def __call__(self, index, ch, loc):
        if not ch.isspace() and ch not in ('#', '(', ')', '"', "'", "."):
            self.value += ch
            return self
        else:
            value = [self.value, self.capture()]
            location = loc(self.start, index)
            return self.create('attribute', location, value)(index, ch, loc)

    def done(self, index, loc):
        value = [self.value, self.capture()]
        location = loc(self.start, index)
        return self.create('attribute', location, value).done(index, loc)

class Comment(Reader):
    def __init__(self, parent, start):
        self.parent = parent
        self.start = start

    def __call__(self, index, ch, loc):
        if ch == '\n':
            return self.parent
        return self

    def done(self, index, loc):
        return self.parent.done(index, loc)

def string(source, path):
    loc = lambda start, stop: (start, stop, path)
    reader = List(None, 0)
    for j, ch in enumerate(source):
        reader = reader(j, ch, loc)
    return reader.done(len(source), loc)

def file(path):
    with open(path) as fd:
        return string(fd.read(), path)

if __name__=='__main__':
    import sourcelines, sys

    def dump(expr):
        if not isinstance(expr, Node):
            return
        print '%s' % expr.name
        print sourcelines.color(expr.location, sourcelines.OKBLUE)
        if isinstance(expr.value, list):
            for ch in expr:
                dump(ch)
    try:
        source = file(sys.argv[1])
        dump(source)
    except Failure, e:
        print e.message
        print sourcelines.color(e.location)
