class Device:
    """\brief Super-class for all devices. Any common methods should be
    declared here.
    """
    
    """
    Holds acceptable sensor classes. The corresponding dictionar value indicates
    whether critical values for this type are an UPPER or LOWER bound on the
    acceptable (safe) range. 0 = UPPER, 1 = LOWER
        Temperature - in degrees Celsius
        Fanspeed - in RPM (revs per minute)
        Current - in Amps
        Voltage - in Volts
        Alarm - discrete value: 0 = OK, 1 = ALARM
        
    NOTE: For alarms, this also works. Just set a critical value of alarms to 1,
    so that if a reading gives a value of 1, it triggers an alert.
    """
    SENSOR_CLASSES = { \
                      'temperature':0, \
                      'fanspeed':1, \
                      'current':0, \
                      'voltage':0, \
                      'alarm':0 \
                      }
    
    def getSensorClasses(self):
        return self.SENSOR_CLASSES.keys()
    
    def getBoundTypeFromClass(self, sensorClass):
        if self.SENSOR_CLASSES.has_key(sensorClass):
            return self.SENSOR_CLASSES[sensorClass]
        return None
    
    def getEmptySensorDictionary(self):
        sensorDictionary = {}
        for sensorClass in self.SENSOR_CLASSES.keys():
            sensorDictionary[sensorClass] = {}
        return sensorDictionary
    
    def getSensorDescriptions(self):
        """\brief Requires overriding.
        If overridden, this method needs to return a dictionary of dictionaries,
        with the form {sensortype:{sensorname:criticalvalue,...},...}, i.e.

                SENSOR_DESCRIPTIONS = {'fanspeed':{'fan1.span':500,
                                                   'fan2.span':500},
                                       'temperature':{'chassistemp1':70,
                                                      'cpu0.memtemp':80}}
        """
        return None
    
    def getSensorReadings(self):
        """\brief Requires overriding.
        If overridden, this method needs to return a dictionary of dictionaries,
        with the form:
                {sensortype:{sensorname:currentvalue,...},...}
        Example:
                return {'fanspeed':{'fan1.span':2134,'fan2.span':3222}}
        """
        return None
    
    def getSensorClassFromName(self, sensorDescriptions, sensorid):
        """\brief Handy method for looking up the sensor class of a given 
        sensor name, using the given sensor description dictionaries.
        """
        for className in sensorDescriptions.keys():
            for sensorName in sensorDescriptions[className].keys():
                if sensorName == sensorid:
                    return className
        return None
    