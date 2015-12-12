from collections import defaultdict
import types

from .header import *
from . import mdis as dis
from .disassemble import iter_disassemble


class UniqueList:
    def __init__(self):
        self.values = []

    def __getitem__(self, value):
        try:
            return self.values.index(value)
        except ValueError:
            self.values.append(value)
            return len(self.values) - 1

    def tuple(self):
        return tuple(self.values)


def _assemble(asm_code, co_freevars=(), co_cellvars=()):
    label = {}
    rel_label = defaultdict(dict)
    abs_label = defaultdict(set)

    bytecode = []
    co_names = UniqueList()
    co_consts = UniqueList()
    co_varnames = UniqueList()

    pos = 0
    for op, arg in asm_code:
        if type(op) == str:
            op = dis.opmap[op]
        if op == 255:
            label[arg] = pos
            if arg in rel_label:
                for slot, rmt_pos in rel_label[arg].items():
                    bytecode[slot] = STRUCT_ARG.pack(pos - rmt_pos)
                del rel_label[arg]
            if arg in abs_label:
                bytecode_pos = STRUCT_ARG.pack(pos)
                for slot in abs_label[arg]:
                    bytecode[slot] = bytecode_pos
                del abs_label[arg]
            continue

        bytecode.append(STRUCT_OP.pack(op))
        pos += OP_LEN

        if op in dis.hasjabs:
            if arg in label:
                arg = label[arg]
            else:
                pos += ARG_LEN
                abs_label[arg].add(len(bytecode))
                bytecode.append(0)
                continue
        if op in dis.hasjrel:
            if arg in label:
                arg = label[arg] - pos - ARG_LEN
            else:
                pos += ARG_LEN
                rel_label[arg][len(bytecode)] = pos
                bytecode.append(0)
                continue

        if op < dis.HAVE_ARGUMENT:
            continue

        if op in dis.hasname:
            arg = co_names[arg]
        elif op in dis.hasconst:
            arg = co_consts[arg]
        elif op in dis.haslocal:
            arg = co_varnames[arg]
        elif op in dis.hasfree:
            if i < len(co_cellvars):
                arg = co_cellvars[i]
            else:
                arg = co_freevars[i - len(co_cellvars)]
        bytecode.append(STRUCT_ARG.pack(arg))
        pos += ARG_LEN

    if rel_label or abs_label:
        raise SyntaxError('Unknown labels')
    return ''.join(bytecode), \
        co_names.tuple(), co_consts.tuple(), co_varnames.tuple()


def assemble(
        asm_code, co_argcount=0, co_stacksize=16, co_flags=64,
        co_filename='<asm>', co_name='<bytecode>', co_firstlineno=1,
        co_lnotab='\x00', co_freevars=(), co_cellvars=()):
    co_code, co_names, co_consts, co_varnames = \
        _assemble(asm_code, co_freevars, co_cellvars)
    '''[
        code.co_argcount,  code.co_nlocals,     code.co_stacksize,
        code.co_flags,     code.co_code,        code.co_consts,
        code.co_names,     code.co_varnames,    code.co_filename,
        code.co_name,      code.co_firstlineno, code.co_lnotab,
        code.co_freevars,  code.co_cellvars
    ]'''
    return types.CodeType(
        co_argcount, len(co_varnames), co_stacksize,
        co_flags, co_code, co_consts,
        co_names, co_varnames, co_filename,
        co_name, co_firstlineno, co_lnotab,
        co_freevars, co_cellvars)


def _get_literal_expression(code):
    tape = []
    iter_code = iter_disassemble(code)
    for op, arg in iter_code:
        if op == dis.opmap['LOAD_GLOBAL'] and arg in dis.opmap:
            literal_op = dis.opmap[arg]
            if literal_op < dis.HAVE_ARGUMENT:
                literal_arg = None
            else:
                fake_op, literal_arg = next(iter_code)
                if fake_op == dis.opmap['LOAD_CONST']:
                    next(iter_code)
            next(iter_code)
            tape.append((literal_op, literal_arg))
        else:
            tape.append((op, arg))
    return tape


def use_assemble(obj):
    if type(obj) == int:
        co_stacksize = obj
    else:
        co_stacksize = 16

    def wrapper(func):
        code_obj = func.__code__
        code = assemble(
            _get_literal_expression(code_obj),
            co_argcount=code_obj.co_argcount, co_stacksize=co_stacksize,
            co_flags=code_obj.co_flags, co_filename=code_obj.co_filename,
            co_name=code_obj.co_name, co_firstlineno=code_obj.co_firstlineno,
            co_freevars=code_obj.co_freevars, co_cellvars=code_obj.co_cellvars)
        return types.FunctionType(
            code, func.__globals__, func.__name__,
            func.__defaults__, func.__closure__)
    if type(obj) == int:
        return wrapper
    else:
        return wrapper(obj)
