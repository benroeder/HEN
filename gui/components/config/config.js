/**
 * @fileoverview  Displays and manages the "Config" tab of the GUI
 * @version 0.1
 */
Namespace ("components.config.config");
Import ("auxiliary.draw", ".", "/");
Import ("auxiliary.hen", ".", "/");


/**
 * Constructs a new components.config.config.ConfigTab object.
 * @class ConfigTab is a subclass of auxiliary.hen.Tab
 * @constructor
 * @return A new ConfigTab object
 */
components.config.config.ConfigTab = function()
{
  /* Necessary to keep reference to 'this' for event handlers */
  var me = this;
  // The label for this tab
  this.tabLabel = "Config";
  // The groups that are allowed to see this tab
  this.allowedGroups.push("henmanager");
  // Gets/Edits config file
  var configURL = "/cgi-bin/gui/components/config/configcgi.py";
  // Asynchronous request object used to get the config file
  var getConfigRequest = null;
  // Asynchronous request object used to save changes to the config file
  var saveConfigRequest = null;
  // Used to create input controls
  this.formHelper = new auxiliary.draw.FormHelper();
  // Used to draw html elements
  this.drawHelper = new auxiliary.draw.DrawHelper();
  // The x start position of the control div
  var X_DISPLAY_PANEL_START_POSITION = 10;
  // The y start position of the control div
  var Y_DISPLAY_PANEL_START_POSITION = 45;
  // The width of the control div
  var DISPLAY_PANEL_WIDTH = 800;
  // The x position of the loading animated div
  var LOADING_DIV_X_POSITION = 0;
  // The y position of the loading animated div
  var LOADING_DIV_Y_POSITION = 200;
  // Used to keep track of the text of the saved config file
  var savedConfigFileText = null;
  // Used to keep track of text that has been submitted for saving but not yet saved
  var pendingConfigFileText = null;

  /**
   * Initializes the tab by sending an asynchronous request to retrieve the config file
   */
  this.initTab = function initTab() 
  {
    // Send the retrieve nodes request
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    var requestPage = configURL + "?action=getconfig";
    getConfigRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleConfigReply);
    getConfigRequest.send();
  };

  /**
   * Event handler for asynchronous request to retrieve the config file. Draws the
   * text area.
   */
  this.handleConfigReply = function handleConfigReply()
  {
    if (getConfigRequest.getReadyState() == 4)
    {
      if (getConfigRequest.getStatus() == 200)
      {
	me.hideLoadingDiv();
	
	var displayPanelDiv = document.createElement("div");
	document.body.appendChild(displayPanelDiv);
	displayPanelDiv.setAttribute("class", "config-displaypaneldiv");
	displayPanelDiv.setAttribute("align", "center");
	displayPanelDiv.style.top = Y_DISPLAY_PANEL_START_POSITION;
	displayPanelDiv.style.left = X_DISPLAY_PANEL_START_POSITION;
	displayPanelDiv.style.width = DISPLAY_PANEL_WIDTH;
	displayPanelDiv.style.border = "0px";
	me.visibilityDivs.push(displayPanelDiv);

	// Table that contains the text area and buttons
	var controlsTable = document.createElement("table");
	controlsTable.setAttribute("align", "center");
	displayPanelDiv.appendChild(controlsTable);

	// Spacer row
	me.drawHelper.createLayoutSpacerRow("10", "1");

	// Buttons row
	var row = me.drawHelper.createLayoutRow();
	controlsTable.appendChild(row);
	var cell = me.drawHelper.createLayoutCell();
	row.appendChild(cell);
	cell.style.backgroundColor = "#ccc";
	cell.style.border = "1px solid";
	var innerTable = me.drawHelper.createLayoutTable();
	cell.appendChild(innerTable);
	innerTable.setAttribute("align", "center");
	var row = me.drawHelper.createLayoutRow();
	innerTable.appendChild(row);
	var cell = me.drawHelper.createLayoutCell();
	row.appendChild(cell);
	cell.appendChild(me.formHelper.createButton("config-savebuttonid", "config-simplebuttoninputform", "Save Changes", me.saveChanges));
	var cell = me.drawHelper.createLayoutCell();
	row.appendChild(cell);
	cell.appendChild(me.formHelper.createButton("config-cancelbuttonid", "config-simplebuttoninputform", "Discard Changes", me.cancelChanges));

	// Start processing reply, add main text area to table
	var row = document.createElement("tr");
	controlsTable.appendChild(row);
	var cell = document.createElement("td");
	row.appendChild(cell);
	var textArea = me.formHelper.createTextArea("config-editconfigtextareaid", "config-simpletextareainputform", "50", "100");
	cell.appendChild(textArea);

	var xmlDoc = getConfigRequest.getResponseXML();
	var configFileLines = xmlDoc.getElementsByTagName("config")[0].getElementsByTagName("configfile")[0].getElementsByTagName("line");

	var configFile = "";
	for (var i = 0; i < configFileLines.length; i++)
	  configFile += configFileLines[i].firstChild.nodeValue;

	textArea.value = configFile;
	savedConfigFileText = configFile;
      }
    }
  };

  /**
   * Onclick event handler for the 'Save Changes' button, talks to a cgi script and attempts
   * to write to the testbed's config file
   */
  this.saveChanges = function saveChanges()
  {
    var answer = confirm("Are you sure you want to save the changes you've made?");
    if (answer)
    {
      me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
      me.setDisableControls(true);

      var configFileText = document.getElementById("config-editconfigtextareaid").value;
      var requestPage = configURL + "?action=editconfig&configfile=" + escape(configFileText);
      saveConfigRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleSaveConfigReply);
      saveConfigRequest.send();    
      pendingConfigFileText = configFileText;
    }
  };
  
  /**
   * Onclick event handler for the 'Cancel Changes' button, discards any changes that the user has typed 
   * since the last save
   */
  this.cancelChanges = function cancelChanges()
  {
    var answer = confirm("Are you sure you want to discard the changes you've made?");
    if (answer)
    {
      document.getElementById("config-editconfigtextareaid").value = savedConfigFileText;
    }
  };

  /**
   * Handles a response to a write config file operation and shows an alert with the result
   */
  this.handleSaveConfigReply = function handleSaveConfigReply()
  {
    if (saveConfigRequest.getReadyState() == 4)
    {
      if (saveConfigRequest.getStatus() == 200)
      {
	var xmlDoc = saveConfigRequest.getResponseXML();
	var responseValue = auxiliary.hen.getAttributeValue(xmlDoc.getElementsByTagName("config")[0].getElementsByTagName("response")[0], "value");
	if (responseValue == "0")
	{
	  savedConfigFileText = pendingConfigFileText;
	  me.hideLoadingDiv();
	  me.setDisableControls(false);
	  alert("changes saved successfully");
	}
	else
	  alert("error while saving changes, your changes have not been saved");
      }
    }
  };

  /**
   * Sets the 'disabled' property of the two buttons and the text area.
   * @param {boolean} disable Whether to disable the controls or not
   */
  this.setDisableControls = function setDisableControls(disable)
  {
    document.getElementById("config-savebuttonid").disabled = disable;
    document.getElementById("config-cancelbuttonid").disabled = disable;
    document.getElementById("config-editconfigtextareaid").disabled = disable
  };

} // end class ConfigTab

// Set up inheritance
components.config.config.ConfigTab.prototype = new auxiliary.hen.Tab();
