import ctypes
from clang.cindex import *

def locate(node, name, parent=None, depth=''):
    if node.spelling and node.spelling == name:
        return node, parent
    if node.displayname and node.displayname == name:
        return node, parent
    for child in node.get_children():
        res = locate(child, name, node, depth+'    ')
        if res is not None:
            return res

class Primitive(object):
    def __init__(self, ctype):
        self.ctype = ctype

    def __repr__(self):
        return 'Primitive(%r)' % self.ctype

class Pointer(object):
    def __init__(self, pointee):
        self.pointee = pointee
        self.ctype = ctypes.POINTER(pointee.ctype)

class FuncType(object):
    def __init__(self, restype, argtypes):
        self.restype = restype
        self.argtypes = argtypes
        self.ctype = ctypes.CFUNCTYPE(restype.ctype, *[arg.ctype for arg in argtypes])

class Record(object):
    def __init__(self, fields, name='record'):
        self.fields = dict(fields)
        cfields = [(name, t.ctype) for name, t in fields]
        self.ctype = type(name, (ctypes.Structure,), {"_fields_":cfields})

    def vm_call(self, args):
        return FFIInstance(self.ctype(*args))

class Union(object):
    def __init__(self, fields, name='union'):
        self.fields = dict(fields)
        cfields = [(name, t.ctype) for name, t in fields]
        self.ctype = type(name, (ctypes.Union,), {"_fields_":cfields})

    def vm_call(self, args):
        return FFIInstance(self.ctype(*args))

class FFIInstance(object):
    def __init__(self, pointer):
        self._as_parameter_ = pointer

    def vm_getattr(self, name):
        return getattr(self._as_parameter_, name)

    def vm_setattr(self, name, value):
        return setattr(self._as_parameter_, name, value)

def byref(obj):
    if isinstance(obj, FFIInstance):
        return ctypes.byref(obj._as_parameter_)
    return ctypes.byref(obj)

def lookup_macro_constant(node):
    extent = node.extent
    start, end = extent.start, extent.end
    with open(start.file.name) as fd:
        a = start.offset + len(node.displayname)
        b = end.offset
        data = fd.read()[a:b].strip()
        if data.isdigit():
            return int(data)
        if data.startswith('0x'):
            return int(data, 16)
        if data.startswith('"') and data.endswith('"'):
            return data[1:-1]
        raise Exception("no interpretation found for %r" % data)

def clang_to_type(typecache, t):
    t = t.get_canonical()
    if t.kind == TypeKind.POINTER:
        return Pointer(clang_to_type(typecache, t.get_pointee()))
    if t.kind == TypeKind.VOID:
        return Primitive(None)
    if t.kind == TypeKind.INT:
        return Primitive(ctypes.c_int)
    if t.kind == TypeKind.UINT:
        return Primitive(ctypes.c_uint)
    if t.kind == TypeKind.LONG:
        return Primitive(ctypes.c_long)
    if t.kind == TypeKind.ULONG:
        return Primitive(ctypes.c_ulong)
    if t.kind == TypeKind.CHAR_S:
        return Primitive(ctypes.c_char)
    if t.kind == TypeKind.UCHAR:
        return Primitive(ctypes.c_ubyte)
    if t.kind == TypeKind.USHORT:
        return Primitive(ctypes.c_ushort)
    if t.kind == TypeKind.SHORT:
        return Primitive(ctypes.c_short)
    if t.kind == TypeKind.ENUM:
        return clang_to_type(typecache, t.get_declaration().enum_type)
        #return Primitive(ctypes.c_ulong) # 'lol hm.. not so lol anymore.'
    if t.kind == TypeKind.RECORD:
        rec = t.get_declaration()
        name = rec.spelling
        if name in typecache:
            return typecache[name]
        cls = {
            CursorKind.UNION_DECL: Union,
            CursorKind.STRUCT_DECL: Record,
        }[rec.kind]
        fields = []
        for child in rec.get_children():
            fields.append((child.spelling, clang_to_type(typecache, child.type)))
        typecache[name] = res = cls(fields, name)
        return res
    if t.kind == TypeKind.FUNCTIONPROTO:
        argtypes = [clang_to_type(typecache, arg) for arg in t.argument_types()]
        restype = clang_to_type(typecache, t.get_result())
        return FuncType(restype, argtypes)
    raise Exception("no type mapping for %r" % t.kind)

def get_enum_constant(node, parent):
    const = 0
    for item in parent.get_children():
        for info in item.get_children():
            assert info.kind == CursorKind.INTEGER_LITERAL
            const = lookup_macro_constant(info)
        if node.spelling == item.spelling:
            return const
        const += 1
    raise Exception("odd or invalid input for this function")

args = ['-D_Noreturn=__attribute__ ((__noreturn__))']
class Header(object):
    def __init__(self, path):
        self.index = index = Index.create()
        self.translation_unit = index.parse(path, args, options=0x5)
        self.typecache = {}

    def lookup(self, name):
        tc = self.translation_unit.cursor
        res = locate(self.translation_unit.cursor, name)
        if res is not None:
            node, parent = res
            if node.kind == CursorKind.ENUM_CONSTANT_DECL:
                return get_enum_constant(node, parent)
            if node.kind == CursorKind.MACRO_DEFINITION:
                return lookup_macro_constant(node)
            return clang_to_type(self.typecache, node.type.get_canonical())

class CFunc(object):
    def __init__(self, fn, type):
        self.fn = fn
        self.type = type
    def vm_call(self, argv):
        return self.fn(*argv)

class CDLL(object):
    def __init__(self, path, *headers):
        self.path = path
        self.headers = [Header(header) for header in headers]
        self.lib = ctypes.CDLL(path)
        self.cache = {}

    def get_decl(self, name):
        if name in self.cache:
            return self.cache[name]
        for header in self.headers:
            result = header.lookup(name)
            if result is not None:
                self.cache[name] = result
                return result
        raise Exception("no type declaration found from headers %r" % name)
    
    def vm_getattr(self, name):
        decl = self.get_decl(name)
        if isinstance(decl, FuncType):
            cfunc = getattr(self.lib, name)
            cfunc.restype = decl.restype.ctype
            cfunc.argtypes = [arg.ctype for arg in decl.argtypes]
            return CFunc(cfunc, decl)
        else: 
            return decl #otherwise it's a constant or typedecl itself
