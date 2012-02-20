##################################################################################################################
# moteiv.py: contains the mote subclass for Moteiv motes
#
# CLASSES
# --------------------------------------------------------------------
# MoteivMote                 The class used to support Moteiv motes (derived from the Mote superclass). This class
#                            contains all operations relating to specific Moteiv operations.
# MoteivTmoteskyMote         The class used to support Moteiv Tmote Sky motes. This class contains information
#                            specific to this model of mote (number of ports, etc)
#
##################################################################################################################
import commands, os, string
from hardware.motes.mote import Mote
#from auxiliary.hen import 

OUI = 0x001275

class MoteivMote(Mote):
    def __init__(self, moteNode):
        Mote.__init__(self, moteNode)

class MoteivTmoteskyMote(MoteivMote):
    
    def __init__(self, moteNode):
        MoteivMote.__init__(self, moteNode)
