import logging
import types
import Ft.Xml
import string
import cStringIO
import Ft.Xml.Domlette
from Ft.Xml import EMPTY_NAMESPACE
from Ft.Xml.XPath import Compile, Evaluate
from Ft.Xml.cDomlette import implementation

log = logging.getLogger()

class PredicateConstraint:
    __name = None
    __expression = None
    __params = []
    __targetConfig = None
    __security = 0
    __context = None
    
    def __init__(self,context,name,expression,targetConfig,security,params):
        self.__context = context
        self.__name = name
        self.__expression = expression
        self.__targetConfig = targetConfig
        self.__security = security
        self.__params = params
#        print "Params are "+str(self.__params)

    def getName(self):
        return self.__name
	
    def getSecurity(self):
	return self.__security
        
    def satisfies(self, user, node):
        #build the predicate first
        predicate = self.__expression
        
        for (toReplace,path,data) in self.__params:
            if data=="!user!":
                if (self.__security!=1):
                    return (0,"cannot use !user! in non-security predicate!")
                value = user
            else:
                if path==None:
                    object = node
                else:
                    res = Evaluate(path,node,self.__context)
                    if (res==None or len(res)==0):
                        return (0, "object of type "+node.localName+ " does not have "+path)
                    object = res[0]
                        
                what = getattr(object,data)
        
                if (callable(what)):
                    value = what()
                else:
                    value = what
            
            predicate = predicate.replace(toReplace,value)
        
        if self.__targetConfig!=None:
            target_node = self.__targetConfig
        else:
            target_node = node
        
        #execute predicate
        if self.__security==1:
            print "Security predicate for "+str(target_node)+" is "+predicate
        else:
            print "Normal predicate for "+str(target_node)+" is "+predicate
            
        result = Evaluate(predicate,target_node,self.__context)
        print "res:",result
        
        return result=="true"

class NodeConstraints:
    __softConfig = None
    __hardConfig = None
    __parent = None
    __dtd = {}
    __constraints = {}
    __predicateDependency = {}
    __allowedOperations = {}
    
    def __init__(self, parent, path, context):
        cfg = Ft.Xml.Domlette.ValidatingReader.parseUri(path)
        self.__softConfig = parent.getSoftConfig()
        self.__hardConfig = parent.getHardConfig()
        self.__parent = parent
        
        constraints = cfg.xpath("/properties/constraints/constraint")
        for c in constraints:
            tag = c.attributes[(None,u'tag')].value
            
            if (c.attributes.has_key((None,u'dtd'))):
                try:
                    f = open(c.attributes[(None,u'dtd')].value,"r")
                    self.__dtd[tag] = f.read()
                    f.close()
                except Exception,e:
                    log.debug(str(e))
            
            self.__allowedOperations[tag] = c.attributes[(None,u'allowedOperations')].value.split(",")

            predicateDependency = c.xpath("child::predicatechild")
            for dep in predicateDependency:
                tagDep = dep.attributes[(None,u'tag')].value
                if (not self.__predicateDependency.has_key(tag)):
                    self.__predicateDependency[tag] = []
                self.__predicateDependency[tag].append(tagDep)
            
            predicates = c.xpath("child::predicate")
            
            for pred in predicates:
                t = pred.attributes[(None,u'targetConfig')].value
                if (t=="hard"):
                    target = self.__hardConfig
                elif (t=="soft"):
                    target = self.__softConfig
                else:
                    target = None
                    
                expression = pred.attributes[(None,u'expression')].value
                name = pred.attributes[(None,u'name')].value
                security = string.atoi(pred.attributes[(None,u'security')].value)
                
                params = []
                ps = pred.xpath("child::param")
                for p in ps:
                    toReplace = p.attributes[(None,u'toReplace')].value
                    if (p.attributes.has_key((None,u'path'))):
                        path = p.attributes[(None,u'path')].value
                    else:
                        path = None
                    data = p.attributes[(None,u'data')].value
                    params.append((toReplace,path,data))
                
                pc = PredicateConstraint(context,name,expression,target,security,params)
                
                if (not self.__constraints.has_key(tag)):
                    self.__constraints[tag] = []
                
                self.__constraints[tag].append(pc)
                
    def __checkNodeDTD(self, newNode):
        if (not self.__dtd.has_key(newNode.localName)):
            return (1,"no dtd specified for tag "+str(newNode.localName))
        
#        print "Checking dtd for node "+newNode.localName
        
        node = self.__softConfig.createDocumentFragment()
        node.appendChild(newNode.cloneNode(1))
        
        s = cStringIO.StringIO()
        Ft.Xml.Domlette.Print(node,s)
        
        doc = self.__dtd[newNode.localName]+s.getvalue()
        try:
            Ft.Xml.Domlette.ValidatingReader.parseString(doc,"dtd_check")
            return (1,"")
        except Exception,e: 
            print "exceptie", e, "\n",doc
            return (0,str(e)+" for tag "+newNode.localName)

    def __checkNodeConstraints(self, user, newNode, security = 0):
#        print "Checking security="+str(security)+" constraints for node "+newNode.localName
        toCheck = [newNode]
        chk = 0
        
        while len(toCheck)>0:
            nodeToCheck = toCheck.pop()
        
            if self.__constraints.has_key(nodeToCheck.localName):
                for constraint in self.__constraints[nodeToCheck.localName]:
                    if (constraint.getSecurity()==security):
                        chk = chk + 1
                        if (constraint.satisfies(user,nodeToCheck) == 0):
                            return (0,"Predicate "+constraint.getName()+" not satisfied for node "+nodeToCheck.localName)
                    
            if self.__predicateDependency.has_key(nodeToCheck.localName):
                for tag in self.__predicateDependency[nodeToCheck.localName]:
                    toCheck.extend(nodeToCheck.xpath("child::"+tag))
        
        if (chk==0 and security==1):
            return (0,"No security constraints specified")
	
        return (1,"")
    
    def __allowed(self,node,action):
        if not self.__allowedOperations.has_key(node.localName):
            return 0
        return (action in self.__allowedOperations[node.localName])

    def actionAllowed(self,node,value,action):
        if (self.__allowed(node, "update")==0):
            return (0, "cannot update "+node.localName)
        
        if (action.find("Attribute")!=-1):
            return (1,"")
        
        if (self.__allowed(value,action)==0):
            return (0,"cannot "+action+" "+value.localName)
        
        return (1,"")

    def checkPermissions(self,user,newNode):
        return self.__checkNodeConstraints(user,newNode,1)
        
    def checkNode(self,newNode):
        (ret,val) = self.__checkNodeDTD(newNode)
        if (ret==0):
            return (ret,val)
            
        return self.__checkNodeConstraints(None, newNode,0)