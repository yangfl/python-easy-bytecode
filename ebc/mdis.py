import copy
from dis import opname, opmap, cmp_op, HAVE_ARGUMENT, \
    hasconst, hasfree, hasname, hasjrel, hasjabs, haslocal, hascompare

opname = copy.copy(opname)
opname[255] = 'LABEL'

opmap = copy.copy(opmap)
opmap['LABEL'] = 255
