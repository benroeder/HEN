//**********************************************************************************
//**********************************************************************************
// Implements the components.status.status namespace
//
// CLASSES
// --------------------------------------------
// StatusTab    Displays and manages the "Status" tab
//
//
// Modified from original StatusTab code by munlee 
//**********************************************************************************
//**********************************************************************************
Namespace("components.status.status");
Import("auxiliary.hen", ".", "/");
Import("auxiliary.draw", ".", "/");


// ***************************************************
// ***** CLASS: StatusTab ***********************
// ***************************************************
components.status.status.StatusTab = function()
{
  // Necessary to keep reference to 'this' for event handlers 
  var me = this;
  // The x start position of the control div
  this.X_CONTROL_PANEL_START_POSITION = 10;
  // The y start position of the control div
  this.Y_CONTROL_PANEL_START_POSITION = 45;
  // The width of the control div
  this.CONTROL_PANEL_WIDTH = 120;
  // The height of the control div
  this.CONTROL_PANEL_HEIGHT = 200;
  // The distance between the control panel and the left-hand unit labels
  this.CONTROL_PANEL_SPACER = 20;
  // The vertical distance between the control and legend panels
  this.PANELS_SPACER = 10;
  // The y start position of the legned div
  this.Y_LEGEND_PANEL_START_POSITION = this.Y_CONTROL_PANEL_START_POSITION + this.CONTROL_PANEL_HEIGHT + this.PANELS_SPACER;
  // The height of the legend div
  this.LEGEND_PANEL_HEIGHT = 300;
  // The width of a wide rack 
  this.WIDE_RACK_WIDTH = 140;
  // The width of a narrow rack 
  this.NARROW_RACK_WIDTH = this.WIDE_RACK_WIDTH - 25;
  // The width of a single vertical unit 
  this.VERTICAL_UNIT_WIDTH = 12;
  // The number of line breaks in a vertical node's text label 
  this.VERTICAL_FUDGE_FACTOR = 10; 
  // The total number of vertical slots that a rack can have 
  this.MAX_NUMBER_VERTICAL_SLOTS = 4;
  // The maximum number of characters for a node label 
  this.MAX_NODE_LABEL_LENGTH = 10;
  // The height of a single unit 
  this.UNIT_HEIGHT = 12;  
  // The number of pixels separating racks 
  this.INTER_RACK_GAP_LENGTH = 10;
  // The width of the div containing a unit label 
  this.LABEL_WIDTH = 20;
  // The height of the div containing a unit label 
  this.LABEL_HEIGHT = 20;
  // The x start position for the unit labels
  this.X_LABEL_START_POSITION = this.X_CONTROL_PANEL_START_POSITION + this.CONTROL_PANEL_WIDTH + this.CONTROL_PANEL_SPACER;
  // The y start position for the rack labels
  this.Y_RACK_LABEL_START_POSITION = 30;
  // The height of the div containing a rack label 
  this.RACK_LABEL_HEIGHT = 15;
  // The number of horizontal pixels between the unit labels and the racks
  this.LABEL_SPACER = 10;
  // The x start position for drawing the racks 
  this.X_DRAW_START_POSITION = this.X_LABEL_START_POSITION + this.LABEL_WIDTH + this.LABEL_SPACER;  
  // The y start position for the unit labels 
  this.Y_LABEL_START_POSITION = this.Y_RACK_LABEL_START_POSITION + this.RACK_LABEL_HEIGHT;
  // The y start position for drawing the racks 
  this.Y_DRAW_START_POSITION = this.Y_LABEL_START_POSITION;
  // The number of vertical pixels between the bottom of the racks and the control buttons 
  this.BUTTONS_SPACER = 25;
  // The width of the switch views button 
  this.TOGGLE_BUTTON_WIDTH = 110;
  // The height of the switch views button 
  this.TOGGLE_BUTTON_HEIGHT = 30;
  // Used to vertically center a node's label 
  this.TEXT_HEIGHT = 8;
  // The width of the pop-up information box 
  this.INFODIV_WIDTH = 200;
  // The height of the pop-up information box 
  this.INFODIV_HEIGHT = 200;
  // The x position of the pop-up information box
  this.INFODIV_X_POSITION = 400;
  // The y position of the pop-up information box
  this.INFODIV_Y_POSITION = 200;
  // The id of the pop-up information box div 
  this.INFODIV_ID = "infodiv";
  // The id of the div for the close button inside the pop-up information box div 
  this.INFODIVCLOSE_ID = "infodivclose";
  // The width of the pop-up information box 
  this.GRAPHDIV_WIDTH = 800;
  // The height of the pop-up information box 
  this.GRAPHDIV_HEIGHT = 200;  
  // The id of the pop-up graph box div 
  this.GRAPHDIV_ID = "graphdiv";  
  // The x position of the pop-up graph box
  this.GRAPHDIV_X_POSITION = 300;
  // The y position of the pop-up graph box
  this.GRAPHDIV_Y_POSITION = 250;
  // The id of the div for the close button inside the pop-up graph box div 
  this.GRAPHDIVCLOSE_ID = "graphdivclose";
  // polling time for status data
  this.TEMPCGI_TIMEOUT_MILISECONDS = 8 * 1000;
  // The back end url for the location information 
  this.PHYSICAL_LOCATION_URL = "/cgi-bin/gui/components/status/physicallocationcgi.py";
  // The x position of the loading animated div
  this.LOADING_DIV_X_POSITION = 500;
  // The y position of the loading animated div
  this.LOADING_DIV_Y_POSITION = 300;


  this.NODES_WITH_SENSORS = new Array();
  this.STATUS_LEVELS = new Array();
  this.STATUS_LEVELS["OFF"] = "white";
  this.STATUS_LEVELS["NORMAL"] = "lightblue";
  this.STATUS_LEVELS["PALE_NORMAL"] = "#E0FFFF"; // light cyan
  this.STATUS_LEVELS["WARNING"] = "orange";
  this.STATUS_LEVELS["CRITICAL"] = "red";
  this.STATUS_LEVELS["ONLINE"] = "green";
  this.STATUS_LEVELS["OFFLINE"] = "maroon";
  this.STATUS_LEVELS["UNKNOWN"] = "lightgrey";

  this.tempMaxNumberRackUnits = null;

  this.theTempRacks = new Array();
  this.tempDrewRear = false;
  this.tempInfoDiv = null;

  this.nodeTempXHR = null;
  this.nodeTempXmlHttp = null;
  this.tempXmlHttp = null;
  this.tempCurrentView = "front";

  this.tabLabel = "Status";
  this.allowedGroups.push("henmanager");

  // Used to create various divs for text and nodes 
  this.drawHelper = new auxiliary.draw.DrawHelper();

  this.mainDiv = null;


  this.initTab = function initTab() 
  {
    me.showLoadingDiv(200, 200);    
    me.tempXmlHttp = new XMLHttpRequest();
    var requestPage = me.PHYSICAL_LOCATION_URL;
    me.tempXmlHttp.onreadystatechange = me.handleStatusReply;
    me.tempXmlHttp.open("GET", requestPage, true);
    me.tempXmlHttp.send(null);
  };



  this.drawTempNode = function drawTempNode(id, divclass, xPos, yPos, numberUnits, unitHeight,
        rackWidth, maxNodeLabelLength, textHeight, callback) 
  {

    var div = me.drawHelper.createAbsoluteDiv(
            id,
            divclass,
            xPos,
            yPos,
            rackWidth,
            (numberUnits * unitHeight) - 1,
            "1",
            "0px",
            "#000000 1px solid");
    div.onclick = callback;

    // Create text div
    var divID = id + "text";
    var textDiv = me.drawHelper.addTextDiv(
            divID,
            "status-nodetext",
            auxiliary.hen.trimLabel(id, maxNodeLabelLength),
            div,
            numberUnits,
            textHeight);
    return div;
  };


  
  this.drawTempVerticalNode = function drawTempVerticalNode(id, divclass, xPos, yPos, numberUnits,
        unitHeight, rackWidth, numberLineBreaks, callback) 
  {
    var div = me.drawHelper.createAbsoluteDiv(
        id,
        divclass,
        xPos,
        yPos,
        rackWidth,
        (numberUnits * unitHeight) - 1,
        "1",
        "0px",
        "#000000 1px solid");
    div.onclick = callback;

    var textDiv = me.drawHelper.createRelativeDiv(
        id + "text",
        divclass,
        0,
        0,
        rackWidth,
        (numberUnits * unitHeight) - 3,
        "1",
        "0px",
        "#000000 0px solid");

    var innerHTML = "";
    for (var i = 0; i < numberLineBreaks; i++) {
        innerHTML += "<br>";
    }

    for (var i = 0; i < id.length; i++) {
        innerHTML += "&nbsp;" + id.charAt(i) + "<br>";
    }
    textDiv.innerHTML = innerHTML;
    div.appendChild(textDiv);

    return div;
  };



  this.drawUnsupportedNode = function drawUnsupportedNode(id, xPos, yPos, rackWidth, unitHeight) 
  {
    return me.drawHelper.createAbsoluteDiv(
        id,
        "off",
        xPos,
        yPos,
        rackWidth,
        unitHeight - 1,
        "1",
        "0px",
        "#000000 1px solid");
  };



  this.drawTempVerticalBlankNode = function drawTempVerticalBlankNode(id, xPos, yPos, width, numberUnits, unitHeight) 
  {
    return me.drawHelper.createAbsoluteDiv(
        id,
        "off",
        xPos,
        yPos,
        width,
        numberUnits * unitHeight - 1,
        "1",
        "0px",
        "#000000 1px solid");
  };



  this.drawSwitchViewButton = function drawSwitchViewButton(id, buttonClass, xPos, yPos, width, height, buttonText, callback, textHeight) 
  {
    var button = me.drawHelper.createAbsoluteDiv(
        id,
        buttonClass,
        xPos,
        yPos,
        width,
        height,
        "1",
        "0px",
        "#000000 1px solid");
    button.onclick = callback;

    // Create text div
    var divID = id + "text";
    var textDiv = me.drawHelper.addTextDiv(divID, buttonClass, buttonText, button, 2, textHeight);
    return button;
  };


  
  this.drawRackUnitLabels = function drawRackUnitLabels(xPos, yPos, id, numberUnits, unitHeight, labelWidth, labelHeight, unitLabelClass) 
  {
    var labelsDiv = document.createElement("div");
    me.tabMainDiv.appendChild(labelsDiv);
    labelsDiv.setAttribute("id", "templabelsDiv");

    for (var i = numberUnits; i > 0; i--) 
    {
      labelsDiv.appendChild(
	   me.drawRackLabel(id + String(i) + "templabel",
            unitLabelClass,
            xPos,
            yPos + (numberUnits - i) * unitHeight,
            String(i),
            labelWidth,
            labelHeight));
    }
  };



  this.drawRackLabel = function drawRackLabel(id, labelClass, xPos, yPos, labelText, labelWidth, labelHeight) 
  {
    var style = "position:absolute; top:" + yPos + 
                "; left:" + xPos + 
                "; width:" + labelWidth + 
                "; height:" + labelHeight + 
                "; z-index:1" +
                "; padding:0px;";

    var labeldiv = document.createElement("div");
    labeldiv.setAttribute("style", style);
    labeldiv.setAttribute("class", labelClass);
    labeldiv.setAttribute("id", id);

    textNode = document.createTextNode(labelText);
    labeldiv.appendChild(textNode);
    return labeldiv;
  };



  this.handleStatusReply = function handleStatusReply() 
  {
    if (me.tempXmlHttp.readyState == 4) 
    {
      if (me.tempXmlHttp.status == 200) 
      {
	var xmlDoc = me.tempXmlHttp.responseXML;
	var row = xmlDoc.getElementsByTagName("row")[0];
	var racks = row.getElementsByTagName("rack");

	var rack;
	for (var i = 0; i < racks.length; i++) 
	{
	  var rackID = auxiliary.hen.getAttributeValue(racks[i], "id");
	  var rackPosition = auxiliary.hen.getAttributeValue(racks[i], "rowposition");
	  var rackHeight = auxiliary.hen.getAttributeValue(racks[i], "height");
	  var rackWidth = auxiliary.hen.getAttributeValue(racks[i], "width");
	  var nodesArray = new Array();
	  
	  var nodes = racks[i].getElementsByTagName("node");
	  var node;
	  for (var j = 0; j < nodes.length; j++) 
	  {
	    var nodeID = nodes[j].attributes["id"].value;
	    var nodeType = nodes[j].attributes["type"].value;
	    var startUnit = auxiliary.hen.getAttributeValue(nodes[j], "rackstartunit");
	    var endUnit = auxiliary.hen.getAttributeValue(nodes[j], "rackendunit");
	    var position = auxiliary.hen.getAttributeValue(nodes[j], "position");
		    
	    node = new auxiliary.hen.Node(nodeID, nodeType, startUnit, endUnit, position);
	    nodesArray.push(node);
	  }
          if (rackWidth == "narrow")
            rackWidth = me.NARROW_RACK_WIDTH;
          else if (rackWidth == "wide")
            rackWidth = me.WIDE_RACK_WIDTH;

          var rearRackWidth = rackWidth - 4 * me.VERTICAL_UNIT_WIDTH;
          rack = new auxiliary.hen.Rack(rackID, rackPosition, rackHeight, rackWidth, nodesArray, rearRackWidth);
          me.theTempRacks.push(rack);
	}
	
        // Remove loading gif
	me.hideLoadingDiv();

	me.tempMaxNumberRackUnits = -1;
	for (var i = 0; i < me.theTempRacks.length; i++) 
	{
	  if (me.theTempRacks[i].rackHeight > me.tempMaxNumberRackUnits)
	    me.tempMaxNumberRackUnits = me.theTempRacks[i].rackHeight;
	}

        // Create control panel div
        var controlPanelDiv = document.createElement("div");
        me.tabMainDiv.appendChild(controlPanelDiv);
        controlPanelDiv.setAttribute("id", "status-controlpaneldivid");
        controlPanelDiv.setAttribute("class", "status-controlpaneldiv");
        controlPanelDiv.setAttribute("align", "center");
        controlPanelDiv.style.top = me.Y_CONTROL_PANEL_START_POSITION;
        controlPanelDiv.style.left = me.X_CONTROL_PANEL_START_POSITION;
        controlPanelDiv.style.width = me.CONTROL_PANEL_WIDTH;
	controlPanelDiv.style.height = me.CONTROL_PANEL_HEIGHT;
        var p = document.createElement("p");
        controlPanelDiv.appendChild(p);
        var label = document.createElement("label");
        label.setAttribute("class", "status-boldlabel");
        p.appendChild(label);
        label.appendChild(document.createTextNode("Control Panel"));
	
        // Create switch views button within control panel
        p = document.createElement("p");
        controlPanelDiv.appendChild(p);
        input = document.createElement("input");
        p.appendChild(input);
        input.setAttribute("type", "button");
        input.setAttribute("value", "Switch views");
        input.setAttribute("class", "status-simplebuttoninputform");
        input.onclick = me.toggleTempViews;

	// Create the legend panel
        var controlPanelDiv = document.createElement("div");
        me.tabMainDiv.appendChild(controlPanelDiv);
        controlPanelDiv.setAttribute("id", "status-legendpaneldivid");
        controlPanelDiv.setAttribute("class", "status-legendpaneldiv");
        controlPanelDiv.setAttribute("align", "center");
        controlPanelDiv.style.top = me.Y_LEGEND_PANEL_START_POSITION;
        controlPanelDiv.style.left = me.X_CONTROL_PANEL_START_POSITION;
        controlPanelDiv.style.width = me.CONTROL_PANEL_WIDTH;
	controlPanelDiv.style.height = me.LEGEND_PANEL_HEIGHT;
        var p = document.createElement("p");
        controlPanelDiv.appendChild(p);
        var label = document.createElement("label");
        label.setAttribute("class", "status-boldlabel");
        p.appendChild(label);
        label.appendChild(document.createTextNode("Background (Sensor) Legend"));	

	// Draw the four legend rectangles
	p = document.createElement("p");
	controlPanelDiv.appendChild(p);
	var div = document.createElement("div");
	div.setAttribute("class", "status-legendrectangleoff");
	div.appendChild(document.createTextNode("off"));
	p.appendChild(div);

	p = document.createElement("p");
	controlPanelDiv.appendChild(p);
	var div = document.createElement("div");
	div.setAttribute("class", "status-legendrectanglenormal");
	div.appendChild(document.createTextNode("normal"));
	p.appendChild(div);

	p = document.createElement("p");
	controlPanelDiv.appendChild(p);
	var div = document.createElement("div");
	div.setAttribute("class", "status-legendrectanglewarm");
	div.appendChild(document.createTextNode("warning"));
	p.appendChild(div);

	p = document.createElement("p");
	controlPanelDiv.appendChild(p);
	var div = document.createElement("div");
	div.setAttribute("class", "status-legendrectanglehot");
	div.appendChild(document.createTextNode("critical"));
	p.appendChild(div);

	// Text Legend
	// Spacer
	p = document.createElement("p");
	controlPanelDiv.appendChild(p);
	
        var label = document.createElement("label");
        label.setAttribute("class", "status-boldlabel");
        p.appendChild(label);
        label.appendChild(document.createTextNode("Text (Pingable) Legend"));
        
        p = document.createElement("p");
	controlPanelDiv.appendChild(p);
	var div = document.createElement("div");
	div.setAttribute("class", "status-legendrectangleoff");
	var textNode = document.createTextNode("offline");
	div.style.color = me.STATUS_LEVELS["OFFLINE"];
	div.appendChild(textNode);
	p.appendChild(div);

        p = document.createElement("p");
	controlPanelDiv.appendChild(p);
	var div = document.createElement("div");
	div.setAttribute("class", "status-legendrectangleoff");
	var textNode = document.createTextNode("online");
	div.style.color = me.STATUS_LEVELS["ONLINE"];
	div.appendChild(textNode);
	p.appendChild(div);

	// Draw the front racks
	me.nodeStatusRequest()
	me.drawTempFrontRacks();

	// Autorefresh the orphan nodes stack 
	setInterval(me.nodeStatusRequest, 30 * 1000);
      } 
      else 
      {
	alert("non-200 response");
      }
    }
  };


  // Getting xmlhttprequest to constantly retrieve information, as opposed to a one shot
  // deal, works eratically. Sometimes the data won’t come through properly or it will
  // work properly for a while and then just stop completely. What it comes down to is
  // the fact that the xmlhttprequest object is only really good for a single request.
  //
  // The best way to deal with this erratic nature is to actually use one object per
  // request, i.e. anytime a request is made, create a new object. Any kind of overhead
  // as a result of using this method isn't really obvious. 
  this.nodeStatusRequest = function nodeStatusRequest() 
  {
    me.nodeTempXmlHttp = new XMLHttpRequest();
    me.nodeTempXmlHttp.onreadystatechange = me.requestNodeStatusCallback;
    me.nodeTempXmlHttp.open("GET", "/cgi-bin/gui/components/status/statuscgi.py", true);
    me.nodeTempXmlHttp.send(null);
  };


  this.requestNodeStatusCallback = function requestNodeStatusCallback() {
    if (me.nodeTempXmlHttp.readyState == 4) {
        if (me.nodeTempXmlHttp.status == 200) {
	  var nodereadings = me.nodeTempXmlHttp.responseXML.getElementsByTagName("nodereading");
	  me.NODES_WITH_SENSORS.length = null;
	  var nodestatuses = me.nodeTempXmlHttp.responseXML.getElementsByTagName("nodestatus");
	  status_array = new Array();
	  
	  for (var j = 0; j < nodestatuses.length; j++) {
	  	sid = nodestatuses[j].getAttribute("id");
	  	stat = parseInt(nodestatuses[j].getAttribute("status"));
		var divs = document.getElementsByTagName("div");
	    	for (var c = 0; c < divs.length; c++) {
			if (divs[c].id == sid) {
				switch(stat) {
					case 1:
		  				divs[c].style.color = me.STATUS_LEVELS["ONLINE"];
		  				break;
		  			case 0:
		  				divs[c].style.color = me.STATUS_LEVELS["OFFLINE"];
		  				break;
		  			default:
		  				divs[c].style.color = me.STATUS_LEVELS["UNKNOWN"];
		  				break;
				}
			}
		}
	  }
	  	  
	  for (var j = 0; j < nodereadings.length; j++) {
	    var nodeid = nodereadings[j].getAttribute("id");
	    var divs = document.getElementsByTagName("div");
	    for (var c = 0; c < divs.length; c++) {
		if (divs[c].id == nodeid) {
		  var node_status = parseInt(nodereadings[j].getAttribute("overallstatus"));
		  var node_sensors = Array();
		  sensor_readings = nodereadings[j].getElementsByTagName("reading");
		  for (var sindex = 0; sindex < sensor_readings.length; sindex++) {
		    node_sensors.push(new auxiliary.hen.SensorStatus(
		        sensor_readings[sindex].getAttribute("id"),
		        sensor_readings[sindex].getAttribute("type"),
		        parseInt(sensor_readings[sindex].getAttribute("time")),
		        parseFloat(sensor_readings[sindex].getAttribute("value")),
		        parseFloat(sensor_readings[sindex].getAttribute("max")),
		        parseInt(sensor_readings[sindex].getAttribute("status"))
			));
		  }

		  me.NODES_WITH_SENSORS.push(new auxiliary.hen.NodeStatus(
			nodereadings[j].getAttribute("id"),
			node_status,
			node_sensors
		  ));

		  switch(node_status) {
			case 0:
				divs[c].style.backgroundColor = me.STATUS_LEVELS["NORMAL"];
				break;
			case 1:
				divs[c].style.backgroundColor = me.STATUS_LEVELS["WARNING"];
				break;
			case 2:
				divs[c].style.backgroundColor = me.STATUS_LEVELS["CRITICAL"];
				break;
			default:
				divs[c].style.backgroundColor = me.STATUS_LEVELS["OFF"];
			if (divs[c].style.color == me.STATUS_LEVELS["OFFLINE"] &&
			     divs[c].style.backgroundColor == me.STATUS_LEVELS["NORMAL"]) {
				divs[c].style.backgroundColor = me.STATUS_LEVELS["PALE_NORMAL"];	
			}
		  }
		}
	    }
	  }
        }
    }
  };


  
  
  this.handleNodeTempInfoRequest = function handleNodeTempInfoRequest(e) 
  {
    var id = e.target.id.substring(0, e.target.id.indexOf('text'));

    if (id == "")
      id = e.target.id;


    for (var i = 0; i < me.NODES_WITH_SENSORS.length; i++) 
    {
      if (me.NODES_WITH_SENSORS[i].id == id) 
      {
	if (!me.tempInfoDiv) 
	{
	  me.tempInfoDiv = me.drawTempInfoDiv(me.INFODIV_Y_POSITION, me.INFODIV_X_POSITION, me.NODES_WITH_SENSORS[i]);
	  break;
	}
      }
    }
  };

  

  this.closeNodeTempInfo = function closeNodeTempInfo() 
  {
    me.drawHelper.toggleVisibleByID(me.INFODIV_ID);
    me.tempInfoDiv = null;
  };



  this.drawTempRearRacks = function drawTempRearRacks() 
  {
    var xPos = me.X_DRAW_START_POSITION;
    //     for (var i = 0; i < theTempRacks.length; i++) 
    for (var i = me.theTempRacks.length - 1; i >= 0; i--) 
    {
      // We must search for the rack whose position is i + 1 so that the racks are drawn in order
      for (var j = 0; j < me.theTempRacks.length; j++)
	if (me.theTempRacks[j].rackPosition == i + 1) 
	{
	  // Adds all elements to the rack by setting theTempRacks[j].rearDiv
	  me.drawTempRearRack(me.theTempRacks[j], xPos,me.Y_RACK_LABEL_START_POSITION );

	  xPos += me.theTempRacks[j].rackWidth + 1;
	  //		    if (i != me.theTempRacks.length - 1)
	  if (i != 0)
	    xPos += me.INTER_RACK_GAP_LENGTH;
	  
	  // Add the rack's div to the tab div for display
	  me.tabMainDiv.appendChild(me.theTempRacks[j].rearDiv);
	}
    }

    for (var i = 0; i < me.theTempRacks.length; i++)
      me.visibilityDivs.push(me.theTempRacks[i].rearDiv);

    me.tempDrewRear = true;
  };




  this.drawTempRearRack = function drawTempRearRack(rack, xPos, yPos) 
  {
    // First draw the rack's label at the top
    rack.rearDiv.appendChild(me.drawRackLabel(
        rack.rackID + "templabel",
        "status-racklabel",
        xPos,
        yPos,
        rack.rackID,
        rack.rackWidth,
        me.RACK_LABEL_HEIGHT));

    // Now draw the actual nodes
    var bottom = me.Y_DRAW_START_POSITION + me.tempMaxNumberRackUnits * me.UNIT_HEIGHT;
    for (var i = 0; i < rack.nodes.length; i++) 
    {
      if ( (rack.nodes[i].endUnit != null && rack.nodes[i].startUnit != null)
	   && (rack.nodes[i].position.indexOf("rear") != -1 || rack.nodes[i].position == "both") ) 
      {
	// A regular node
	if (rack.nodes[i].position == "rear" || rack.nodes[i].position == "both") 
	{
	  var yPos = bottom - (rack.nodes[i].endUnit * me.UNIT_HEIGHT);
	  var numberUnits = rack.nodes[i].endUnit - rack.nodes[i].startUnit + 1;

	  rack.rearDiv.appendChild(me.drawTempNode(
                  rack.nodes[i].nodeID,
		  "t"+rack.nodes[i].nodeType,
		  xPos + 2 * me.VERTICAL_UNIT_WIDTH,
		  yPos,
		  numberUnits,
		  me.UNIT_HEIGHT,
		  rack.rearRackWidth,
		  me.MAX_NODE_LABEL_LENGTH,
		  me.TEXT_HEIGHT,
		  me.handleNodeTempInfoRequest));
	}
      } 
      else if (rack.nodes[i].position.indexOf("rearleft") != -1 ||
	       rack.nodes[i].position.indexOf("rearright") != -1) 
	   {
	     // A vertical node
	     var xPosition = me.calculateTempVerticalUnitXPos(xPos, rack.nodes[i].position, rack.rearRackWidth);
	     rack.rearDiv.appendChild(me.drawTempVerticalNode(
				      rack.nodes[i].nodeID,
				      //rack.nodes[i].nodeType,
				      "off",
				      xPosition,
				      me.Y_DRAW_START_POSITION,
				      rack.rackHeight,
				      me.UNIT_HEIGHT,
				      me.VERTICAL_UNIT_WIDTH,
				      me.VERTICAL_FUDGE_FACTOR,
				      me.handleNodeTempInfoRequest));
	   }
    }

    // Now fill in the horizontal empty slots
    for (var i = 1; i <= rack.rackHeight; i++) 
    {
      if (me.isTempSlotEmpty(rack, i)) 
      {
	var yPos = bottom - (i * me.UNIT_HEIGHT);
	rack.rearDiv.appendChild(me.drawUnsupportedNode(
              rack.rackID + "off" + String(i),
	      xPos + 2 * me.VERTICAL_UNIT_WIDTH,
	      yPos,
	      rack.rearRackWidth,
	      me.UNIT_HEIGHT));
      }
    }

    // Finally fill in any empty vertical slots
    if (me.isTempVerticalSlotEmpty(rack, "rearleft1")) 
    {
      var xPosition = me.calculateTempVerticalUnitXPos(xPos, "rearleft1", rack.rearRackWidth);
      rack.rearDiv.appendChild(me.drawTempVerticalBlankNode(
          rack.rackID + "off" + "rearleft1",
	  xPosition,
	  me.Y_DRAW_START_POSITION + (me.tempMaxNumberRackUnits - rack.rackHeight) * me.UNIT_HEIGHT,
	  me.VERTICAL_UNIT_WIDTH,
	  rack.rackHeight,
	  me.UNIT_HEIGHT));
    }
    if (me.isTempVerticalSlotEmpty(rack, "rearleft2")) 
    {
      var xPosition = me.calculateTempVerticalUnitXPos(xPos, "rearleft2", rack.rearRackWidth);
        rack.rearDiv.appendChild(me.drawTempVerticalBlankNode(
          rack.rackID + "off" + "rearleft2",
	  xPosition,
	  me.Y_DRAW_START_POSITION + (me.tempMaxNumberRackUnits - rack.rackHeight) * me.UNIT_HEIGHT,
	  me.VERTICAL_UNIT_WIDTH,
	  rack.rackHeight,
	  me.UNIT_HEIGHT));
    }
    if (me.isTempVerticalSlotEmpty(rack, "rearright1")) 
    {
      var xPosition = me.calculateTempVerticalUnitXPos(xPos, "rearright1", rack.rearRackWidth);
      rack.rearDiv.appendChild(me.drawTempVerticalBlankNode(
          rack.rackID + "off" + "rearright1",
	  xPosition,
	  me.Y_DRAW_START_POSITION + (me.tempMaxNumberRackUnits - rack.rackHeight) * me.UNIT_HEIGHT,
	  me.VERTICAL_UNIT_WIDTH,
	  rack.rackHeight,
	  me.UNIT_HEIGHT));
    }
    if (me.isTempVerticalSlotEmpty(rack, "rearright2")) 
    {
      var xPosition = me.calculateTempVerticalUnitXPos(xPos, "rearright2", rack.rearRackWidth);
      rack.rearDiv.appendChild(me.drawTempVerticalBlankNode(
          rack.rackID + "off" + "rearright2",
	  xPosition,
	  me.Y_DRAW_START_POSITION + (me.tempMaxNumberRackUnits - rack.rackHeight) * me.UNIT_HEIGHT,
	  me.VERTICAL_UNIT_WIDTH,
	  rack.rackHeight,
	  me.UNIT_HEIGHT));
    }
  };
    


  this.drawTempFrontRacks = function drawTempFrontRacks() 
  {
    me.drawRackUnitLabels(
         me.X_LABEL_START_POSITION,
	 me.Y_LABEL_START_POSITION,
	 "status-leftunitlabelid",
	 me.tempMaxNumberRackUnits,
	 me.UNIT_HEIGHT,
	 me.LABEL_WIDTH,
	 me.LABEL_HEIGHT,
	 "status-leftunitlabel");

    var xPos = me.X_DRAW_START_POSITION;
    for (var i = 0; i < me.theTempRacks.length; i++) 
    {
      // We must search for the rack whose position is i + 1 so that the racks are drawn in order
      for (var j = 0; j < me.theTempRacks.length; j++)
	if (me.theTempRacks[j].rackPosition == i + 1) 
	{
	  // Adds all elements to the rack by setting theTempRacks[j].frontDiv 
	  me.drawTempFrontRack(me.theTempRacks[j], xPos,me.Y_RACK_LABEL_START_POSITION );
	  
	  xPos += me.theTempRacks[j].rackWidth + 1;
	  if (i != me.theTempRacks.length - 1)
	    xPos += me.INTER_RACK_GAP_LENGTH;
	  
	  // Add the rack's div to the tab div for display
	  me.tabMainDiv.appendChild(me.theTempRacks[j].frontDiv);
	}
    }

    for (var i = 0; i < me.theTempRacks.length; i++)
      me.visibilityDivs.push(me.theTempRacks[i].frontDiv);

    me.drawRackUnitLabels(
       xPos + me.LABEL_SPACER,
       me.Y_LABEL_START_POSITION,
       "status-rightunitlabelid",
       me.tempMaxNumberRackUnits,
       me.UNIT_HEIGHT,
       me.LABEL_WIDTH,
       me.LABEL_HEIGHT,
       "status-rightunitlabel");
  };



  this.drawTempFrontRack = function drawTempFrontRack(rack, xPos, yPos) 
  {
    // First draw the rack's label at the top
    rack.frontDiv.appendChild(me.drawRackLabel(rack.rackID + "templabel", "status-racklabel", xPos, yPos, rack.rackID, rack.rackWidth, me.RACK_LABEL_HEIGHT));

    // Now draw the actual nodes
    var bottom = me.Y_DRAW_START_POSITION + me.tempMaxNumberRackUnits * me.UNIT_HEIGHT;
    for (var i = 0; i < rack.nodes.length; i++) 
    {
      if ( (rack.nodes[i].endUnit != null && rack.nodes[i].startUnit != null)
	   && (rack.nodes[i].position.indexOf("front") != -1 || rack.nodes[i].position == "both") ) 
      {
	var yPos = bottom - (rack.nodes[i].endUnit * me.UNIT_HEIGHT);
	var numberUnits = rack.nodes[i].endUnit - rack.nodes[i].startUnit + 1;
	
	rack.frontDiv.appendChild(me.drawTempNode(
              rack.nodes[i].nodeID,
	      "t"+rack.nodes[i].nodeType,
	      xPos,
	      yPos,
	      numberUnits,
	      me.UNIT_HEIGHT,
	      rack.rackWidth,
	      me.MAX_NODE_LABEL_LENGTH,
	      me.TEXT_HEIGHT,
	      me.handleNodeTempInfoRequest));
      }
    }

    // Now we need to fill in the empty slots
    for (var i = 1; i <= rack.rackHeight; i++) 
    {
      if (me.isTempSlotEmpty(rack, i)) 
      {
	var yPos = bottom - (i * me.UNIT_HEIGHT);
	rack.frontDiv.appendChild(me.drawUnsupportedNode(
              rack.rackID + "off" + String(i),
	      xPos,
	      yPos,
	      rack.rackWidth,
	      me.UNIT_HEIGHT));
      }
    }
  };


  this.drawTempInfoDiv = function drawTempInfoDiv(posX, posY, nodeObject) 
  {
    var style = "position:absolute; top:" + posX +
                "; left:" + posY +
                "; width: auto" +
                "; height: auto" +
                "; z-index:2" +
                "; padding:10px" +
                "; font-size: 8pt" +
                "; border:#000000 1px solid" +
                "; background-color:white;";

    var infodiv = document.createElement("div");
    infodiv.setAttribute("id", me.INFODIV_ID);
    infodiv.setAttribute("style", style);

    var table = document.createElement("table");
    infodiv.appendChild(table);
    table.setAttribute("width", me.INFODIV_WIDTH);

    var header = document.createElement("th");
    table.appendChild(header);
    header.setAttribute("align", "right");
    header.setAttribute("colspan", "2");

    var img = document.createElement("img");
    //infodiv.appendChild(img);
    header.appendChild(img);
    img.setAttribute("id", me.INFODIVCLOSE_ID);
    img.src = "images/close.gif";
    img.onclick = me.closeNodeTempInfo;


    // id
    var row = document.createElement("tr");
    table.appendChild(row);
    var cell1 = document.createElement("td");
    row.appendChild(cell1);
    cell1.setAttribute("align", "right");
    cell1.appendChild(document.createTextNode("Nodeid:"));
    var cell2 = document.createElement("td");
    row.appendChild(cell2);
    cell2.appendChild(document.createTextNode(nodeObject.id));

    for (var index = 0; index < nodeObject.sensors.length; index++) {
    	var status = nodeObject.sensors[index];
	var row = document.createElement("tr");
    	table.appendChild(row);
    	var cell1 = document.createElement("td");
    	row.appendChild(cell1);
    	cell1.setAttribute("align", "right");
    	var link = document.createElement("a");
    	link.innerHTML = status.id + ":";
	link.href = "javascript:void(null)"
	link.onclick = me.createGraphRequestFunction(nodeObject.id, status.id);
    	cell1.appendChild(link);
    	var cell2 = document.createElement("td");
    	row.appendChild(cell2);
    	cell2.appendChild(document.createTextNode(status.val));	
    }
    me.tabMainDiv.appendChild(infodiv);
    return infodiv;
  };
  
  this.createGraphRequestFunction = function createGraphRequestFunction(nodeid, sensorid) {
  	return function() { me.graphRequest(nodeid, sensorid); }
  };
  this.graphRequest = function graphRequest(nodeid, sensorid) 
  {
    me.showLoadingDiv(me.LOADING_DIV_X_POSITION, me.LOADING_DIV_Y_POSITION);
    me.graphRequestNodeid = nodeid
    me.graphRequestSensorid = sensorid
    graphurl = "/cgi-bin/gui/components/status/makesensorgraphcgi.py?nodeid=" + 
    		encodeURIComponent(nodeid) + "&sensorid=" + encodeURIComponent(sensorid) + 
    		"&timerange=604800"
    me.graphXMLHttp = new XMLHttpRequest();
    me.graphXMLHttp.onreadystatechange = me.requestGraphCallback;
    me.graphXMLHttp.open("GET", graphurl, true);
    me.graphXMLHttp.send(null);
  };


  this.requestGraphCallback = function requestGraphCallback() {
    if (me.graphXMLHttp.readyState == 4) {
        if (me.graphXMLHttp.status == 200) {
           me.hideLoadingDiv();
	   me.drawSensorGraphBox(me.graphXMLHttp.responseText);
	}
    }
  }

  this.closeSensorGraphBox = function closeSensorGraphBox() 
  {
    me.drawHelper.toggleVisibleByID(me.GRAPHDIV_ID);
    me.graphBoxDiv = null;
  };

  this.drawSensorGraphBox = function drawSensorGraphBox(graphurl) 
  {
    var style = "position:absolute; top:" + me.GRAPHDIV_X_POSITION +
                "; left:" + me.GRAPHDIV_Y_POSITION +
                "; width: auto" +
                "; height: auto" +
                "; z-index:2" +
                "; padding:10px" +
                "; font-size: 8pt" +
                "; border:#000000 1px solid" +
                "; background-color:white;";

    var graphdiv = document.createElement("div");
    graphdiv.setAttribute("id", me.GRAPHDIV_ID);
    graphdiv.setAttribute("style", style);

    var table = document.createElement("table");
    graphdiv.appendChild(table);
    table.setAttribute("width", me.GRAPHDIV_WIDTH);

    var header = document.createElement("th");
    table.appendChild(header);
    header.setAttribute("align", "right");
    header.setAttribute("colspan", "2");

    var img = document.createElement("img");
    header.appendChild(img);
    img.setAttribute("id", me.GRAPHDIVCLOSE_ID);
    img.src = "images/close.gif";
    img.onclick = me.closeSensorGraphBox;

    var graph = document.createElement("img");
    graph.src = graphurl;
    graphdiv.appendChild(graph);
    
//	link.href = "/cgi-bin/gui/components/status/makesensorgraphcgi.py?nodeid=" + 
//    		encodeURIComponent(nodeObject.id) + "&sensorid=" + encodeURIComponent(status.id) + 
//    		"&timerange=" + 604800;

    me.tabMainDiv.appendChild(graphdiv);
    return graphdiv;
  };

  this.isTempSlotEmpty = function isTempSlotEmpty(rack, slot) 
  {
    for (var i = 0; i < rack.nodes.length; i++) 
    {
      if ( (slot >= rack.nodes[i].startUnit) && (slot <= rack.nodes[i].endUnit)
	   && (rack.nodes[i].position.indexOf(me.tempCurrentView) != -1 || rack.nodes[i].position == "both") )
	return false;
    }
    return true;
  };

  this.isTempVerticalSlotEmpty = function isTempVerticalSlotEmpty(rack, slot) 
  {
    for (var i = 0; i < rack.nodes.length; i++)
    {
      if (rack.nodes[i].position.indexOf(slot) != -1)
	return false;
    }
    return true;
  };



  this.calculateTempVerticalUnitXPos = function calculateTempVerticalUnitXPos(initialXPos, slot, rackWidth) 
  {
    if (slot == "rearleft1")
      return initialXPos;
    if (slot == "rearleft2")
      return initialXPos + me.VERTICAL_UNIT_WIDTH;
    if (slot == "rearright1")
      return initialXPos + 2 * me.VERTICAL_UNIT_WIDTH + rackWidth;
    if (slot == "rearright2")
      return initialXPos + 3 * me.VERTICAL_UNIT_WIDTH + rackWidth;
  };



  this.toggleTempViews = function toggleTempViews() 
  {
    // First hide the racks currently begin displayed
    me.toggleTempRacks();

    // Switch from front to rear
    if (me.tempCurrentView == "front") 
    {
      if (!me.tempDrewRear) 
      {
	me.tempCurrentView = "rear";
	me.drawTempRearRacks();
	me.nodeStatusRequest();
      } 
      else 
      {
	// We've drawn the divs before, just make them visible
	me.tempCurrentView = "rear";
	me.toggleTempRacks();
      }
    } 
    else 
    {
      // Switch from rear to front
      me.tempCurrentView = "front";
      me.toggleTempRacks();
    }
  };




  this.toggleTempRacks = function toggleTempRacks() 
  {
    for (var i = 0; i < me.theTempRacks.length; i++)
      if (me.tempCurrentView == "front")
	me.drawHelper.toggleVisibleByElement(me.theTempRacks[i].frontDiv);
      else
	me.drawHelper.toggleVisibleByElement(me.theTempRacks[i].rearDiv);
  };


} // end class StatusTab

// Set up inheritance
components.status.status.StatusTab.prototype = new auxiliary.hen.Tab();
