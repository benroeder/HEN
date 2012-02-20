from Ft.Xml.XPath import Conversions
import Ft.Xml
import Ft.Xml.Domlette
from Ft.Xml.XPath.Context import Context

class NodeIdentity:
    MAX_CACHE = 2000
    DELETE_ENTRIES = 100
    __uidCache = {}
    __uidLRU = []
    __nodePrimaryAttributes = {}
    
    def __init__(self, constraints):
        constraints = Ft.Xml.Parse(constraints).xpath("/properties/constraints/constraint")
        for constraint in constraints:
            if constraint.attributes.has_key((None,u'primaryAttributes')):
                tag = constraint.attributes[(None,u'tag')].value
                
                attr = constraint.attributes[(None,u'primaryAttributes')].value
                if attr!="":
                    self.__nodePrimaryAttributes[tag] = attr.split(",")
                else:
                    self.__nodePrimaryAttributes[tag]= []
#                print tag,self.__nodePrimaryAttributes[tag]

    def check_uniqueness(self,context, nodes):
        '''available in XPath as check-uniqueness'''
        hash = {}
        
        for n in nodes:
            h = self.nodeUID(n)
            if (hash.has_key(h)):
                return Conversions.BooleanValue(0)
            hash[h] = 1
        
        return Conversions.BooleanValue(1)
    #return time.asctime(time.localtime())
    def attrname_compare(self,x, y):
        (a1,b1) = x
        (a1,b2) = y
        return cmp(b1,b2)

    def nodeUID(self,node):
        if (self.__uidCache.has_key(node)):
            return self.__uidCache[node]
        
        uid = node.localName

        if (self.__nodePrimaryAttributes.has_key(node.localName)):
            
            for attr in self.__nodePrimaryAttributes[node.localName]:
                if (node.attributes.has_key((None,attr))):
                    uid = uid +","+ attr+"="+str(node.attributes[(None,attr)].value)
        else:
            #all attributes must be the same
            if (node.attributes==None):
                return uid
            lst = node.attributes.keys()
            lst.sort(self.attrname_compare)
            for (x,attr) in lst:
                uid = uid +","+ attr+"="+str(node.attributes[(x,attr)].value)
        
        #store in cache
        if (len(self.__uidLRU)>self.MAX_CACHE):
            #delete DELETE_ENTRIES entries from cache
            print "Performing cache cleanup"
            i = 0
            while i<self.DELETE_ENTRIES:
                n = self.__uidLRU.pop(0)
                del self.__uidCache[n]
                i = i+1
        
        self.__uidLRU.append(node)
        self.__uidCache[node] = uid

        return uid