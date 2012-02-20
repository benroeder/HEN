import logging
import types
import Ft.Xml
import string
import cStringIO
import Ft.Xml.Domlette
from Ft.Xml import EMPTY_NAMESPACE
from Ft.Xml.cDomlette import implementation
import imp

log = logging.getLogger()

loadedModules = {}

def getModule(name):
    global loadedModules
    if (loadedModules.has_key(name)):
        return loadedModules[name]
    else:
        try:
            f= imp.find_module(name)
        except Exception, e:
            log.error(str(e))
            return None
        
        try:
            loadedModules[name] = imp.load_module(name,f[0],f[1],f[2])
            f[0].close
        except Exception,e:
            log.error(str(e))
            f[0].close
            return None
            
        return loadedModules[name]     

def trigger_cmp(s1,s2):
    return cmp(s1.getTrigger().getPhase(),s2.getTrigger().getPhase())

class Trigger:
    __handler = None
    __phase = None
    __action = None
    __tag = None
    
    def __init__(self, module, handler, phase,tag,action):
        self.__phase = phase
        self.__tag = tag
        self.__action = action
        
        mod = getModule(module)
        if (mod==None):
            return
        
        try:
            self.__handler = getattr(mod, handler)
        except Exception,e:
            log.error("Cannot find method "+handler+" of module "+module+" because:"+str(e))
        
    def getAction(self):
        return self.__action

    def getTag(self):
        return self.__tag

    def getPhase(self):
        return self.__phase

    def runTrigger(self,paramOld,paramNew):
        if (self.__handler!=None):
            	return self.__handler(self.__tag,self.__action, paramOld,paramNew)
        else:
            	log.error("Trying to run None handler!")
		return (404,"Trying to run none handler!")

    def getInstance(self, paramOld, paramNew):
	       return SpecificTrigger(self,paramOld,paramNew)
    
class SpecificTrigger(Trigger):
    __oldState = None
    __newState = None
    __trigger = None
    
    def __init__(self, trigger, paramOld, paramNew):
        self.__trigger = trigger
        self.__oldState = paramOld
        self.__newState = paramNew
    
    def getTrigger(self):
        return self.__trigger
        
    def executeTrigger(self):
        return self.__trigger.runTrigger(self.__oldState,self.__newState)

class ActionTriggers:
    __triggers = {}
    
    def __init__(self, parent, path):	
        cfg = Ft.Xml.Domlette.ValidatingReader.parseUri(path)
        self.__parent = parent
        
        triggers = cfg.xpath("/properties/triggers/trigger")
        for t in triggers:
            tag = t.attributes[(None,u'tag')].value
            action = t.attributes[(None,u'action')].value
            module = t.attributes[(None,u'module')].value
            handler = t.attributes[(None,u'handler')].value
            phase = string.atoi(t.attributes[(None,u'phase')].value)

            trigger = Trigger(module,handler,phase,tag,action)
                
            if (not self.__triggers.has_key(tag)):
                self.__triggers[tag] = {}
            if (not self.__triggers[tag].has_key(action)):
                self.__triggers[tag][action] = []
                
            self.__triggers[tag][action].append(trigger)
    
    def getTriggers(self, tag, action):
        if (not self.__triggers.has_key(tag)):
            return []
        if (not self.__triggers[tag].has_key(action)):
            return []
        
        return self.__triggers[tag][action]
    
    def instantiateTriggers(self, tag, action, oldParam, newParam):
        list = self.getTriggers(tag, action)

        ret = []
        for t in list:
            ret.append(t.getInstance(oldParam,newParam))
            
        return ret
