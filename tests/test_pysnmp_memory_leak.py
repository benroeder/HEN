#!/usr/local/bin/python

import sys
print sys.path
#sys.path.remove('/usr/local/lib/python2.4/site-packages')
#sys.path.append('/site-packages/')
from auxiliary.snmp import SNMP
import gc
import code

#from sizer import scanner, annotate, formatting#, graph

gc.enable()
gc.set_debug(gc.DEBUG_LEAK)

def dump_garbage( ):
    """
    show us what the garbage is about
    """
    # Force collection
    print "\nGARBAGE:"
    gc.collect( )
    print "\nGARBAGE OBJECTS:"
    for x in gc.garbage:
        s = str(x)
        if len(s) > 80: s = s[:77]+'...'
        print type(x),"\n ", s
                                            
def Test1():
    print "Testing creation and deletion of one snmp object"
    s = SNMP("public","192.168.1.2")
    del s
    dump_garbage()
    
def Test2():
    print "Testing getting temperature reading"
    
    s = SNMP("private","192.168.1.9")
    res = s.get(SNMP.extremeCurrentTemperature)
    del s
    del res
    dump_garbage( )
    



Test2()

# old stuff

#Test2()
#print gc.collect(), "unreachable objects"


#objs = scanner.Objects()
#code.interact(local={'objs':objs})

#s = SNMP("private","192.168.1.9")
#res = s.get(SNMP.extremeCurrentTemperature)        
#objs = scanner.Objects()
#code.interact(local = {'objs':objs})

#creators = annotate.findcreators(objs)
#formatting.printsizes(creators.back, count=9)

#fromc = creators.back[("/home/arkell/u0/adam/python/lib/python2.4/site-packages/pysnmp/v4/smi/indices.py",156)]

#formatting.printsizes(fromc.back)

#mods = annotate.simplegroupby(objs, modules = True)
#formatting.printsizes(mods)

#del s
#del res
#objs = scanner.Objects()
#creators = annotate.findcreators(objs)
#formatting.printsizes(creators.back, count=9)



#mods = annotate.simplegroupby(objs, modules = True)
#graph.makegraph(mods,count=15,proportional =True)
