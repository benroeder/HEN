/**
 * @fileoverview  Displays and manages the "Power" tab of the GUI
 * @version 0.1
 */
Namespace ("components.power.power");
Import ("auxiliary.draw", ".", "/");
Import ("auxiliary.hen", ".", "/");


/**
 * Constructs a new components.power.power.PowerTab object.
 * @class PowerTab is a subclass of auxiliary.hen.Tab
 * @constructor
 * @return A new PowerTab object
 */
components.power.power.PowerTab = function()
{
  /* Necessary to keep reference to 'this' for event handlers */
  var me = this;
  // The label for this tab
  this.tabLabel = "Power";
  // The groups that are allowed to see this tab
  this.allowedGroups.push("henmanager");
  // Controls power to nodes
  var powerURL = "/cgi-bin/gui/components/power/powercgi.py";
  // Asynchronous request object used to get all the ids of nodes with power switch
  var getNodeIDsRequest = null;
  // Asynchronous request object used to send a power request
  var powerRequest = null;
  // Used to keep track of the number of nodes displayed
  var numberNodes = null;
  // The x start position of the control div
  var X_DISPLAY_PANEL_START_POSITION = 100;
  // The y start position of the control div
  var Y_DISPLAY_PANEL_START_POSITION = 45;
  // The width of the control div
  var DISPLAY_PANEL_WIDTH = 500;
  // The x position of the loading animated div
  var LOADING_DIV_X_POSITION = 0;
  // The y position of the loading animated div
  var LOADING_DIV_Y_POSITION = 200;

  /**
   * Initializes the tab by sending an asynchronous request to retrieve the ids of 
   * all nodes that have a power switch. 
   */
  this.initTab = function initTab() 
  {
    // Send the retrieve nodes request
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    var requestPage = powerURL + "?action=getnodeids";
    getNodeIDsRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleNodeIDsReply);
    getNodeIDsRequest.send();
  };

  /**
   * Event handler for asynchronous request to retrieve the ids of all 
   * nodes that have a power switch. Draws the control buttons as well
   * as the table of nodes
   */
  this.handleNodeIDsReply = function handleNodeIDsReply()
  {
    if (getNodeIDsRequest.getReadyState() == 4)
    {
      if (getNodeIDsRequest.getStatus() == 200)
      {
	me.hideLoadingDiv();

	var displayPanelDiv = document.createElement("div");
	document.body.appendChild(displayPanelDiv);
	displayPanelDiv.setAttribute("class", "power-displaypaneldiv");
	displayPanelDiv.setAttribute("align", "center");
	displayPanelDiv.style.top = Y_DISPLAY_PANEL_START_POSITION;
	displayPanelDiv.style.left = X_DISPLAY_PANEL_START_POSITION;
	displayPanelDiv.style.width = DISPLAY_PANEL_WIDTH;
	me.visibilityDivs.push(displayPanelDiv);

	// Table that contains the select box and buttons
	var controlsTable = document.createElement("table");
	controlsTable.setAttribute("class", "power-powercontrolstable");
	controlsTable.setAttribute("align", "center");
	displayPanelDiv.appendChild(controlsTable);

	// Spacer row
	var spacerRow = document.createElement("tr");
	controlsTable.appendChild(spacerRow);
	var spacerCell = document.createElement("td");
	spacerCell.setAttribute("align", "center");
	spacerRow.appendChild(spacerCell);
	var img = document.createElement("img");
	img.src = "images/transparent.gif";
	img.setAttribute("height", "10");
	spacerCell.appendChild(img);

	// Buttons row
	var row = document.createElement("tr");
	controlsTable.appendChild(row);
	var cell = document.createElement("td");
	cell.setAttribute("align", "center");
	row.appendChild(cell);
	// Power on button
	var input = document.createElement("input");
	input.setAttribute("type", "button");
	input.setAttribute("id", "power-buttonOnId");
	input.setAttribute("value", "power on");
	input.setAttribute("class", "power-simplebuttoninputform");
	input.onclick = me.sendPowerRequest;
	cell.appendChild(input);
	// Spacer
	var img = document.createElement("img");
	img.src = "images/transparent.gif";
	img.setAttribute("width", "5");
	cell.appendChild(img);
	// Power off button
	var input = document.createElement("input");
	input.setAttribute("type", "button");
	input.setAttribute("id", "power-buttonOffId");
	input.setAttribute("value", "power off");
	input.setAttribute("class", "power-simplebuttoninputform");
	input.onclick = me.sendPowerRequest;
	cell.appendChild(input);
	
	// Spacer
	var img = document.createElement("img");
	img.src = "images/transparent.gif";
	img.setAttribute("width", "5");
	cell.appendChild(img);
	// Restart button
	var input = document.createElement("input");
	input.setAttribute("type", "button");
	input.setAttribute("id", "power-buttonRestartId");
	input.setAttribute("value", "restart");
	input.setAttribute("class", "power-simplebuttoninputform");
	input.onclick = me.sendPowerRequest;
	cell.appendChild(input);
	// Spacer
	var img = document.createElement("img");
	img.src = "images/transparent.gif";
	img.setAttribute("width", "5");
	cell.appendChild(img);
	
	// Refresh button
	var input = document.createElement("input");
	input.setAttribute("type", "button");
	input.setAttribute("id", "power-buttonRefreshId");
	input.setAttribute("value", "status");
	input.setAttribute("class", "power-simplebuttoninputform");
	input.onclick = me.sendPowerRequest;
	cell.appendChild(input);
	
	// Spacer row
	var spacerRow = document.createElement("tr");
	controlsTable.appendChild(spacerRow);
	var spacerCell = document.createElement("td");
	spacerCell.setAttribute("align", "center");
	spacerRow.appendChild(spacerCell);
	var img = document.createElement("img");
	img.src = "images/transparent.gif";
	img.setAttribute("height", "20");
	spacerCell.appendChild(img);    

	// Start processing reply
	var row = document.createElement("tr");
	controlsTable.appendChild(row);
	var cell = document.createElement("td");
	row.appendChild(cell);

	var xmlDoc = getNodeIDsRequest.getResponseXML();
	var nodes = xmlDoc.getElementsByTagName("power")[0].getElementsByTagName("node");

        var nodesTable = document.createElement("table");
        nodesTable.setAttribute("class", "power-powertable");
        nodesTable.setAttribute("id", "power-powerTableId");
        nodesTable.setAttribute("align", "center");
        nodesTable.style.width = DISPLAY_PANEL_WIDTH - 50;
        cell.appendChild(nodesTable);

        // Print the final row containing the select all, deselect all buttons
        var row = document.createElement("tr");
        row.setAttribute("class", "power-powerrow");
        nodesTable.appendChild(row);
        var cell = document.createElement("td");
        cell.setAttribute("class", "power-powercell");
        cell.setAttribute("align", "left");
        cell.setAttribute("colspan", "4");
	cell.setAttribute("valign", "top");
        row.appendChild(cell);
	
        var checkBox = document.createElement("input");
        checkBox.setAttribute("type", "checkbox");
        checkBox.setAttribute("id", "power-powerCheckBoxAll");
        checkBox.onclick = me.selectCheckBoxes;
        cell.appendChild(checkBox);
        var headingLabel = document.createElement("label");
        headingLabel.setAttribute("class", "power-boldlabel");
        cell.appendChild(headingLabel);
        headingLabel.appendChild(document.createTextNode("all"));
        var checkBox = document.createElement("input");
        checkBox.setAttribute("type", "checkbox");
        checkBox.setAttribute("id", "power-powerCheckBoxNone");
        checkBox.onclick = me.selectCheckBoxes;
        cell.appendChild(checkBox);

        var headingLabel = document.createElement("label");
        headingLabel.setAttribute("class", "power-boldlabel");
        cell.appendChild(headingLabel);
        headingLabel.appendChild(document.createTextNode("none"));

        var headings = new Array();
        headings.push("select");
        headings.push("node id");
        headings.push("node status");
        headings.push("owner");
        var headingsRow = document.createElement("tr");
        headingsRow.setAttribute("class", "power-powerrow");
        nodesTable.appendChild(headingsRow);
        for (var i = 0; i < headings.length; i++)
	{
	  var headingCell = document.createElement("td");
	  headingCell.setAttribute("class", "power-powercell");
	  headingCell.setAttribute("align", "center");
	  headingsRow.appendChild(headingCell);
	  var headingLabel = document.createElement("label");
	  headingLabel.setAttribute("class", "power-boldlabel");
	  headingCell.appendChild(headingLabel);
	  headingLabel.appendChild(document.createTextNode(headings[i]));
	}

        // For each node print a row containing a checkbox, the nodeid, and its (for now unknown) power status
        numberNodes = nodes.length;
        for (var i = 0; i < nodes.length; i++)
	{
	  var nodeID = auxiliary.hen.getAttributeValue(nodes[i], "id");
	  var nodeOwner = auxiliary.hen.getAttributeValue(nodes[i], "owner");
	  var row = document.createElement("tr");
	  row.setAttribute("class", "power-powerrow");
	  nodesTable.appendChild(row);

	  // Checkbox
	  var cell = document.createElement("td");
	  cell.setAttribute("class", "power-powercell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  var checkBox = document.createElement("input");
	  checkBox.setAttribute("type", "checkbox");
	  checkBox.setAttribute("id", "power-powerCheckBox" + i);
	  checkBox.setAttribute("nodeid", nodeID);
	  cell.appendChild(checkBox);
	  // Node id
	  var cell = document.createElement("td");
	  cell.setAttribute("class", "power-powercell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  var label = document.createElement("label");
	  label.setAttribute("class", "power-normallabel");
	  cell.appendChild(label);
	  label.appendChild(document.createTextNode(nodeID));

	  // Status
	  var cell = document.createElement("td");
	  cell.setAttribute("class", "power-powercell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  var label = document.createElement("label");
	  label.setAttribute("class", "power-normallabel");
	  label.setAttribute("id", "power-powerLabel" + nodeID);
	  label.innerHTML = "unknown";
	  cell.appendChild(label);

	  // Owner
	  var cell = document.createElement("td");
	  cell.setAttribute("class", "power-powercell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  var label = document.createElement("label");
	  label.setAttribute("class", "power-normallabel");
	  cell.appendChild(label);
	  label.appendChild(document.createTextNode(nodeOwner));
	}

	// Spacer row
	var spacerRow = document.createElement("tr");
	controlsTable.appendChild(spacerRow);
	var spacerCell = document.createElement("td");
	spacerCell.setAttribute("align", "center");
	spacerRow.appendChild(spacerCell);
	var img = document.createElement("img");
	img.src = "images/transparent.gif";
	img.setAttribute("height", "20");
	spacerCell.appendChild(img);    
      }
    }
  };

  /**
   * Onclick event handler for the control buttons. Send an asynchronous request to 
   * perform the power operation
   * @evt (Event} The onlick event
   */
  this.sendPowerRequest = function sendPowerRequest(evt)
  {
    var selectedNodes = new Array();
    var buttonID = null;
    var action = null;
    try
    {
      buttonID = evt.target.id;
      action = buttonID.substring(buttonID.indexOf("button") + 6, buttonID.indexOf("Id"));
    }
    catch (e)
    {
      action = evt;
    }

    if (action == "On")
      action = "poweron";
    else if (action == "Off")
      action = "poweroff";
    else if (action == "Restart")
      action = "restart";
    else
      action = "status";

    for (var i = 0; i < numberNodes; i++)
    {
      var checkBox = document.getElementById("power-powerCheckBox" + i);
      if (checkBox.checked && !checkBox.disabled)
	selectedNodes.push(checkBox.getAttribute("nodeid"));
    }


    if (selectedNodes.length > 0)
    {
      me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
      me.setDisablePowerControls(true);

      var requestPage = powerURL + "?action=" + action + "&numbernodes=" + selectedNodes.length + "&node0=" + selectedNodes[0];
      for (var i = 1; i < selectedNodes.length; i++)
        requestPage += "&node" + i + "=" + selectedNodes[i];

      powerRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePowerReply);
      powerRequest.send();
    }
  };

  /**
   * Handles the reply to a power request by updating the status of the relevant nodes
   */
  this.handlePowerReply = function handlePowerReply()
  {
    if (powerRequest.getReadyState() == 4)
    {
      if (powerRequest.getStatus() == 200)
      {
	var xmlDoc = powerRequest.getResponseXML();
	var nodes = xmlDoc.getElementsByTagName("power")[0].getElementsByTagName("node");

	for (var i = 0; i < nodes.length; i++)
	{
	  var nodeID = auxiliary.hen.getAttributeValue(nodes[i], "id");
	  var nodeStatus = auxiliary.hen.getAttributeValue(nodes[i], "status");
	  var label = document.getElementById("power-powerLabel" + nodeID);
	  label.innerHTML = nodeStatus;
	}
	
	me.setDisablePowerControls(false);
	me.hideLoadingDiv();
	
	// Clear all the checkboxes
	for (var i = 0; i < numberNodes; i++)
	{
	  document.getElementById("power-powerCheckBox" + i).checked = false;
	}
      }
    }
  };

  /**
   * Disables all the controls on the tab
   * @param {boolean} disable Whether or not to disable the controls
   */
  this.setDisablePowerControls = function setDisablePowerControls(disable)
  {
    document.getElementById("power-buttonOnId").disabled = disable;
    document.getElementById("power-buttonOffId").disabled = disable;
    document.getElementById("power-buttonRestartId").disabled = disable;
    document.getElementById("power-buttonRefreshId").disabled = disable;
    document.getElementById("power-powerCheckBoxNone").disabled = disable;
    document.getElementById("power-powerCheckBoxAll").disabled = disable;

    for (var i = 0; i < numberNodes; i++)
    {
	var checkBox = document.getElementById("power-powerCheckBox" + i);
	document.getElementById("power-powerCheckBox" + i).disabled = disable;
    }
  };

  /**
   * Onclick event handler for select all/none checkboxes
   * @param {Event} evt The onclick event
   */
  this.selectCheckBoxes = function selectCheckBoxes(evt)
  {
    var checkBoxID = null;

    try
    {
      checkBoxID = evt.target.id;
    }
    catch (e)
    {
      checkBoxID = evt;
    }
    var checkBox = document.getElementById(checkBoxID);
    var action = checkBoxID.substring(checkBoxID.indexOf("Box") + 3);
    checkBox.checked = false;
    for (var i = 0; i < numberNodes; i++)
    {
      var checkBox = document.getElementById("power-powerCheckBox" + i);
      if (action == "All")
      {
	if (!checkBox.disabled)
	  checkBox.checked = true;
      }
      else
      {
	if (!checkBox.disabled)
	{
	  checkBox.checked = false;
	}
      }
    }
  };

} // end class PowerTab

// Set up inheritance
components.power.power.PowerTab.prototype = new auxiliary.hen.Tab();
