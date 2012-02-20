#!/usr/local/bin/python
import auxiliary.protocol
import pickle, os, sys

class ReservationClient:
    
    def __init__(self):
        self.__daemon = auxiliary.protocol.Protocol(None)
        self.__results = None

    def connect(self, daemonIP, daemonPort):
        self.__daemon.open(daemonIP, daemonPort)

    def close(self):
        self.__daemon.close()

    def sendRequest(self, command, payload):
        self.__daemon.sendRequest(command, payload, self.handler)
        self.__daemon.readAndProcess()
        return self.__results

    def sendAsyncRequest(self, command, payload):
        self.__daemon.sendRequest(command, payload, None)
        #self.__daemon.readAndProcess()
        return 
    
    def handler(self, code, seq, sz,payload):
        self.__results = pickle.loads(payload)
