import logging
import Ft.Xml
import Ft.Xml.Domlette
from nodeconstraint import PredicateConstraint
from Ft.Xml import EMPTY_NAMESPACE
from Ft.Xml.cDomlette import implementation
import imp

log = logging.getLogger()

class InitData:
    __initData = {}
    __hardConfig = None
    __softConfig = None

    def __init__(self, path,context,config):    
        cfg = Ft.Xml.Domlette.ValidatingReader.parseUri(path)
        
        initializers = cfg.xpath("/properties/initializers/initializer")
        for t in initializers:
		textToInsert = str(t.attributes[(None,u'toinsert')].value)
		textToInsert = textToInsert.replace("&lt;","<")
		textToInsert = textToInsert.replace("&gt;",">")
		print textToInsert
		toInsert = Ft.Xml.Domlette.NonvalidatingReader.parseString(textToInsert,'http://').firstChild
		Ft.Xml.Domlette.PrettyPrint (toInsert) 

		if (not self.__initData.has_key(toInsert)):
			self.__initData[toInsert] = []
		
		predicates = t.xpath("child::predicate")
		for pred in predicates:
                	t = pred.attributes[(None,u'targetConfig')].value
                	if (t=="hard"):
                    		target = config
                	elif (t=="soft"):
                    		log.error("soft config cannot be used as a target for initdata!")
                	else:
                    		target = None

                	expression = pred.attributes[(None,u'expression')].value
                	name = pred.attributes[(None,u'name')].value
                	#security = string.atoi(pred.attributes[(None,u'security')].value)

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

                	pc = PredicateConstraint(context,name,expression,target,0,params)

                	self.__initData[toInsert].append(pc)
    
    def getAddList(self,node):
		res = []
		for k in self.__initData.keys():
			ok = True
			for pred in self.__initData[k]:
				if (not pred.satisfies(None,node)):
					ok = False
					break
			if (ok==True):
				res.append(k.cloneNode(1))
        	return res
