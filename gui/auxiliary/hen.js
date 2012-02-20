/**
 * @fileoverview  Implements several common GUI classes
 *
 * CLASSES
 * --------------------------------------------
 * Tab        Super class for all tabs in the GUI 
 * Rack       Contains information about a rack and how to display it
 * Node       Contains information about a node and how to display it
 * User       Contains information about a user
 * SensorNode Contains information about a sensor node
 * Experiment Contains information about an experiment
 * DateRange  A date range consists of a start date and an end date, both in DD/MM/YYYY format
 * AsynchronousRequest Used to send and receive asynchronous requests
 * @version 0.1
 */
Namespace("auxiliary.hen");
Import("auxiliary.draw", ".", "/");


// ***************************************************
// ***** CLASS: Tab **********************************
// ***************************************************
auxiliary.hen.Tab = function()
{
  // The tab's label
  this.tabLabel = null;
  // The tab's main div object
  this.tabMainDiv = null;
  // The logged in user's information
  this.user = null;
  // The divs whose style.visibility property has been set manually (not through parent)
  this.visibilityDivs = new Array();
  // Whether the tab has been displayed, used to know whether to create the tab's elements
  this.notYetShown = true;
  // A user belonging to any of these groups is allowed to see the tab
  this.allowedGroups = new Array();
  // Used to save the visibility states of divs before hiding a tab
  var savedVisibility = new Array();
  // Used to draw divs with
  var drawHelper = new auxiliary.draw.DrawHelper();
  // Used to hold a reference to the div holding the loading animated gif
  var loadingDiv = null;

  this.getTabLabel = function getTabLabel()
  {
    return this.tabLabel;
  };

  this.getAllowedGroups = function getAllowedGroups()
  {
    return this.allowedGroups;
  };

  this.setUser = function setUser(user)
  {
    this.user = user;
  }

  this.setVisibility = function setVisibility(visibility)
  {
    var runInit = false;
    if ( (this.notYetShown) && (visibility == "visible") )
    {
      this.notYetShown = false;
      this.initTab();
      runInit = true;
    }

    this.tabMainDiv.style.visibility = visibility;

    // Before hiding the tab we must save the divs' visibility states
    if (visibility == "hidden") 
    {
      if (savedVisibility.length == 0)
      {
	for (var i = 0; i < this.visibilityDivs.length; i++)
	  savedVisibility.push(this.visibilityDivs[i].style.visibility);
	
	for (var i = 0; i < this.visibilityDivs.length; i++)
	  this.visibilityDivs[i].style.visibility = visibility;
      }
    }
    // To show the tab once again we must restore the divs' visibility states
    else if (!runInit)
    {
      for (var i = 0; i < this.visibilityDivs.length; i++)
	this.visibilityDivs[i].style.visibility = savedVisibility[i];
      savedVisibility.length = 0;
    }
  };

  this.createTab = function createTab()
  {
    var div = document.createElement("div");
    div.setAttribute("id", this.getTabLabel() + "Tab");
    this.tabMainDiv = div;
    return div;
  };

  this.showLoadingDiv = function showLoadingDiv(xPos, yPos)
  {
    loadingDiv = drawHelper.createLoadingDiv(xPos, yPos);
    this.tabMainDiv.appendChild(loadingDiv);
  };

  this.hideLoadingDiv = function hideLoadingDiv()
  {
    if (loadingDiv)
      this.tabMainDiv.removeChild(loadingDiv);
  }
}


// ***************************************************
// ***** CLASS: Rack *********************************
// ***************************************************
auxiliary.hen.Rack = function(rackID, rackPosition, rackHeight, rackWidth, nodes, rearRackWidth) 
{
  this.rackID = rackID;
  this.rackPosition = Number(rackPosition);
  this.rackHeight = Number(rackHeight);
  this.rackWidth = Number(rackWidth);
  this.nodes = nodes;
  this.frontDiv = document.createElement("div");
  this.rearDiv = document.createElement("div");
  this.rearRackWidth = rearRackWidth;
}


// ***************************************************
// ***** CLASS: Node *********************************
// ***************************************************
auxiliary.hen.Node = function(nodeID, nodeType, startUnit, endUnit, position)
{
  this.nodeID = nodeID;
  this.nodeType = nodeType;
  if (startUnit != null)
    this.startUnit = Number(startUnit);
  else
    this.startUnit = null;
  if (endUnit != null)
    this.endUnit = Number(endUnit);
  else
    this.endUnit = null;

  this.endUnit = Number(endUnit);
  this.position = position;
}

// ***************************************************
// ***** CLASS: User *********************************
// ***************************************************
auxiliary.hen.User = function(username, password, email, groups)
{
  this.username = username;
  this.password = password;
  this.email = email;
  this.groups = groups;


  this.isManager = function isManager()
  {
    for (var i = 0; i < this.groups.length; i++)
      if (this.groups[i] == "henmanager")
	return true;
    return false;
  };
}

/**
 * Holds the status of a Node, as given by MonitorD
 * @class NodeStatus
 * @param {String} id The NodeID
 * @param {int} status The node's overall status (0=OK,1=WARNING,2=CRITICAL)
 * @param {Array} sensors Array of SensorStatus classes 
 * describing the node's sensor statuses.
 */
auxiliary.hen.NodeStatus = function NodeStatus(id, status, sensors)
{
  this.id = id;
  this.status = status;
  this.sensors = sensors;
};

/**
 * Holds the status of a Node's Sensor, as given by MonitorD
 * @class SensorStatus
 * @param {String} id The Sensor ID (i.e. cpu0.temp)
 * @param {String} type The Sensor Type (i.e. temperature)
 * @param {int} time The time when the last reading was taken, in secs since epoch
 * @param {float} val The current sensor value
 * @param {float} maxval The maximum recorded sensor value since MonitorD restart
 * @param {int} status The current sensor status (0=OK,1=WARNING,2=CRITICAL)
 */
auxiliary.hen.SensorStatus = function SensorStatus(id, type, time, val, maxval, status)
{
  this.id = id;
  this.type = type;
  this.time = time;
  this.val = val;
  this.maxval = maxval;
  this.status = status;
};

/**
 * Used to send asynchronous requests
 * @class AsynchronousRequest
 * @constructor
 * @param {String} requestPage The URL to send the request to
 * @param {function} handler The response's handler
 * @return A new AsynchronousRequest object
 */
auxiliary.hen.AsynchronousRequest = function AsynchronousRequest(requestPage, handler)
{
  // The page to send the request to
  var requestPage = requestPage;
  // The response's handler
  var handler = handler;
  // The actual asynchronous request object
  var requestObject = null;

  /** 
   * Gets the asynchronous request object
   * @return {XmlHttpRequest} The asynchronous request object
   */
  this.getRequestObject = function getRequestObject() { return requestObject; };

  /**
   * Gets the asynchronous request's ready state
   * @return {int} The ready state
   */
  this.getReadyState = function getReadyState() { return requestObject.readyState; };

  /**
   * Gets the asynchronous request's status
   * @return {int} The status
   */
  this.getStatus = function getStatus() { return requestObject.status; };
  
  /**
   * Gets the asynchronous request's response XML
   * @return {XML} The response XML
   */
  this.getResponseXML = function getResponseXML() { return requestObject.responseXML; };

  /**
   * Gets the asynchronous request's response text
   * @return {String} The response text
   */
  this.getResponseText = function getResponseText() { return requestObject.responseText; };

  /**
   * Send the asynchronous request
   */
  this.send = function send()
  {
    requestObject = new XMLHttpRequest();
    requestObject.onreadystatechange = handler;
    requestObject.open("GET", requestPage, true);
    requestObject.send(null);
  }
};

/**
 * Holds information about an experiment on the testbed.
 * @class Experiment
 * @constructor
 * @param {String} experimentID The experiment's id
 * @param {auxiliary.hen.User} user The experiment's owner
 * @param {Date} startDate The experiment's start date
 * @param {Date} endDate The experiment's end date
 * @param {Array of String} nodeIDs A list of the ids for the nodes the experiment uses
 * @param {boolean} shared Whether the user is not the direct owner of the experiment
 * @return A new Experiment object
 */
auxiliary.hen.Experiment = function Experiment(experimentID, user, startDate, endDate, nodeIDs, shared)
{
  var experimentID = experimentID;
  var user = user;
  var startDate = startDate;
  var endDate = endDate;
  var nodeIDs = nodeIDs;
  var shared = shared;

  /**
   * Gets the experiment id
   * @return {String} The experiment's id
   */
  this.getExperimentID = function getExperimentID() { return experimentID; };

  /**
   * Gets the experiment owner
   * @return {auxiliary.hen.User} The experiment's owner
   */
  this.getUser = function getUser() { return user; };

  /**
   * Gets the experiment start date
   * @return {Date} The experiment's start date
   */
  this.getStartDate = function getStartDate() { return startDate; };

  /**
   * Gets the experiment end date
   * @return {Date} The experiment's end date
   */
  this.getEndDate = function getEndDate() { return endDate; };

  /**
   * Gets a list of ids for the nodes the experiment uses
   * @return {Array of String} The node ids
   */
  this.getNodeIDs = function getNodeIDs() { return nodeIDs; };

  /**
   * Gets whether the user directly owns the exeriment or not
   * @return {boolean} Whether the user directly owns the exeriment or not
   */
  this.getShared = function getShared() { return shared; };

  /**
   * Returns a string with the object's information
   * @return {String} The object's information
   */
  this.toString = function toString() 
  {
    return "Experiment:" +
      "\nexperimentID: " + this.getExperimentID() +
      "\nuser: " + this.getUser() + 
      "\nstartDate: " + this.getStartDate() +
      "\nendDate: " + this.getEndDate() + 
      "\nnodeIDs: " + this.getNodeIDs() + 
      "\nshared: " + this.getShared();
  };
}; 

/**
 * Holds information about a date range. A date range consists of two Date objects and the id of the experiment 
 * that the range refers to.
 * @class DateRange
 * @constructor
 * @param {Date} startDate The range's start date
 * @param {Date} endDate The range's end date
 * @param {String} experimentID The id of the experiment that the range refers to.
 * @return A new DateRange object
 */
auxiliary.hen.DateRange = function DateRange(startDate, endDate, experimentID)
{
  var startDate = startDate;
  var endDate = endDate;
  var experimentID = experimentID;

  /**
   * Gets the range's start date
   * @return {Date} The range's start date
   */
  this.getStartDate = function getStartDate() { return startDate; };

  /**
   * Gets the range's end date
   * @return {Date} The range's end date
   */
  this.getEndDate = function getEndDate() { return endDate; };

  /**
   * Gets the experiment id
   * @return {String} The experiment's id
   */
  this.getExperimentID = function getExperimentID() { return experimentID; };

  /**
   * Returns a string with the object's information
   * @return {String} The object's information
   */
  this.toString = function toString() 
  {
    return "DateRange:" +
      "\nstartDate: " + this.getStartDate() +
      "\nendDate: " + this.getEndDate() + 
      "\nexperimentID: " + this.getExperimentID();
  };
}; 



// *****************************************************************************
// **************** FUNCTIONS **************************************************
// *****************************************************************************
/**
 * Retrieves an attribute's value from an xml tag.
 * @param {Element} obj The xml containing the attribute to retrieve
 * @param {String} attribute The name of the attribute to retrieve
 * @return {String} The attribute's value, or null if the tag did not have the specified attribute
 */
auxiliary.hen.getAttributeValue = function(obj, attribute) 
{
  if (!obj)
    return null;

  if (obj.attributes[attribute])
    return obj.attributes[attribute].value;
  
  return null;
}

/**
 * Trims the elementName portion of a string of the form [elementName][number]
 * @param {String} label The labe to trim
 * @param {int} The amount of characters that the elementName portion of the string should have after trimming
 * @return {String} The trimmed label
 */
auxiliary.hen.trimLabel = function (label, labelLength)
{
  if (label.length <= labelLength)
    return label;

  // Find first numeric character
  var i;
  for (i = 0; i < label.length; i++)
  {
    var c = label.charAt(i);
    if (!(c < "0" || c > "9"))
      break;
  }

  var nodeType = label.substring(0, i);
  var numberCharsToTrim = label.length - labelLength;
  return label.substring(0, i - numberCharsToTrim) + label.substring(i, label.length);
}
