from __future__ import print_function

import types

from .header import *
from . import mdis as dis


class LabelDict(dict):
    def __init__(self):
        dict.__init__(self)
        self.counter = 1

    def __missing__(self, key):
        self[key] = "#G{:04d}".format(self.counter)
        self.counter += 1
        return self[key]


def iter_disassemble(code):
    if isinstance(code, types.FunctionType):
        code = code.__code__
    d_label = LabelDict()
    pos = 0
    tape = []
    while pos < len(code.co_code):
        old_pos = pos

        op = STRUCT_OP.unpack_from(code.co_code, pos)[0]
        pos += OP_LEN
        if op < dis.HAVE_ARGUMENT:
            arg = None
        else:
            arg = STRUCT_ARG.unpack_from(code.co_code, pos)[0]
            pos += ARG_LEN

            if op in dis.hasname:
                arg = code.co_names[arg]
            elif op in dis.hasconst:
                arg = code.co_consts[arg]
            elif op in dis.haslocal:
                arg = code.co_varnames[arg]
            elif op in dis.hasfree:
                if i < len(code.co_cellvars):
                    arg = code.co_cellvars[i]
                else:
                    arg = code.co_freevars[i - len(code.co_cellvars)]
            elif op in dis.hasjrel:
                arg = d_label[pos + arg]
            elif op in dis.hasjabs:
                arg = d_label[arg]

        tape.append([old_pos, op, arg])
    for pos, op, arg in tape:
        if pos in d_label:
            yield 255, d_label[pos]
        yield op, arg


def disassemble(code):
    if isinstance(code, types.FunctionType):
        code = code.__code__
    return list(iter_disassemble(code))


def print_disassemble(code):
    if isinstance(code, types.FunctionType):
        code = code.__code__
    i = 0
    for op, arg in iter_disassemble(code):
        if op == 255:
            print('{:10} {:<13} {:>13}'.format('', arg + ':', ''))
        else:
            if op < dis.HAVE_ARGUMENT:
                arg = ''
            elif op not in dis.hasjrel and op not in dis.hasjabs:
                arg = repr(arg)
            op = dis.opname[op]
            print('{:10d} {:<13} {:>13}'.format(i, op, arg))
            i += 1
