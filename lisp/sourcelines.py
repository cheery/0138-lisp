HEADER = '\033[95m'
OKBLUE = '\033[94m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

def plain((start, stop, path)):
    with open(path) as fd:
        lines = fd.readlines()
    k1 = 0
    res = []
    for lineno, line in enumerate(lines, 1):
        k0 = k1
        k1 += len(line)
        line = line.strip('\r\n')
        include = False

        print line, k0, stop, k1,  k0 <= stop < k1
        print line, k0, start, k1, k0 <= start < k1
        if k0 <= stop <= k1:
            include = True
        if k0 <= start <= k1:
            include = True
        if start <= k0 and k1 <= stop:
            include = True

        if include:
            fmt = " %3i  %s"
            res.append(fmt % (lineno, line))
    return '\n'.join(res)

def color((start, stop, path), color=FAIL):
    with open(path) as fd:
        lines = fd.readlines()
    k1 = 0
    res = []
    for lineno, line in enumerate(lines, 1):
        k0 = k1
        k1 += len(line)
        line = line.strip('\r\n')
        include = False

        if k0 <= stop <= k1:
            cut = stop - k0
            line = line[:cut] + ENDC + line[cut:]
            include = True
        else:
            line = line + ENDC
        if k0 <= start <= k1:
            cut = start - k0
            line = line[:cut] + color + line[cut:]
            include = True
        else:
            line = color + line
        if start <= k0 and k1 <= stop:
            include = True

        if include:
            fmt = HEADER+" %3i"+ENDC+"  %s"
            res.append(fmt % (lineno, line))
    return '\n'.join(res)
