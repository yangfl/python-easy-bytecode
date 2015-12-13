from __future__ import absolute_import, print_function

import ebc

@ebc.use_assemble
def foo(a, *b):
    LOAD_FAST .a
    POP_TOP

    LOAD_CONST -(-1)
    STORE_FAST -'1'

    LOAD_GLOBAL -'print'
    LOAD_FAST -'1'
    CALL_FUNCTION -1
    POP_TOP

    LABEL -'1'
    if a > 1:
        JUMP_ABSOLUTE -2
    JUMP_ABSOLUTE -'end'

    LABEL -2
    a -= 1
    print(a)
    JUMP_ABSOLUTE -'1'

    LABEL -'end'


import dis
dis.dis(foo)
foo(9)
