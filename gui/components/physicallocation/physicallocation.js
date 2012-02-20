//**********************************************************************************
//**********************************************************************************
// Implements the components.physicallocation.physicallocation namespace
//
// CLASSES
// --------------------------------------------
// PhysicalLocationTab    Displays and manages the "Physical Location" tab
//
//
// $Id: physicallocation.js 183 2006-08-11 09:47:36Z munlee $ 
//**********************************************************************************
//**********************************************************************************
Namespace("components.physicallocation.physicallocation");
Import("auxiliary.hen", ".", "/");
Import("auxiliary.draw", ".", "/");


// ***************************************************
// ***** CLASS: PhysicalLocationTab ******************
// ***************************************************
components.physicallocation.physicallocation.PhysicalLocationTab = function()
{
  // Necessary to keep reference to 'this' for event handlers 
  var me = this;
  // The x start position of the control div
  this.X_CONTROL_PANEL_START_POSITION = 10;
  // The y start position of the control div
  this.Y_CONTROL_PANEL_START_POSITION = 45;
  // The width of the control div
  this.CONTROL_PANEL_WIDTH = 140;
  // The distance between the control panel and the left-hand unit labels
  this.CONTROL_PANEL_SPACER = 20;
  // The width of a wide rack 
  this.WIDE_RACK_WIDTH = 140;
  // The width of a narrow rack 
  this.NARROW_RACK_WIDTH = this.WIDE_RACK_WIDTH - 25;
  // The height of a single unit 
  this.UNIT_HEIGHT = 12;
  // The width of a single vertical unit 
  this.VERTICAL_UNIT_WIDTH = 12;
  // The number of pixels separating racks 
  this.INTER_RACK_GAP_LENGTH = 10;
  // The number of line breaks in a vertical node's text label 
  this.VERTICAL_FUDGE_FACTOR = 10; 
  // The total number of vertical slots that a rack can have 
  this.MAX_NUMBER_VERTICAL_SLOTS = 4;
  // The y start position for the rack labels
  this.Y_RACK_LABEL_START_POSITION = 30;
  // The x start position for the unit labels 
  this.X_LABEL_START_POSITION = this.X_CONTROL_PANEL_START_POSITION + this.CONTROL_PANEL_WIDTH + this.CONTROL_PANEL_SPACER;
  // The height of the div containing a rack label 
  this.RACK_LABEL_HEIGHT = 15;
  // The y start position for the unit labels 
  this.Y_LABEL_START_POSITION = this.Y_RACK_LABEL_START_POSITION + this.RACK_LABEL_HEIGHT;
  // The y start position for drawing the racks 
  this.Y_DRAW_START_POSITION = this.Y_LABEL_START_POSITION
  // The width of the div containing a unit label 
  this.LABEL_WIDTH = 20;
  // The height of the div containing a unit label 
  this.LABEL_HEIGHT = 20;
  // The maximum number of characters for a node label 
  this.MAX_NODE_LABEL_LENGTH = 10;
  // Used to vertically center a node's label 
  this.TEXT_HEIGHT = 8;  
  // The number of horizontal pixels between the unit labels and the racks 
  this.LABEL_SPACER = 10;
  // The number of vertical pixels between the bottom of the racks and the control buttons 
  this.BUTTONS_SPACER = 15;
  // The x start position for drawing the racks 
  this.X_DRAW_START_POSITION = this.X_LABEL_START_POSITION + this.LABEL_WIDTH + this.LABEL_SPACER;
  // The width of the switch views button 
  this.TOGGLE_BUTTON_WIDTH = 110;
  // The height of the switch views button 
  this.TOGGLE_BUTTON_HEIGHT = 20;
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
  // The id of the div for the text inside the pop-up information box div 
  this.INFODIVTEXT_ID = "infodivtext";
  // The id of the div for the close button inside the pop-up information box div 
  this.INFODIVCLOSE_ID = "infodivclose";
  // The back end url for the location information 
  this.PHYSICAL_LOCATION_URL = "/cgi-bin/gui/components/physicallocation/physicallocationcgi.py";
  // The back end url for the additional information pop-up box 
  this.NODE_INFO_URL = "/cgi-bin/gui/components/physicallocation/nodeinformationcgi.py?id=";
  // The asynchronous request object 
  this.xmlHttp = null;
  // The asynchronous request object for polling the CGI 
  this.xmlHttpPoll = null;
  // The div representing the pop-up information box 
  this.infoDiv;
  // The array containing all of the rack location information 
  this.theRacks = new Array(); 
  // The number of units in the tallest rack 
  this.maxNumberRackUnits;
  // Either front or rear 
  this.currentView = "front";
  // Whether the rear view has already been drawn or not 
  this.drewRear = false;
  // timeout value for setTimeout() function 
  this.TIMEOUT_MILISECONDS = 5000;
  // The timeout interval ID. 
  this.intervalID = null;

  this.tabLabel = "Location";
  this.allowedGroups.push("henmanager");

  // Used to create various divs for text and nodes 
  this.drawHelper = new auxiliary.draw.DrawHelper();



  this.initTab = function initTab()
  {
    me.showLoadingDiv(200, 200);
    me.xmlHttp = new XMLHttpRequest();
    var requestPage = me.PHYSICAL_LOCATION_URL;
    me.xmlHttp.onreadystatechange = me.handlePhysicalLocationReply;
    me.xmlHttp.open("GET", requestPage, true);
    me.xmlHttp.send(null);
  };



  this.handlePhysicalLocationReply = function handlePhysicalLocationReply() 
  {
    if (me.xmlHttp.readyState == 4) 
    {
      if (me.xmlHttp.status == 200) 
      {	
	var xmlDoc = me.xmlHttp.responseXML;
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
	  me.theRacks.push(rack);
	}

	me.maxNumberRackUnits = -1;
	for (var i = 0; i < me.theRacks.length; i++) 
	{
	  if (me.theRacks[i].rackHeight > me.maxNumberRackUnits)
	    me.maxNumberRackUnits = me.theRacks[i].rackHeight;
	}

	// Remove loading gif
	me.hideLoadingDiv();

	// Create control panel div
	var controlPanelDiv = document.createElement("div");
	me.tabMainDiv.appendChild(controlPanelDiv);
	controlPanelDiv.setAttribute("id", "physicallocation-controlpaneldivid");
	controlPanelDiv.setAttribute("class", "physicallocation-controlpaneldiv");
	controlPanelDiv.setAttribute("align", "center");
	controlPanelDiv.style.top = me.Y_CONTROL_PANEL_START_POSITION;
	controlPanelDiv.style.left = me.X_CONTROL_PANEL_START_POSITION;
	controlPanelDiv.style.width = me.CONTROL_PANEL_WIDTH;
	var p = document.createElement("p");
	controlPanelDiv.appendChild(p);
	var label = document.createElement("label");
	label.setAttribute("class", "physicallocation-boldlabel");
	p.appendChild(label);
	label.appendChild(document.createTextNode("Control Panel"));
	
	// Create switch views button within control panel
	p = document.createElement("p");
	controlPanelDiv.appendChild(p);
	input = document.createElement("input");
	p.appendChild(input);
	input.setAttribute("type", "button");
	input.setAttribute("value", "Switch views");
	input.setAttribute("class", "physicallocation-simplebuttoninputform");
	input.onclick = me.toggleViews;

	// Draw the front racks
	me.drawFrontRacks();

      } 
      else 
      {
	alert("non-200 response");
      }
    }
  };

  this.updateRackGUI = function updateRackGUI() 
  {
    var rackStart = document.getElementById("deviceRackStartSelectId").value;
    var rackEnd = document.getElementById("deviceRackEndSelectId").value;
    var position = document.getElementById("devicePositionSelectId").value;
    var rackname = top.document.getElementById("rackSelectId").value;
    var type = top.document.getElementById("typeSelectId").value;

    var theHighestRow = 0;
    var theLowestRow = 0;
    if (parseInt(rackStart) >= parseInt(rackEnd)) {
        theHighestRow = parseInt(rackStart);
        theLowestRow = parseInt(rackEnd);
    } else {
        theHighestRow = parseInt(rackEnd);
        theLowestRow = parseInt(rackStart);
    }
    var theRackHeight = (theHighestRow - theLowestRow) + 1;

    //alert(rackStart);
    //alert(rackEnd);
    //alert(position);
    //alert(rackname);

    var divs = document.getElementsByTagName("div");
    for (var i = 0; i < divs.length; i++) {
        if (divs[i].getAttribute("class") == "physicallocation-empty") {
            var theID = divs[i].getAttribute("id");
            var theRackName = theID.substring(0, divs[i].getAttribute("id").indexOf('empty'));
            var theRowNumber = theID.substring(divs[i].getAttribute("id").indexOf('empty') + 5, theID.length);
            if (theRackName == rackname && theRowNumber == theHighestRow) {
                //alert(theRackName);
                //alert(theRowNumber);
                //alert(type);
                var topPos = parseInt(divs[i].style.top);
                // the height in pixels multiplied by the number of racks
                var newHeight = parseInt(divs[i].style.height) * theRackHeight;
                if (type == "physicallocation-computer") {
                    // give the div a colour corresponding to its type
                    divs[i].style.backgroundColor = "orange";
                    // give the div a new height value
                    divs[i].style.height = newHeight;

                    // change to the temporary new id
                    divs[i].setAttribute("id", "newNodePlaceholderId");
                    divs[i].setAttribute("class", type);


                    for (var j = theHighestRow - 1; j >= theLowestRow; j--) {
                        var targetElement = document.getElementById(theRackName + "empty" + j);
                        targetElement.parentNode.removeChild(targetElement);
                    }
                } else {
                    // handle other node classes here
                }
            }




        }
    }
  };

  this.handleNodeInfoRequest = function handleNodeInfoRequest(e) 
  {
    var id = e.target.id.substring(0, e.target.id.indexOf('text'))

    if (id == "")
      id = e.target.id;

    var element = document.getElementById(id);
    var top = element.style.top;
    var left = element.style.left;
    var width = element.style.width;
    var height = element.style.height;

    if (!me.infoDiv)
      me.infoDiv = me.drawInfoDiv(me.INFODIV_Y_POSITION, me.INFODIV_X_POSITION);

    var requestPage = me.NODE_INFO_URL + id;
    me.xmlHttp.onreadystatechange = me.handleNodeInfoReply;
    me.xmlHttp.open("GET", requestPage, true);
    me.xmlHttp.send(null);
  };



  this.handleNodeInfoReply = function handleNodeInfoReply() 
  {
    if (me.xmlHttp.readyState == 4) 
    {
      if (me.xmlHttp.status == 200) 
      {
	var element = document.getElementById(me.INFODIVTEXT_ID);
	element.innerHTML = me.xmlHttp.responseText;
      } 
      else 
      {
	var element = document.getElementById(me.INFODIVTEXT_ID);
	element.innerHTML = "no data";
      }
    }
  };



  this.closeNodeInfo = function closeNodeInfo() 
  {
    //toggleVisibleByID(me.INFODIV_ID);
    var targetElement = document.getElementById(me.INFODIV_ID);
    targetElement.parentNode.removeChild(targetElement);

    me.infoDiv = null;
  };



  this.drawRearRacks = function drawRearRacks() 
  {
    var xPos = me.X_DRAW_START_POSITION;
    //     for (var i = 0; i < me.theRacks.length; i++) 
    for (var i = me.theRacks.length - 1; i >= 0; i--) 
    {
      // We must search for the rack whose position is i + 1 so that the racks are drawn in order
      for (var j = 0; j < me.theRacks.length; j++)
	if (me.theRacks[j].rackPosition == i + 1) 
	{
	  // Adds all elements to the rack by setting me.theRacks[j].rearDiv
	  me.drawRearRack(me.theRacks[j], xPos,me.Y_RACK_LABEL_START_POSITION );

	  xPos += me.theRacks[j].rackWidth + 1;
	  //		    if (i != me.theRacks.length - 1)
	  if (i != 0)
	    xPos += me.INTER_RACK_GAP_LENGTH;
	  
	  // Add the rack's div to the tab div for display
	  me.tabMainDiv.appendChild(me.theRacks[j].rearDiv);
	}
    }
    for (var i = 0; i < me.theRacks.length; i++)
      me.visibilityDivs.push(me.theRacks[i].rearDiv);

    me.drewRear = true;
  };



  this.drawRearRack = function drawRearRack(rack, xPos, yPos) 
  {
    // First draw the rack's label at the top
    rack.rearDiv.appendChild(me.drawHelper.drawLabel(
        rack.rackID + "label",
        "physicallocation-racklabel",
        xPos,
        yPos,
        rack.rackID,
        rack.rackWidth,
        me.RACK_LABEL_HEIGHT));

    // Now draw the actual nodes
    var bottom = me.Y_DRAW_START_POSITION + me.maxNumberRackUnits * me.UNIT_HEIGHT;
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

	  rack.rearDiv.appendChild(me.drawHelper.drawNode(
	       rack.nodes[i].nodeID,
	       rack.nodes[i].nodeType,
	       xPos + 2 * me.VERTICAL_UNIT_WIDTH,
	       yPos,
	       numberUnits,
	       me.UNIT_HEIGHT,
	       rack.rearRackWidth,
	       me.MAX_NODE_LABEL_LENGTH,
	       me.TEXT_HEIGHT,
	       me.handleNodeInfoRequest,
	       "physicallocation-nodetext"));
	}
      } 
      else if (rack.nodes[i].position.indexOf("rearleft") != -1 ||
	       rack.nodes[i].position.indexOf("rearright") != -1) 
      {
	// A vertical node
	var xPosition = me.calculateVerticalUnitXPos(xPos, rack.nodes[i].position, rack.rearRackWidth);
	rack.rearDiv.appendChild(me.drawHelper.drawVerticalNode(
                rack.nodes[i].nodeID,
                rack.nodes[i].nodeType,
                xPosition,
                me.Y_DRAW_START_POSITION,
                rack.rackHeight,
                me.UNIT_HEIGHT,
                me.VERTICAL_UNIT_WIDTH,
                me.VERTICAL_FUDGE_FACTOR,
                me.handleNodeInfoRequest,
		"physicallocation-verticalnodetext"));
      }
    }

    // Now fill in the horizontal empty slots
    for (var i = 1; i <= rack.rackHeight; i++) 
    {
      if (me.isSlotEmpty(rack, i)) 
      {
	var yPos = bottom - (i * me.UNIT_HEIGHT);
	rack.rearDiv.appendChild(me.drawHelper.drawBlankNode(
                rack.rackID + "empty" + String(i),
		"physicallocation-empty",
                xPos + 2 * me.VERTICAL_UNIT_WIDTH,
                yPos,
                rack.rearRackWidth,
                me.UNIT_HEIGHT));
      }
    }

    // Finally fill in any empty vertical slots
    if (me.isVerticalSlotEmpty(rack, "rearleft1")) 
    {
      var xPosition = me.calculateVerticalUnitXPos(xPos, "rearleft1", rack.rearRackWidth);
      rack.rearDiv.appendChild(me.drawHelper.drawVerticalBlankNode(
            rack.rackID + "empty" + "rearleft1",
	    "physicallocation-empty",
            xPosition,
            me.Y_DRAW_START_POSITION + (me.maxNumberRackUnits - rack.rackHeight) * me.UNIT_HEIGHT,
            me.VERTICAL_UNIT_WIDTH,
            rack.rackHeight,
            me.UNIT_HEIGHT));
    }
    if (me.isVerticalSlotEmpty(rack, "rearleft2")) 
    {
      var xPosition = me.calculateVerticalUnitXPos(xPos, "rearleft2", rack.rearRackWidth);
      rack.rearDiv.appendChild(me.drawHelper.drawVerticalBlankNode(
            rack.rackID + "empty" + "rearleft2",
	    "physicallocation-empty",
            xPosition,
            me.Y_DRAW_START_POSITION + (me.maxNumberRackUnits - rack.rackHeight) * me.UNIT_HEIGHT,
            me.VERTICAL_UNIT_WIDTH,
            rack.rackHeight,
            me.UNIT_HEIGHT));
    }
    if (me.isVerticalSlotEmpty(rack, "rearright1")) 
    {
      var xPosition = me.calculateVerticalUnitXPos(xPos, "rearright1", rack.rearRackWidth);
      rack.rearDiv.appendChild(me.drawHelper.drawVerticalBlankNode(
            rack.rackID + "empty" + "rearright1",
	    "physicallocation-empty",
            xPosition,
            me.Y_DRAW_START_POSITION + (me.maxNumberRackUnits - rack.rackHeight) * me.UNIT_HEIGHT,
            me.VERTICAL_UNIT_WIDTH,
            rack.rackHeight,
            me.UNIT_HEIGHT));
    }
    if (me.isVerticalSlotEmpty(rack, "rearright2")) 
    {
      var xPosition = me.calculateVerticalUnitXPos(xPos, "rearright2", rack.rearRackWidth);
      rack.rearDiv.appendChild(me.drawHelper.drawVerticalBlankNode(
            rack.rackID + "empty" + "rearright2",
	    "physicallocation-empty",
            xPosition,
            me.Y_DRAW_START_POSITION + (me.maxNumberRackUnits - rack.rackHeight) * me.UNIT_HEIGHT,
            me.VERTICAL_UNIT_WIDTH,
            rack.rackHeight,
            me.UNIT_HEIGHT));
    }
  };



  this.drawFrontRacks = function drawFrontRacks() 
  {
    me.tabMainDiv.appendChild(me.drawHelper.drawUnitLabels(
       me.X_LABEL_START_POSITION,
       me.Y_LABEL_START_POSITION,
       "left",
       me.maxNumberRackUnits,
       me.UNIT_HEIGHT,
       me.LABEL_WIDTH,
       me.LABEL_HEIGHT,
       "physicallocation-leftunitlabel"));

    var xPos = me.X_DRAW_START_POSITION;
    for (var i = 0; i < me.theRacks.length; i++) 
    {
      // We must search for the rack whose position is i + 1 so that the racks are drawn in order
      for (var j = 0; j < me.theRacks.length; j++)
	if (me.theRacks[j].rackPosition == i + 1) 
	{
	  // Adds all elements to the rack by setting me.theRacks[j].frontDiv 
	  me.drawFrontRack(me.theRacks[j], xPos,me.Y_RACK_LABEL_START_POSITION );

	  xPos += me.theRacks[j].rackWidth + 1;
	  if (i != me.theRacks.length - 1)
	    xPos += me.INTER_RACK_GAP_LENGTH;

	  // Add the rack's div to the tab div for display
	  me.tabMainDiv.appendChild(me.theRacks[j].frontDiv);
	}
    }
    me.tabMainDiv.appendChild(me.drawHelper.drawUnitLabels(
        xPos + me.LABEL_SPACER,
        me.Y_LABEL_START_POSITION,
        "right",
        me.maxNumberRackUnits,
        me.UNIT_HEIGHT,
        me.LABEL_WIDTH,
        me.LABEL_HEIGHT,
	"physicallocation-rightunitlabel"));

    for (var i = 0; i < me.theRacks.length; i++)
      me.visibilityDivs.push(me.theRacks[i].frontDiv);
  };



  this.drawFrontRack = function drawFrontRack(rack, xPos, yPos) 
  {
    // First draw the rack's label at the top
    rack.frontDiv.appendChild(me.drawHelper.drawLabel(rack.rackID + "label", "physicallocation-racklabel", xPos, yPos, rack.rackID, rack.rackWidth, me.RACK_LABEL_HEIGHT));

    // Now draw the actual nodes
    var bottom = me.Y_DRAW_START_POSITION + me.maxNumberRackUnits * me.UNIT_HEIGHT;
    for (var i = 0; i < rack.nodes.length; i++) 
    {
      if ( (rack.nodes[i].endUnit != null && rack.nodes[i].startUnit != null)
	   && (rack.nodes[i].position.indexOf("front") != -1 || rack.nodes[i].position == "both") ) 
      {
	var yPos = bottom - (rack.nodes[i].endUnit * me.UNIT_HEIGHT);
	var numberUnits = rack.nodes[i].endUnit - rack.nodes[i].startUnit + 1;

	rack.frontDiv.appendChild(me.drawHelper.drawNode(
             rack.nodes[i].nodeID,
	     rack.nodes[i].nodeType,
	     xPos,
	     yPos,
	     numberUnits,
	     me.UNIT_HEIGHT,
	     rack.rackWidth,
	     me.MAX_NODE_LABEL_LENGTH,
                me.TEXT_HEIGHT,
	     me.handleNodeInfoRequest,
	     "physicallocation-nodetext"));
      }
    }

    // Now we need to fill in the empty slots
    for (var i = 1; i <= rack.rackHeight; i++) 
    {
      if (me.isSlotEmpty(rack, i)) 
      {
	var yPos = bottom - (i * me.UNIT_HEIGHT);
	rack.frontDiv.appendChild(me.drawHelper.drawBlankNode(
              rack.rackID + "empty" + String(i),
	      "physicallocation-empty",
	      xPos,
	      yPos,
	      rack.rackWidth,
	      me.UNIT_HEIGHT));
      }
    }
  };



  this.drawInfoDiv = function drawInfoDiv(posX, posY) 
  {
    var style = "position:absolute; top:" + posX +
                "; left:" + posY +
                "; width:" + me.INFODIV_WIDTH +
                "; height:" + me.INFODIV_HEIGHT +
                "; z-index:2" +
                "; padding:0px" +
                "; border:#000000 1px solid" +
                "; background-color:white;";

    var infodiv = document.createElement("div");
    infodiv.setAttribute("id", me.INFODIV_ID);
    infodiv.setAttribute("style", style);

    var table = document.createElement("table");
    table.setAttribute("width", me.INFODIV_WIDTH);
    var row1 = document.createElement("tr");
    var row2 = document.createElement("tr");
    var cell1 = document.createElement("td");
    cell1.setAttribute("align", "right");
    var cell2 = document.createElement("td");
    cell2.setAttribute("id", me.INFODIVTEXT_ID);
    cell2.setAttribute("class", "physicallocation-nodeinfotext");
    var img = document.createElement("img");
    img.setAttribute("id", me.INFODIVCLOSE_ID);
    img.src = "images/close.gif";
    img.onclick = me.closeNodeInfo;
    infodiv.appendChild(img);

    cell1.appendChild(img);
    row1.appendChild(cell1);
    row2.appendChild(cell2);
    table.appendChild(row1);
    table.appendChild(row2);
    infodiv.appendChild(table);

    me.tabMainDiv.appendChild(infodiv);
    return infodiv;
  };



  this.isSlotEmpty = function isSlotEmpty(rack, slot) 
  {
    for (var i = 0; i < rack.nodes.length; i++) 
    {
      if ( (slot >= rack.nodes[i].startUnit) && (slot <= rack.nodes[i].endUnit)
	   && (rack.nodes[i].position.indexOf(me.currentView) != -1 || rack.nodes[i].position == "both") )
	return false;
    }
    return true;
  };



  this.isVerticalSlotEmpty = function isVerticalSlotEmpty(rack, slot) 
  {
    for (var i = 0; i < rack.nodes.length; i++) {
      if (rack.nodes[i].position.indexOf(slot) != -1)
	return false;
    }
    return true;
  };



  this.calculateVerticalUnitXPos = function calculateVerticalUnitXPos(initialXPos, slot, rackWidth) 
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


  
  this.toggleViews = function toggleViews() 
  {
    // First hide the racks currently begin displayed
    me.toggleRacks();

    // Switch from front to rear
    if (me.currentView == "front") 
    {
      if (!me.drewRear) 
      {
	me.currentView = "rear";
	me.drawRearRacks();
      } 
      else 
      {
	// We've drawn the divs before, just make them visible
	me.currentView = "rear";
	me.toggleRacks();
      }
    } 
    else 
    {
      // Switch from rear to front
      me.currentView = "front";
      me.toggleRacks();
    }
  };



  this.toggleRacks = function toggleRacks() 
  {
    for (var i = 0; i < me.theRacks.length; i++)
      if (me.currentView == "front")
	me.drawHelper.toggleVisibleByElement(me.theRacks[i].frontDiv);
      else
	me.drawHelper.toggleVisibleByElement(me.theRacks[i].rearDiv);
  };


  
  this.isInfoWindowSelectsDisabled = function isInfoWindowSelectsDisabled() 
  {
    var infodiv = document.getElementById("infodiv");
    var select = infodiv.getElementsByTagName("select");
    for (var i = 0; i < select.length; i++) 
    {
      if (select[i].disabled == true) 
      {
	return true;
      }
    }
    return false;
  };

} // end class PhysicalLocationTab

// Set up inheritance
components.physicallocation.physicallocation.PhysicalLocationTab.prototype = new auxiliary.hen.Tab();
