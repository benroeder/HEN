//**********************************************************************************
//**********************************************************************************
// Implements the components.experiment.experiment namespace
//
// CLASSES
// --------------------------------------------
// ExperimentTab    Displays and manages the "Experiment" tab
//
//
// $Id: experiment.js 176 2006-08-05 14:31:11Z munlee $ 
//**********************************************************************************
//**********************************************************************************
Namespace("components.experiment.experiment");
Import ("components.experiment.calendar", ".", "/");
Import ("components.experiment.canvas", ".", "/");
Import ("auxiliary.draw", ".", "/");
Import ("auxiliary.hen", ".", "/");

// ***************************************************
// ***** CLASS: ExperimentTab ************************
// ***************************************************
components.experiment.experiment.ExperimentTab = function()
{
  // Used by the SVG canvas to interact with the rest of the tab 
  window.experimentTabSVGCanvas = new components.experiment.canvas.SVGCanvas();
  // Necessary to keep reference to 'this' for event handlers 
  var me = this;
  // Used to create various form elements 
  this.formHelper = new auxiliary.draw.FormHelper();
  // Used to create various div elements
  this.drawHelper = new auxiliary.draw.DrawHelper();
  // Gives the experiment history
  this.experimentHistoryURL = "/cgi-bin/gui/components/experiment/historycgi.py";
  // Controls power to nodes
  this.experimentPowerURL = "/cgi-bin/gui/components/experiment/powercgi.py";
  // Back-end to files subtab
  this.experimentFileURL = "/cgi-bin/gui/components/experiment/filecgi.py";
  // Back-end to files subtab
  this.experimentCalendarURL = "/cgi-bin/gui/components/experiment/calendarcgi.py";
  // Back-end for log information
  this.experimentLogURL = "/cgi-bin/gui/components/experiment/logcgi.py";
  // Used to retrieve the experiment history
  this.experimentHistoryXmlHttp = null;
  // The width of the history div
  this.HISTORY_DIV_WIDTH = 500;
  // Keeps track of the currently active canvas tab
  this.currentActiveCanvasTab = null;
  // Contains references to all the canvas tabs
  this.canvasTabDivs = new Array();
  // The height of the canvas
  this.CANVAS_HEIGHT = 480;
  // The width of the canvas
  this.CANVAS_WIDTH = 500;
  // The x position of the canvas
  this.CANVAS_X_POSITION = 240;
  // The y position of the canvas
  this.CANVAS_Y_POSITION = 70;
  // Used to keep track of the number of nodes currently displayed in the power tab
  this.powerTabNumberNodes = null;
  // The class for select boxes in the edit/add canvas
  this.selectBoxClass = "experiment-simpledropdowninputform";
  // The class for text boxes in the edit/add canvas
  this.textBoxClass = "experiment-simpletextinputform";
  // The class for buttons in the edit/add canvas
  this.buttonClass = "experiment-simplebuttoninputform";
  // The class for text areas in the edit/add canvas
  this.textAreaClass = "experiment-simpletextareainputform";
  // Used to pop a floating div with an input form
  this.floatingInputDiv = null;
  // The x position of the pop up div
  this.POP_UP_X_POSITION = 400;
  // The y position of the pop up div
  this.POP_UP_Y_POSITION = 200;
  // The width of the pop up div
  this.POP_UP_WIDTH = 160;
  // The height of the pop up div
  this.POP_UP_HEIGHT = 90;
  // Whether the pop-up div used for user input has been create yet
  this.createdPopUp = false;
  // Used to hold a reference to the calendar objects
  this.calendarTable = null;
  // Asynchronous request object used to retrieve all experiment for the calendar subtab
  this.calendarTabGetExperimentsXmlHttp = null;
  // The subtab divs whose style.visibility property has been set manually (not through parent)
  this.visibilitySubDivs = new Array();
  // The x position of the loading animated div
  var LOADING_DIV_X_POSITION = 200;
  // The y position of the loading animated div
  var LOADING_DIV_Y_POSITION = 200;
  // Asynchronous request object used to request log information
  this.logRequest = null;
  // Asynchronous request object used to request a file node edit/add/delete operation
  this.fileNodeRequest = null;
  // Asynchronous request object used to request the files in a user's directory (used by files subtab)
  this.fileNamesRequest = null;
  // Asynchronous request object used to request the files in a user's directory (used by main tab)
  this.userFileNamesRequest = null;
  // Asynchronous request object used to request the files in a user's directory + standard ones (used by file subtab)
  this.viewFilesIDsRequest = null;
  // Used to keep track of whether the user is editing a file or not
  this.mode = null;

  this.ifacexhr = null;
  this.nodeXHR = null;
  this.powerTabXmlHttp = null;
  this.powerTabXmlHttp2 = null;
  this.powerTabXmlHttp3 = null;
  this.fileTabXmlHttp = null;
  this.fileTabXmlHttp2 = null;
  this.removeConfigXhr = null;  
  this.refreshConfigFileListXhr = null;
  this.REFRESH_LIST_TIMEOUT_MILISECONDS = 2000;
  this.configLoadSelectName = null;
  this.nodeNameDropdownSelectName = null;
  this.nodeTypesName = null;
  this.endNodeIDName = null;
  this.startNodeIDName = null;
  this.user = null;
  this.mainDiv = null;
  this.mainNameDiv = null;

  this.tabLabel = "Experiment";
  this.allowedGroups.push("henmanager");
  this.allowedGroups.push("henuser");

  this.handleViewFilesIDsReply = function handleViewFilesIDsReply()
  {
    if (me.viewFilesIDsRequest.getReadyState() == 4)
    {
      if (me.viewFilesIDsRequest.getStatus() == 200)
      {
	var xmlDoc = me.viewFilesIDsRequest.getResponseXML();
	var filenames = xmlDoc.getElementsByTagName("experiments")[0].getElementsByTagName("filenode");
	var selectBox = document.getElementById("experiment-fileSubTabViewFileId");
	selectBox.options.length = 0;
	selectBox[0] = new Option("please select...", "please select...");
	for (var i = 0; i < filenames.length; i++)
	{
	  var fileNodeID = auxiliary.hen.getAttributeValue(filenames[i], "id");
	  var standard = auxiliary.hen.getAttributeValue(filenames[i], "standard");

	  if (standard == "yes")
	    selectBox[selectBox.options.length] = new Option(fileNodeID + " (standard)", fileNodeID);
	  else     
	    selectBox[selectBox.options.length] = new Option(fileNodeID, fileNodeID);
	}
      }
    }
  }

  this.handleUserFileNamesReply = function handleUserFileNamesReply()
  {
    if (me.userFileNamesRequest.getReadyState() == 4)
    {
      if (me.userFileNamesRequest.getStatus() == 200)
      {
	var xmlDoc = me.userFileNamesRequest.getResponseXML();
	var filenames = xmlDoc.getElementsByTagName("experiments")[0].getElementsByTagName("filenode");
	var selectBoxes = new Array();
	selectBoxes["filesystem"] = document.getElementById("filesystemForm");
	selectBoxes["kernel"] = document.getElementById("kernelForm");
	selectBoxes["loader"] = document.getElementById("loaderForm");
	selectBoxes["filesystem"].options.length = 0;
	selectBoxes["filesystem"][0] = new Option("please select...", "please select...");
	selectBoxes["kernel"].options.length = 0;
	selectBoxes["kernel"][0] = new Option("please select...", "please select...");
	selectBoxes["loader"].options.length = 0;
	selectBoxes["loader"][0] = new Option("please select...", "please select...");	
	for (var i = 0; i < filenames.length; i++)
	{
	  var selectBox = selectBoxes[auxiliary.hen.getAttributeValue(filenames[i], "type")];
	  var fileNodeID = auxiliary.hen.getAttributeValue(filenames[i], "id");
	  var standard = auxiliary.hen.getAttributeValue(filenames[i], "standard");
	  var fileName = auxiliary.hen.getAttributeValue(filenames[i], "path");

	  if (standard == "yes")
	    selectBox[selectBox.options.length] = new Option(fileNodeID + ": " + fileName + " (standard)", fileNodeID);
	  else     
	    selectBox[selectBox.options.length] = new Option(fileNodeID + ": " + fileName, fileNodeID);
	}
      }
    }
  };

  this.initTab = function initTab() 
  {
    var nodeOptions = new Array(); 
    me.getNodes()
    window.experimentTabSVGCanvas.nodeOptions = nodeOptions;

    // Create canvas tabs and initialize them
    var tabAreaDiv = document.createElement("div");
    tabAreaDiv.setAttribute("id", "experimentTabAreaDivId");
    tabAreaDiv.setAttribute("class", "experimentTabArea");
    me.tabMainDiv.appendChild(tabAreaDiv);
    me.createTabs(tabAreaDiv);
    me.currentActiveCanvasTab = "experiment-topologyTabId";
    me.toggleTabs("experiment-topologyTabId");

    var newNodeMenuDiv = document.createElement("div");
    me.tabMainDiv.appendChild(newNodeMenuDiv);
    newNodeMenuDiv.setAttribute("id", "newNodeMenuId");
    newNodeMenuDiv.setAttribute("class", "experiment-newnodedivpanel");

    var div = document.createElement("div");
    newNodeMenuDiv.appendChild(div);
    div.setAttribute("id", "typeSelectDivId");

    var form = document.createElement("form");
    div.appendChild(form);
    form.setAttribute("name", "nodeTypeFormName");

    var select = document.createElement("select");
    form.appendChild(select);
    select.setAttribute("name", "nodeTypesName");
    me.nodeTypesName = form.nodeTypesName;
    select.onchange = me.doChangeMenu;
    select.setAttribute("class", "experiment-simpledropdowninputform");

    var option = document.createElement("option");
    select.appendChild(option);
    option.setAttribute("value", "node");
    option.appendChild(document.createTextNode("Node"));

    option = document.createElement("option");
    select.appendChild(option);
    option.setAttribute("value", "edge");
    option.appendChild(document.createTextNode("Edge"));

    var nodeInfoDiv = document.createElement("div");
    newNodeMenuDiv.appendChild(nodeInfoDiv);
    nodeInfoDiv.setAttribute("id", "nodeInfoDivId");
    nodeInfoDiv.setAttribute("class", "nodeInfoDivClass");

    // Node name form
    div = document.createElement("div");
    nodeInfoDiv.appendChild(div);
    div.setAttribute("id", "nodeNameDropdownDivId");
    div.setAttribute("class", "nodeNameDropdownDivClass");

    style = "font-family: verdana, sans-serif;" +
            "font-size: 10px;" +
            "font-weight: bold;";
    div.setAttribute("style", style);

    form = document.createElement("form");
    div.appendChild(form);
    form.setAttribute("id", "nodeNameDropdownFormId");
    form.setAttribute("name", "nodeNameDropdownFormName");

    select = document.createElement("select");
    form.appendChild(select);
    select.setAttribute("name", "nodeNameDropdownSelectName");
    select.setAttribute("class", "experiment-simpledropdowninputform");

    me.nodeNameDropdownSelectName = form.nodeNameDropdownSelectName;
    select.onchange = me.doNodeNameDropdownSelect;


    // Table
    var nodeInfoTable = document.createElement("table");
    nodeInfoDiv.appendChild(nodeInfoTable);
    nodeInfoTable.setAttribute("border", "0");
    nodeInfoTable.setAttribute("width", "200px");
    nodeInfoTable.setAttribute("id", "nodeInfoTableId");
    nodeInfoTable.setAttribute("name", "nodeInfoTableName");

    var tbody = document.createElement("tbody");
    nodeInfoTable.appendChild(tbody);
    tbody.setAttribute("id", "nodeInfoTableTbody");

    // Type
    tbody.appendChild(me.formHelper.createTableEntry("Node ID", "nodeTable", "nodeTableClass", null));
    // Model
    tbody.appendChild(me.formHelper.createTableEntry("Motherboard", "motherboardTable", "motherboardTableClass", null));
    // CPU Type
    tbody.appendChild(me.formHelper.createTableEntry("CPU Type", "cputypeTable", "cpuTypeTableClass", null));
    // CPU Speed
    tbody.appendChild(me.formHelper.createTableEntry("CPU Speed", "cpuspeedTable", "cpuSpeedTableClass", null));
    // Multi processors
    tbody.appendChild(me.formHelper.createTableEntry("Multi processors", "multiprocessorTable", "multiProcTableClass", null));
    // Memory
    tbody.appendChild(me.formHelper.createTableEntry("Memory", "memoryTable", "memoryTableClass", null));

    // Filesystem
    var row = me.drawHelper.createLayoutRow();
    tbody.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("experiment-boldlabel", "Filesystem");
    cell.appendChild(label);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("filesystemForm", "experiment-simpledropdowninputform", options, null);
    selectBox.style.width = "120px";
    cell.appendChild(selectBox);

    // Kernel
    var row = me.drawHelper.createLayoutRow();
    tbody.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("experiment-boldlabel", "Kernel");
    cell.appendChild(label);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("kernelForm", "experiment-simpledropdowninputform", options, null);
    selectBox.style.width = "120px";
    cell.appendChild(selectBox);

    // Loader
    var row = me.drawHelper.createLayoutRow();
    tbody.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("experiment-boldlabel", "Loader");
    cell.appendChild(label);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("loaderForm", "experiment-simpledropdowninputform", options, null);
    selectBox.style.width = "120px";
    cell.appendChild(selectBox);

    // Send request to populate the above 3 select boxes
    var requestPage = me.experimentFileURL + "?action=getfilesbyuser&username=" + me.user.username + "&getstandard=yes";
    me.userFileNamesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleUserFileNamesReply);
    me.userFileNamesRequest.send();

    // Create node button
    p = document.createElement("p");
    nodeInfoDiv.appendChild(p);
    form = document.createElement("form");
    p.appendChild(form);
    form.setAttribute("id", "nodeTypeInputFormId");
    form.setAttribute("name", "nodeTypeInputForm");
    input = document.createElement("input");
    form.appendChild(input);
    input.setAttribute("type", "button");
    input.setAttribute("id", "experiment-createNodeButtonId");
    input.setAttribute("value", "Create node");
    input.setAttribute("class", "experiment-simplebuttoninputform");
    input.onclick = window.experimentTabSVGCanvas.doCreateNode;
    input.style.visibility = "hidden";
    me.visibilityDivs.push(input);

    // Edge form
    var edgeDiv = document.createElement("div");
    newNodeMenuDiv.appendChild(edgeDiv);
    edgeDiv.setAttribute("id", "edgeDivId");
    edgeDiv.setAttribute("class", "edgeDivClass");

    style = "position: relative;" +
            "font-family: verdana, sans-serif;" +
            "font-size: 10px;" +
            "font-weight: bold;" +
            "display: none;";
    edgeDiv.setAttribute("style", style);

    form = document.createElement("form");
    edgeDiv.appendChild(form);
    form.setAttribute("id", "edgeInputFormId");
    form.setAttribute("name", "edgeInputForm");

    // Edge name
    var div = document.createElement("div");
    form.appendChild(div);
    var label = document.createElement("label");
    div.appendChild(label);
    label.setAttribute("for", "edgeNameId");
    label.appendChild(document.createTextNode("VLAN Name"));

    var input = document.createElement("input");
    div.appendChild(input);
    input.setAttribute("type", "text");
    input.setAttribute("id", "edgeNameId");
    input.setAttribute("name", "edgeName");
    input.setAttribute("value", "");
    input.setAttribute("size", "20");
    input.setAttribute("maxlength", "80");
    input.setAttribute("class", "experiment-longtextinputform");

    // Edge start node id
    var div = document.createElement("div");
    form.appendChild(div);
    var label = document.createElement("label");
    div.appendChild(label);
    label.setAttribute("for", "startNodeId");
    label.appendChild(document.createTextNode("Start node"));
    var br = document.createElement("br");
    div.appendChild(br);

    var select = document.createElement("select");
    div.appendChild(select);
    select.setAttribute("id", "startNodeId");
    select.setAttribute("name", "startNodeIDName");
    select.setAttribute("class", "experiment-simpledropdowninputform");
    
    me.startNodeIDName = form.startNodeIDName;
    select.onchange = me.doStartNodeIDNameDropdownSelect;

    // Edge start node interface
    var div = document.createElement("div");
    form.appendChild(div);
    var label = document.createElement("label");
    div.appendChild(label);
    label.setAttribute("for", "startNodeIntId");
    label.appendChild(document.createTextNode("Start node interface"));
    var br = document.createElement("br");
    div.appendChild(br);

    var select = document.createElement("select");
    div.appendChild(select);
    select.setAttribute("id", "startNodeIntId");
    select.setAttribute("name", "startNodeIntName");
    select.setAttribute("class", "experiment-simpledropdowninputform");

    // Edge end node id
    var div = document.createElement("div");
    form.appendChild(div);
    var label = document.createElement("label");
    div.appendChild(label);
    label.setAttribute("for", "endNodeId");
    label.appendChild(document.createTextNode("End node"));
    var br = document.createElement("br");
    div.appendChild(br);

    var select = document.createElement("select");
    div.appendChild(select);
    select.setAttribute("id", "endNodeId");
    select.setAttribute("name", "endNodeIDName");
    me.endNodeIDName = form.endNodeIDName;
    select.onchange = me.doEndNodeIDNameDropdownSelect;
    select.setAttribute("class", "experiment-simpledropdowninputform");

    // Edge end node interface
    var div = document.createElement("div");
    form.appendChild(div);
    var label = document.createElement("label");
    div.appendChild(label);
    label.setAttribute("for", "endNodeIntId");
    label.appendChild(document.createTextNode("Start node interface"));
    var br = document.createElement("br");
    div.appendChild(br);

    var select = document.createElement("select");
    div.appendChild(select);
    select.setAttribute("id", "endNodeIntId");
    select.setAttribute("name", "endNodeIntName");
    select.setAttribute("class", "experiment-simpledropdowninputform");

    // Create edge button
    p = document.createElement("p");
    form.appendChild(p);
    input = document.createElement("input");
    p.appendChild(input);
    input.setAttribute("type", "button");
    input.setAttribute("value", "Create edge");
    input.setAttribute("class", "experiment-simplebuttoninputform");                           
    input.onclick = window.experimentTabSVGCanvas.doCreateEdge;

    var experimentFileDiv = document.createElement("div");
    me.tabMainDiv.appendChild(experimentFileDiv);
    experimentFileDiv.setAttribute("id", "experimentFileId");
    experimentFileDiv.setAttribute("class", "experiment-experimentinfodivpanel");

    // Create submit experiment button
    form = document.createElement("form");
    experimentFileDiv.appendChild(form);
    form.setAttribute("id", "experimentIdInputFormId");
    form.setAttribute("name", "experimentIdInputFormName");

    // Experiment ID
    p = document.createElement("p");
    form.appendChild(p);
    
    label = document.createElement("label");
    p.appendChild(label);

    label.setAttribute("for", "experimentIdInputFormId");
    label.appendChild(document.createTextNode("Experiment ID  "));

    input = document.createElement("input");
    p.appendChild(input);
    input.setAttribute("type", "text");
    input.setAttribute("id", "experimentIdId");
    input.setAttribute("name", "experimentIdName");
    input.setAttribute("value", "");
    input.setAttribute("size", "18");
    input.setAttribute("maxlength", "80");
    input.setAttribute("class", "experiment-simpletextinputform");

    // Experiment description
    p = document.createElement("p");
    form.appendChild(p);

    label = document.createElement("label");
    p.appendChild(label);
   label.setAttribute("for", "experimentDescInputFormId");
    label.appendChild(document.createTextNode("Experiment Description"));
    br = document.createElement("br");
    p.appendChild(br);

    var textarea = document.createElement("textarea");
    p.appendChild(textarea);
    textarea.setAttribute("name", "experimentDescription");
    textarea.setAttribute("cols", "50");
    textarea.setAttribute("rows", "4");
    textarea.setAttribute("class", "experiment-simpletextareainputform");

    var table = document.createElement("table");
    table.setAttribute("border", "0");
    form.appendChild(table);
    
    // Start date
    var row = document.createElement("tr");
    table.appendChild(row);
    var cell1 = document.createElement("td");
    row.appendChild(cell1);
    var cell2 = document.createElement("td");
    row.appendChild(cell2);

    label = document.createElement("label");
    cell1.appendChild(label);
    label.setAttribute("for", "startDateInputFormId");
    label.setAttribute("class", "experiment-boldlabel");
    label.appendChild(document.createTextNode("Start date "));

    input = document.createElement("input");
    cell2.appendChild(input);
    input.setAttribute("type", "text");
    input.setAttribute("id", "startDateInputFormId");
    input.setAttribute("name", "startDateInputFormName");
    input.setAttribute("value", "");
    input.setAttribute("size", "18");
    input.setAttribute("maxlength", "80");
    input.setAttribute("class", "experiment-simpletextinputform");

    // End date
    var row = document.createElement("tr");
    table.appendChild(row);
    var cell1 = document.createElement("td");
    row.appendChild(cell1);
    var cell2 = document.createElement("td");
    row.appendChild(cell2);

    label = document.createElement("label");
    cell1.appendChild(label);
    label.setAttribute("for", "endDateInputFormId");
    label.setAttribute("class", "experiment-boldlabel");
    label.appendChild(document.createTextNode("End date "));

    input = document.createElement("input");
    cell2.appendChild(input);
    input.setAttribute("type", "text");
    input.setAttribute("id", "endDateInputFormId");
    input.setAttribute("name", "endDateInputFormName");
    input.setAttribute("value", "");
    input.setAttribute("size", "18");
    input.setAttribute("maxlength", "80");
    input.setAttribute("class", "experiment-simpletextinputform");

    // Write out config button
    var configWriteDiv = document.createElement("div");
    me.tabMainDiv.appendChild(configWriteDiv);
    configWriteDiv.setAttribute("id", "configWriteId");
    configWriteDiv.setAttribute("class", "experiment-experimentwritedivpanel");
    configWriteDiv.setAttribute("align", "center");

    // Create panel form
    form = document.createElement("form");
    configWriteDiv.appendChild(form);
    form.setAttribute("id", "experimentIdInputFormId");
    form.setAttribute("name", "experimentIdInputFormName");

    // Drop-down box of available experiments
    var p = document.createElement("p");
    form.appendChild(p);
    var select = document.createElement("select");
    p.appendChild(select);
    select.setAttribute("id", "configLoadSelectId");
    select.setAttribute("name", "configLoadSelectName");
    select.setAttribute("class", "experiment-simpledropdowninputform");

    // Create write experiment button
    p = document.createElement("p");
    form.appendChild(p);
    input = document.createElement("input");
    p.appendChild(input);
    input.setAttribute("type", "button");
    input.setAttribute("value", "Write experiment");
    input.setAttribute("class", "experiment-longbuttoninputform");
    input.onclick = window.experimentTabSVGCanvas.doWriteConfig;

    // Remove experiment button
    p = document.createElement("p");
    form.appendChild(p);
    var input = document.createElement("input");
    p.appendChild(input);
    input.setAttribute("type", "button");
    input.setAttribute("value", "Remove experiment");
    input.setAttribute("class", "experiment-longbuttoninputform");
    me.configLoadSelectName = form.configLoadSelectName;
    input.onclick = me.doRemoveConfig;

    // load experiment button
    p = document.createElement("p");
    form.appendChild(p);
    input = document.createElement("input");
    p.appendChild(input);
    input.setAttribute("type", "button");
    input.setAttribute("value", "Restore experiment");
    input.setAttribute("class", "experiment-longbuttoninputform");
    me.configLoadSelectName = form.configLoadSelectName;
    input.onclick = me.doExperimentLoadSelect;

    // refresh the drop-down box
    me.doRefreshConfigFileList();

    // Clear canvas button
    p = document.createElement("p");
    form.appendChild(p);
    input = document.createElement("input");
    p.appendChild(input);
    input.setAttribute("type", "button");
    input.setAttribute("value", "Clear canvas");
    input.setAttribute("class", "experiment-longbuttoninputform");
    input.onclick = window.experimentTabSVGCanvas.doClearCanvas;

    // Experiment history div
    var experimentHistoryDiv = document.createElement("div");
    me.tabMainDiv.appendChild(experimentHistoryDiv);
    experimentHistoryDiv.setAttribute("id", "experimentHistoryDivId");
    experimentHistoryDiv.setAttribute("class", "experiment-experimenthistorydivpanel");
    experimentHistoryDiv.setAttribute("align", "center");
    me.experimentHistoryXmlHttp = new XMLHttpRequest();
    var requestPage = me.experimentHistoryURL + "?username=" + me.user.username;
    me.experimentHistoryXmlHttp.onreadystatechange = me.handleHistoryReply;
    me.experimentHistoryXmlHttp.open("GET", requestPage, true);
    me.experimentHistoryXmlHttp.send(null);


    // Give the SVG canvas a reference to our main div
    window.experimentTabSVGCanvas.tabMainDiv = me.tabMainDiv;
    // Give the SVG canvas a reference to the array containing divs to manually show/hide
    window.experimentTabSVGCanvas.visibilityDivs = me.visibilityDivs;    
  };

  this.createTabs = function createTabs(mainDiv)
  {
    var topologyTab = document.createElement("div");
    topologyTab.setAttribute("id", "experiment-topologyTabId");
    topologyTab.setAttribute("class", "experimentTab activeTab");
    topologyTab.setAttribute("drawn", "false");
    topologyTab.setAttribute("tabname", "Topology");
    topologyTab.appendChild(document.createTextNode("topology"));
    topologyTab.onclick = me.toggleTabs;
    mainDiv.appendChild(topologyTab);

    var calendarTab = document.createElement("div");
    calendarTab.setAttribute("id", "experiment-calendarTabId");
    calendarTab.setAttribute("class", "experimentTab");
    calendarTab.setAttribute("drawn", "false");
    calendarTab.setAttribute("tabname", "Calendar");
    calendarTab.appendChild(document.createTextNode("calendar"));
    calendarTab.onclick = me.toggleTabs;
    mainDiv.appendChild(calendarTab);

    var filesTab = document.createElement("div");
    filesTab.setAttribute("id", "experiment-filesTabId");
    filesTab.setAttribute("class", "experimentTab");
    filesTab.setAttribute("drawn", "false");
    filesTab.setAttribute("tabname", "Files");
    filesTab.appendChild(document.createTextNode("files"));
    filesTab.onclick = me.toggleTabs;
    mainDiv.appendChild(filesTab);

    var powerTab = document.createElement("div");
    powerTab.setAttribute("id", "experiment-powerTabId");
    powerTab.setAttribute("class", "experimentTab");
    powerTab.setAttribute("drawn", "false");
    powerTab.setAttribute("tabname", "Power");
    powerTab.appendChild(document.createTextNode("power"));
    powerTab.onclick = me.toggleTabs;
    mainDiv.appendChild(powerTab);
  };

  this.initTopologyTab = function initTopologyTab()
  {
    var topologyDiv = document.createElement("div");
    me.tabMainDiv.appendChild(topologyDiv);
    topologyDiv.setAttribute("id", "experiment-topologyTabDivId");
    topologyDiv.setAttribute("class", "SVGCanvasClass");
    var style = "position: absolute;" +
                "top: " + me.CANVAS_Y_POSITION + "px;" +
                "left: " + me.CANVAS_X_POSITION + "px;" +
                "width: " + me.CANVAS_WIDTH + "px;" +
                "height: " +  me.CANVAS_HEIGHT + "px;" +
                "border: 1px solid #ccc;" +
                "border-top: 0px;";      
    topologyDiv.setAttribute("style", style);
    me.canvasTabDivs.push(topologyDiv);
    me.visibilityDivs.push(topologyDiv);

    // Embed SVG object into topology tab
    var embed = document.createElement("embed");
    topologyDiv.appendChild(embed);
    embed.setAttribute("src", "components/experiment/canvas.svg");
    embed.setAttribute("width", me.CANVAS_WIDTH);
    embed.setAttribute("height", me.CANVAS_HEIGHT);
    embed.setAttribute("type", "image/svg+xml");
  };

  this.initCalendarTab = function initCalendarTab()
  {
    var calendarDiv = document.createElement("div");
    me.tabMainDiv.appendChild(calendarDiv);
    calendarDiv.setAttribute("id", "experiment-calendarTabDivId");
    var style = "position: absolute;" +
                "top: " + me.CANVAS_Y_POSITION + "px;" +
                "left: " + me.CANVAS_X_POSITION + "px;" +
                "width: " + me.CANVAS_WIDTH + "px;" +
                "height: " +  me.CANVAS_HEIGHT + "px;" +
                "border: 1px solid #ccc;" + 
                "border-top: 0px;";
    calendarDiv.setAttribute("style", style);
    me.canvasTabDivs.push(calendarDiv);
    me.tabMainDiv.appendChild(calendarDiv);
    me.visibilityDivs.push(calendarDiv);

    // Add scrollable div
    var scrollableDiv = document.createElement("div");
    scrollableDiv.setAttribute("class", "experiment-powerscrollarea");
    scrollableDiv.setAttribute("id", "experiment-calendarScrollableDivId");
    scrollableDiv.style.width = me.CANVAS_WIDTH - 10;
    scrollableDiv.style.height = me.CANVAS_HEIGHT - 20;
    calendarDiv.appendChild(scrollableDiv);

    // Create layout table
    var table = me.drawHelper.createLayoutTable();
    table.setAttribute("id", "experiment-calendarMainTableID");
    scrollableDiv.appendChild(table);

    // Title row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("experiment-tabletitlelabel", "HEN Experiments");
    cell.appendChild(label);

    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);

    // Send request for date to populate calendar with
    me.calendarTabGetExperimentsXmlHttp = new XMLHttpRequest();
    var requestPage = me.experimentCalendarURL + "?action=getexperiments&username=" + me.user.username;
    me.calendarTabGetExperimentsXmlHttp.onreadystatechange = me.handleExperimentsReply;
    me.calendarTabGetExperimentsXmlHttp.open("GET", requestPage, true);
    me.calendarTabGetExperimentsXmlHttp.send(null);
  };

  this.handleExperimentsReply = function handleExperimentsReply()
  {
    if (me.calendarTabGetExperimentsXmlHttp.readyState == 4)
    {
      if (me.calendarTabGetExperimentsXmlHttp.status == 200)
      {
	var xmlDoc = me.calendarTabGetExperimentsXmlHttp.responseXML;
	var experiments = xmlDoc.getElementsByTagName("experiments")[0].getElementsByTagName("experiment");

	var theExperiments = new Array();
	for (var i = 0; i < experiments.length; i++)
	{
	  var experimentID = auxiliary.hen.getAttributeValue(experiments[i], "id");
	  var experimentUser = new auxiliary.hen.User(auxiliary.hen.getAttributeValue(experiments[i], "user"), null,
						      auxiliary.hen.getAttributeValue(experiments[i], "email"), null);
	  var startDate = auxiliary.hen.getAttributeValue(experiments[i], "startdate");
	  var endDate = auxiliary.hen.getAttributeValue(experiments[i], "enddate");
	  var shared = auxiliary.hen.getAttributeValue(experiments[i], "shared");
	  
	  var nodes = experiments[i].getElementsByTagName("node");
	  var nodeIDs = new Array();
	  for (var j = 0; j < nodes.length; j++)
	    nodeIDs.push(auxiliary.hen.getAttributeValue(nodes[j], "id"));
	  
	  theExperiments.push(new auxiliary.hen.Experiment(experimentID, experimentUser, startDate, endDate, nodeIDs, shared));
	}
	me.hideLoadingDiv();

	// Create the actual calendar
	var table = document.getElementById("experiment-calendarMainTableID");
	var row = me.drawHelper.createLayoutRow();
	table.appendChild(row);
	var cell = me.drawHelper.createLayoutCell();
	row.appendChild(cell);
	me.calendar = new components.experiment.calendar.Calendar(23, 10, 10, theExperiments, null, me.calendarTabGetCellInfo, "experiment-calendar", "calendarCellName", "elementID", me.user.username);
	cell.appendChild(me.calendar.createCalendar());
	me.calendar.populateAllocations(); 
      }
    }
  };
  this.calendarTabGetCellInfo = function calendarTabGetCellInfo(evt)
  {
    var cellName = evt.target.getAttribute("calendarCellName");
    if (cellName)
      me.calendar.getCellInfo(cellName);
  };

  this.initFilesTab = function initFilesTab()
  {
    var filesDiv = document.createElement("div");
    me.tabMainDiv.appendChild(filesDiv);
    filesDiv.setAttribute("id", "experiment-filesTabDivId");
    var style = "position: absolute;" +
                "top: " + me.CANVAS_Y_POSITION + "px;" +
                "left: " + me.CANVAS_X_POSITION + "px;" +
                "width: " + me.CANVAS_WIDTH + "px;" +
                "height: " +  me.CANVAS_HEIGHT + "px;" +
                "border: 1px solid #ccc;" + 
                "border-top: 0px;";
    filesDiv.setAttribute("style", style);
    me.canvasTabDivs.push(filesDiv);
    me.tabMainDiv.appendChild(filesDiv);
    me.visibilityDivs.push(filesDiv);

    // Main layout table containing two rows, each containing a table. The
    // top row table contains the controls, the bottom row table contains the fields
    var table = me.drawHelper.createLayoutTable();
    table.setAttribute("width", me.CANVAS_WIDTH - 10);
    filesDiv.appendChild(table);
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.style.backgroundColor = "#ccc";
    cell.style.border = "1px solid";

    // Create a table within the control panel to lay things out
    var selectBoxClass = "experiment-simpledropdowninputform";
    var innerTable = me.drawHelper.createLayoutTable();
    cell.appendChild(innerTable);
    innerTable.appendChild(me.drawHelper.createLayoutSpacerRow("10", "1"));
    var row = me.drawHelper.createLayoutRow();
    innerTable.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("experiment-boldlabel", "view");
    cell.appendChild(label);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("experiment-fileSubTabViewFileId", selectBoxClass, options, me.viewUserFile);
    selectBox.style.width = "85px";
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("experiment-boldlabel", "add");
    cell.appendChild(label);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please select...", "filesystem", "kernel", "loader");
    var selectBox = me.formHelper.createSelectBox("experiment-fileSubTabAddFileId", selectBoxClass, options, me.addUserFile);
    selectBox.style.width = "85px";
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("experiment-boldlabel", "edit");
    cell.appendChild(label);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("experiment-fileSubTabEditFileId", selectBoxClass, options, me.editUserFile);
    selectBox.style.width = "85px";
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("experiment-boldlabel", "delete");
    cell.appendChild(label);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("experiment-fileSubTabDeleteFileId", selectBoxClass, options, me.deleteUserFile);
    selectBox.style.width = "85px";
    cell.appendChild(selectBox);

    innerTable.appendChild(me.drawHelper.createLayoutSpacerRow("10", "1"));

    me.fileTabXmlHttp = new XMLHttpRequest();
    var requestPage = me.experimentFileURL + "?action=getfilesbyuser&username=" + me.user.username;
    me.fileTabXmlHttp.onreadystatechange = me.fileTabHandleFileIDsReply;
    me.fileTabXmlHttp.open("GET", requestPage, true);
    me.fileTabXmlHttp.send(null);

    //handleViewUserFilesReply
    var requestPage = me.experimentFileURL + "?action=getfilesbyuser&username=" + me.user.username + "&getstandard=yes";
    me.viewFilesIDsRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleViewFilesIDsReply);
    me.viewFilesIDsRequest.send();

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("5", "1"));

    // Row containing all the input fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.style.backgroundColor = "white";
    cell.style.border = "1px solid";
    cell.setAttribute("id", "experiment-fileSubTabFormsCellId"); 
  };

  this.initPowerTab = function initPowerTab()
  {
    var powerDiv = document.createElement("div");
    me.tabMainDiv.appendChild(powerDiv);
    powerDiv.setAttribute("id", "experiment-powerTabDivId");
    var style = "position: absolute;" +
                "top: " + me.CANVAS_Y_POSITION + "px;" +
                "left: " + me.CANVAS_X_POSITION + "px;" +
                "width: " + me.CANVAS_WIDTH + "px;" +
                "height: " +  me.CANVAS_HEIGHT + "px;" +
                "border: 1px solid #ccc;" +
                "border-top: 0px;";
    powerDiv.setAttribute("style", style);
    me.canvasTabDivs.push(powerDiv);
    me.tabMainDiv.appendChild(powerDiv);
    me.visibilityDivs.push(powerDiv);    

    // Add scrollable div
    var scrollableDiv = document.createElement("div");
    scrollableDiv.setAttribute("class", "experiment-powerscrollarea");
    scrollableDiv.setAttribute("id", "experiment-powerScrollableDivId");
    scrollableDiv.style.width = me.CANVAS_WIDTH - 10;
    scrollableDiv.style.height = me.CANVAS_HEIGHT - 10;
    powerDiv.appendChild(scrollableDiv);

    // Table that contains the select box and buttons
    var controlsTable = document.createElement("table");
    controlsTable.setAttribute("class", "experiment-powercontrolstable");
    controlsTable.setAttribute("align", "center");
    controlsTable.style.width = me.CANVAS_WIDTH - 10;
    scrollableDiv.appendChild(controlsTable);

    // Select box row
    var row = document.createElement("tr");
    controlsTable.appendChild(row);
    var cell = document.createElement("td");
    row.appendChild(cell);
    var selectBox = document.createElement("select");
    selectBox.setAttribute("id", "experiment-powerSelectBoxId");
    selectBox.setAttribute("class", "experiment-simpledropdowninputform");
    selectBox.onchange = me.powerDisplayNodes;
    selectBox.options[0] = new Option("plase wait...", "please wait...");
    cell.appendChild(selectBox);
    var cell = document.createElement("td");
    row.appendChild(cell);
    me.powerTabXmlHttp = new XMLHttpRequest();
    var requestPage = me.experimentHistoryURL + "?username=" + me.user.username;
    me.powerTabXmlHttp.onreadystatechange = me.powerTabHandleExperimentIDsReply;
    me.powerTabXmlHttp.open("GET", requestPage, true);
    me.powerTabXmlHttp.send(null);
    
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
    row.appendChild(cell);
    // Power on button
    var input = document.createElement("input");
    input.setAttribute("type", "button");
    input.setAttribute("id", "powerButtonOnId");
    input.setAttribute("value", "power on");
    input.setAttribute("class", "experiment-simplebuttoninputform");
    input.onclick = me.powerRequest;
    cell.appendChild(input);
    // Spacer
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("width", "5");
    cell.appendChild(img);
    // Power off button
    var input = document.createElement("input");
    input.setAttribute("type", "button");
    input.setAttribute("id", "powerButtonOffId");
    input.setAttribute("value", "power off");
    input.setAttribute("class", "experiment-simplebuttoninputform");
    input.onclick = me.powerRequest;
    cell.appendChild(input);
    // Spacer
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("width", "5");
    cell.appendChild(img);
    // Restart button
    var input = document.createElement("input");
    input.setAttribute("type", "button");
    input.setAttribute("id", "powerButtonRestartId");
    input.setAttribute("value", "restart");
    input.setAttribute("class", "experiment-simplebuttoninputform");
    input.onclick = me.powerRequest;
    cell.appendChild(input);
    // Spacer
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("width", "5");
    cell.appendChild(img);
    // Refresh button
    var input = document.createElement("input");
    input.setAttribute("type", "button");
    input.setAttribute("id", "powerButtonRefreshId");
    input.setAttribute("value", "refresh");
    input.setAttribute("class", "experiment-simplebuttoninputform");
    input.onclick = me.powerRequest;
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
  };

  this.fileTabHandleFileIDsReply = function fileTabHandleFileIDsReply()
  {
    if (me.fileTabXmlHttp.readyState == 4)
    {
      if (me.fileTabXmlHttp.status == 200)
      {
	var selectBox = document.getElementById("experiment-fileSubTabEditFileId");
	var xmlDoc = me.fileTabXmlHttp.responseXML;
	var fileNodes = xmlDoc.getElementsByTagName("experiments")[0].getElementsByTagName("filenode");

	selectBox[0] = new Option("please select...", "please select...");
	for (var i = 0; i < fileNodes.length; i++)
	{
	  var fileNodeID = auxiliary.hen.getAttributeValue(fileNodes[i], "id");
	  selectBox[i + 1] = new Option(fileNodeID, fileNodeID);
	}

	var selectBox = document.getElementById("experiment-fileSubTabDeleteFileId");
	selectBox[0] = new Option("please select...", "please select...");
	for (var i = 0; i < fileNodes.length; i++)
	{
	  var fileNodeID = auxiliary.hen.getAttributeValue(fileNodes[i], "id");
	  selectBox[i + 1] = new Option(fileNodeID, fileNodeID);
	}
      }
    }
  };

  this.clearCanvas = function clearCanvas(canvasID)
  {
    var canvas = document.getElementById(canvasID);

    while (canvas.hasChildNodes())
      {
	canvas.removeChild(canvas.firstChild);
      }
  };

  this.cancelAction = function cancelAction()
  {
    var answer = confirm("Are you sure you want to cancel?");
    if (answer)
      {
	me.clearCanvas("experiment-fileSubTabFormsCellId");
	document.getElementById("experiment-fileSubTabAddFileId").selectedIndex = 0;
	document.getElementById("experiment-fileSubTabEditFileId").selectedIndex = 0;
      }
  };

  this.viewUserFile = function viewUserFile()
  {
    var selectBox = document.getElementById("experiment-fileSubTabViewFileId");
    var selectedElementID = selectBox.value;

    if ((selectedElementID == "please select...") || (selectedElementID == "please wait..."))
      return;

    me.clearCanvas("experiment-fileSubTabFormsCellId");
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.setDisableFilesControls(true);

    me.fileTabXmlHttp2 = new XMLHttpRequest();
    var requestPage = me.experimentFileURL + "?action=elementview&elementid=" + selectedElementID;
    me.fileTabXmlHttp2.onreadystatechange = me.handleViewReply;
    me.fileTabXmlHttp2.open("GET", requestPage, true);
    me.fileTabXmlHttp2.send(null);
  };

  this.addUserFile = function addUserFile()
  {
    me.mode = "add";
    document.getElementById("experiment-fileSubTabEditFileId").selectedIndex = 0;
    var selectBox = document.getElementById("experiment-fileSubTabAddFileId");
    var selectedNodeType = selectBox.value;
    
    if ( (selectedNodeType == "please select...") || (selectedNodeType == "please wait..."))
      return;

    me.clearCanvas("experiment-fileSubTabFormsCellId");

    // Call the appropiate draw fields method dynamically
    var createFields = me["draw" + selectedNodeType[0].toUpperCase() + selectedNodeType.substring(1) + "Fields"];
    try
    {
      createFields();
    }
    catch (e)
    {
      alert("function not supported for type " + selectedNodeType);
    }
  };

  this.editUserFile = function editUserFile()
  {
    document.getElementById("experiment-fileSubTabAddFileId").selectedIndex = 0;
    var selectBox = document.getElementById("experiment-fileSubTabEditFileId");
    var selectedElementID = selectBox.value;

    if ((selectedElementID == "please select...") || (selectedElementID == "please wait..."))
      return;

    me.clearCanvas("experiment-fileSubTabFormsCellId");
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.setDisableFilesControls(true);

    me.fileTabXmlHttp2 = new XMLHttpRequest();
    var requestPage = me.experimentFileURL + "?action=elementedit&elementid=" + selectedElementID;
    me.fileTabXmlHttp2.onreadystatechange = me.handleEditReply;
    me.fileTabXmlHttp2.open("GET", requestPage, true);
    me.fileTabXmlHttp2.send(null);
  };

  this.deleteUserFile = function deleteUserFile()
  {
    var selectBox = document.getElementById("experiment-fileSubTabDeleteFileId");
    var selectedElementID = selectBox.value;
    
    if ( (selectedElementID == "please select...") || (selectedElementID == "please wait..."))
      return;

    var answer = confirm("Are you sure you want to permanently delete " + selectedElementID + "?");
    if (answer)
    {
      me.setDisableFilesControls(true);
      me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
      var requestPage = me.experimentFileURL + "?action=deletefilenode&filenodeid=" + selectedElementID;
      me.fileNodeRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleFileNodeReply);
      me.fileNodeRequest.send();
    }
  };

  this.handleFileNodeReply = function handleFileNodeReply()
  {
    if (me.fileNodeRequest.getReadyState() == 4)
    {
      if (me.fileNodeRequest.getStatus() == 200)
      {
        me.hideLoadingDiv();
	me.setDisableFilesControls(false);

	var xmlDoc = me.fileNodeRequest.getResponseXML();
	var result = xmlDoc.getElementsByTagName("experiment")[0].getElementsByTagName("result")[0];
	var operation = auxiliary.hen.getAttributeValue(result, "operation");
	var fileNodeID = auxiliary.hen.getAttributeValue(result, "filenodeid");
	var value = auxiliary.hen.getAttributeValue(result, "value");
	var fileNodeType = document.getElementById("experiment-fileSubTabAddFileId").value; 

	if (operation == "delete")
	{
	  if (value == "0")
	  {
	    var selectBox = document.getElementById("experiment-fileSubTabEditFileId");
	    for (var i = 0; i < selectBox.options.length; i++)
	    {
	      if (selectBox[i].value == fileNodeID)
	      {
		selectBox.options[i] = null;
		break;
	      }
	    }
	    var selectBox = document.getElementById("experiment-fileSubTabDeleteFileId");
	    selectBox.selectedIndex = 0;
	    for (var i = 0; i < selectBox.options.length; i++)
	    {
	      if (selectBox[i].value == fileNodeID)
	      {
		selectBox.options[i] = null;
		break;
	      }
	    }
	    var selectBox = document.getElementById("experiment-fileSubTabViewFileId");
	    for (var i = 0; i < selectBox.options.length; i++)
	    {
	      if (selectBox[i].value == fileNodeID)
	      {
		selectBox.options[i] = null;
		break;
	      }
	    }
	    alert("success! deleted " + fileNodeID);
	  }
	  else
	  {
	    alert("error while deleting " + fileNodeID);
	  }
	}
	else if (operation == "create")
	{
	  if (value == "0")
	  {
	    var selectBox = document.getElementById("experiment-fileSubTabEditFileId");
	    selectBox[selectBox.options.length] = new Option(fileNodeID, fileNodeID);
	    var selectBox = document.getElementById("experiment-fileSubTabDeleteFileId");
	    selectBox[selectBox.options.length] = new Option(fileNodeID, fileNodeID);
	    var selectBox = document.getElementById("experiment-fileSubTabViewFileId");
	    selectBox[selectBox.options.length] = new Option(fileNodeID, fileNodeID);
	    alert("success! created " + fileNodeID);
	  }
	  else
	  {
	    alert("error while adding " + fileNodeType);
	  }
	}
	else if (operation == "edit")
	{
	  if (value == "0")
	  {
	    alert("success! edited " + fileNodeID);
	  }
	  else
	  {
	    alert("error while editing " + fileNodeID);
	  }
	}
	me.clearCanvas("experiment-fileSubTabFormsCellId");
	document.getElementById("experiment-fileSubTabEditFileId").selectedIndex = 0;
	document.getElementById("experiment-fileSubTabAddFileId").selectedIndex = 0;
      }
    }
  };

  this.handleViewReply = function handleViewReply()
  {
    if (me.fileTabXmlHttp2.readyState == 4)
    {
      if (me.fileTabXmlHttp2.status == 200)
      {
	document.getElementById("experiment-fileSubTabViewFileId").selectedIndex = 0;
	document.getElementById("experiment-fileSubTabAddFileId").selectedIndex = 0;
	document.getElementById("experiment-fileSubTabEditFileId").selectedIndex = 0;
	var numberColumns = "1";
	var mainCell = document.getElementById("experiment-fileSubTabFormsCellId");
	var table = document.createElement("table");
	var fileNode = me.fileTabXmlHttp2.responseXML.getElementsByTagName("experiment")[0].firstChild.nodeValue;
	table.setAttribute("id", "experiment-filenodetableid");
	mainCell.appendChild(table);
	table.setAttribute("align", "center");
	table.setAttribute("width", me.CANVAS_WIDTH - 10);

	var row = me.drawHelper.createLayoutRow();
	table.appendChild(row);
	var cell = me.drawHelper.createLayoutCell();
	cell.setAttribute("colspan", numberColumns);
	cell.setAttribute("align", "center");
	row.appendChild(cell);
	var label = me.drawHelper.createLabel("experiment-normallabel", fileNode);
	cell.appendChild(label);
	me.hideLoadingDiv();	
	me.setDisableFilesControls(false);
      }
    }
  };

  this.handleEditReply = function handleEditReply()
  {
    if (me.fileTabXmlHttp2.readyState == 4)
    {
      if (me.fileTabXmlHttp2.status == 200)
      {
	me.hideLoadingDiv();
	me.setDisableFilesControls(false);

	me.mode = "edit"
	var xmlDoc = me.fileTabXmlHttp2.responseXML;
	var element = xmlDoc.getElementsByTagName("experiments")[0].getElementsByTagName("element")[0];
	var elementType = auxiliary.hen.getAttributeValue(element, "type");
	var properties = element.getElementsByTagName("property");
	var attributes = element.getElementsByTagName("attribute");

	// Call the appropiate draw fields method dynamically
	var createFields = me["draw" + elementType[0].toUpperCase() + elementType.substring(1) + "Fields"];
	createFields();
        originalElementType = elementType;
	if (elementType == "kernel" || elementType == "loader")
	  elementType = "filesystem";
	me.populateFields(elementType, properties, attributes, originalElementType);
	
	// Populate attributes text area, which is common to all elements
	var textArea = document.getElementById("experiment-filenodeattributesid");
	for (var i = 0; i < attributes.length; i++)
	{
	  var attributeName = auxiliary.hen.getAttributeValue(attributes[i], "name");
	  var attributeValue = auxiliary.hen.getAttributeValue(attributes[i], "value");
	  textArea.value += attributeName + " = " + attributeValue + "\n";
	}
      }
    }
  };

  this.populateFields = function populateFields(elementType, properties, attributes, originalElementType)
  {
    var label = document.getElementById("experiment-" + originalElementType + "MainTitleId");
    label.removeChild(label.firstChild);
    label.appendChild(document.createTextNode("Edit " + originalElementType));
    var button = document.getElementById("experiment-" + originalElementType + "CreateButtonId");
    button.setAttribute("value", "Edit " + originalElementType);
    button.onclick = me.editFileNode;

    var pathCell = document.getElementById("experiment-filenodepathcellid");
    pathCell.removeChild(pathCell.firstChild);
    var textBox = me.formHelper.createTextBox("experiment-filenodepathid", me.textBoxClass, "");
    pathCell.appendChild(textBox);

    for (var i = 0; i < properties.length; i++)
    {
      var propertyName = auxiliary.hen.getAttributeValue(properties[i], "name");
      var propertyValue = auxiliary.hen.getAttributeValue(properties[i], "value");

      var input = document.getElementById("experiment-" + elementType + propertyName + "id");
      if (!input)
	input = document.getElementById("experiment-filenode" + propertyName + "id");

      if ( (input.type == "text") || (input.type == "password") )
	input.value = propertyValue;
      else if (input.type == "select-one")
      {
	// If the value is already in the select box, select it, otherwise add it and select it, always
	// leaving the last option as last (in case it's other...)
	var isInSelectBox = false;
	var foundIndex;
	for (var j = 0; j < input.options.length; j++)
	  if (input.options[j].value == propertyValue)
	  {
	    isInSelectBox = true;
	    foundIndex = j;
	    break;
	  }
	
	if (isInSelectBox)
	  input.selectedIndex = foundIndex;
        else
	{
	  var previousLastOption = input.options[input.options.length - 1].value;
	  input.options[input.options.length - 1] = new Option(propertyValue, propertyValue);
	  input.options[input.options.length] = new Option(previousLastOption, previousLastOption);
	  input.selectedIndex = input.options.length - 2;
	}
      }      
    }
    textBox.readOnly = true;
  };

  this.handleFileNamesReply = function handleFileNamesReply()
  {
    if (me.fileNamesRequest.getReadyState() == 4)
    {
      if (me.fileNamesRequest.getStatus() == 200)
      {
	me.setDisableFilesControls(false);
	me.hideLoadingDiv();
	if (me.mode == "edit")
	  return;
	var xmlDoc = me.fileNamesRequest.getResponseXML();
	var filenames = xmlDoc.getElementsByTagName("experiment")[0].getElementsByTagName("filenode");
	
	var selectBox = document.getElementById("experiment-filenodepathid");
	selectBox.length = 0;
	selectBox[0] = new Option("please select...", "please select...");
	for (var i = 0; i < filenames.length; i++)
	  selectBox[i + 1] = new Option(auxiliary.hen.getAttributeValue(filenames[i], "name"));

	var fileNodeType = document.getElementById("experiment-fileSubTabAddFileId").value;
	if (selectBox.options.length > 1)
	{
	}
	else
	{
	  alert("you have no " + fileNodeType + "s in your directory that are not already in the testbed");
	  me.clearCanvas("experiment-fileSubTabFormsCellId");
	}
      }
    }
  };


  this.drawFilesystemFields = function drawFilesystemFields()
  {
    var mainCell = document.getElementById("experiment-fileSubTabFormsCellId");
    // Create the table where all the input fields will go
    var table = document.createElement("table");
    table.setAttribute("id", "experiment-filenodetableid");
    mainCell.appendChild(table);
    table.setAttribute("align", "center");
    table.setAttribute("width", me.CANVAS_WIDTH - 10);
    var numberColumns = "3";

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("experiment-tabletitlelabel", "Add Filesystem");
    label.setAttribute("id", "experiment-filesystemMainTitleId");
    cell.appendChild(label);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Draw the fields common to all file nodes
    me.drawFileNodeFields(table);

    // Add and populate the paths select box
    var selectBoxCell = document.getElementById("experiment-filenodepathcellid");
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("experiment-filenodepathid", "experiment-simpledropdowninputform", options, null);
    selectBox.style.width = "120px";
    selectBoxCell.appendChild(selectBox);

    var requestPage = me.experimentFileURL + "?action=getfilesindir&username=" + me.user.username + "&filenodetype=filesystem"
    me.fileNamesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleFileNamesReply);
    me.fileNamesRequest.send();

    // Titles for username and password fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("id", "experiment-filesystemUsernameLabelCellId");
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("experiment-boldlabel", "username"));
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("id", "experiment-filesystemPasswordLabelCellId");
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("experiment-boldlabel", "password"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Username and password fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("id", "experiment-filesystemUsernameCellId");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("experiment-filesystemusernameid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("id", "experiment-filesystemPasswordCellId");
    row.appendChild(cell);
    var textBox = me.formHelper.createPasswordBox("experiment-filesystempasswordid", me.textBoxClass);
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Draw attribute fields
    me.drawAttributeFields(table);

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("experiment-filesystemCreateButtonId", me.buttonClass, "Add filesystem", me.addFileNode);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("experiment-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    me.setDisableFilesControls(true);
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
  };

  this.drawKernelFields = function drawKernelFields()
  {
    var mainCell = document.getElementById("experiment-fileSubTabFormsCellId");
    // Create the table where all the input fields will go
    var table = document.createElement("table");
    table.setAttribute("id", "experiment-filenodetableid");
    mainCell.appendChild(table);
    table.setAttribute("align", "center");
    table.setAttribute("width", me.CANVAS_WIDTH - 10);
    var numberColumns = "3";

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("experiment-tabletitlelabel", "Add Kernel");
    label.setAttribute("id", "experiment-kernelMainTitleId");
    cell.appendChild(label);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Draw the fields common to all file nodes
    me.drawFileNodeFields(table);

    // Add and populate the paths select box
    var selectBoxCell = document.getElementById("experiment-filenodepathcellid");
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("experiment-filenodepathid", "experiment-simpledropdowninputform", options, null);
    selectBox.style.width = "120px";
    selectBoxCell.appendChild(selectBox);

    var requestPage = me.experimentFileURL + "?action=getfilesindir&username=" + me.user.username + "&filenodetype=kernel"
    me.fileNamesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleFileNamesReply);
    me.fileNamesRequest.send();

    // Draw attribute fields
    me.drawAttributeFields(table);

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("experiment-kernelCreateButtonId", me.buttonClass, "Add kernel", me.addFileNode);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("experiment-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));
  };

  this.drawLoaderFields = function drawLoaderFields()
  {
    var mainCell = document.getElementById("experiment-fileSubTabFormsCellId");
    // Create the table where all the input fields will go
    var table = document.createElement("table");
    table.setAttribute("id", "experiment-filenodetableid");
    mainCell.appendChild(table);
    table.setAttribute("align", "center");
    table.setAttribute("width", me.CANVAS_WIDTH - 10);
    var numberColumns = "3";

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("experiment-tabletitlelabel", "Add Loader");
    label.setAttribute("id", "experiment-loaderMainTitleId");
    cell.appendChild(label);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Draw the fields common to all file nodes
    me.drawFileNodeFields(table);

    // Add and populate the paths select box
    var selectBoxCell = document.getElementById("experiment-filenodepathcellid");
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("experiment-filenodepathid", "experiment-simpledropdowninputform", options, null);
    selectBox.style.width = "120px";
    selectBoxCell.appendChild(selectBox);

    var requestPage = me.experimentFileURL + "?action=getfilesindir&username=" + me.user.username + "&filenodetype=loader"
    me.fileNamesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleFileNamesReply);
    me.fileNamesRequest.send();

    // Draw attribute fields
    me.drawAttributeFields(table);

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("experiment-loaderCreateButtonId", me.buttonClass, "Add loader", me.addFileNode);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("experiment-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));
  };

  this.drawFileNodeFields = function drawFileNodeFields(table)
  {
    var numberColumns = "3";

    // Titles for path, architecture and os type fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("experiment-boldlabel", "path"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("experiment-boldlabel", "architecture"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("experiment-boldlabel", "OS type"));
    var cell = me.drawHelper.createLayoutCell();

    // Path, architecture and os type fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("id", "experiment-filenodepathcellid");
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("experiment-filenodearchitectureid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("experiment-filenodeostypeid", me.textBoxClass, "");
    cell.appendChild(textBox);

    // Titles for version and description fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("experiment-boldlabel", "version"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("experiment-boldlabel", "description"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Version and description fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("experiment-filenodeversionid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("experiment-filenodedescriptionid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
  };

  this.drawAttributeFields = function drawAttributeFields(table)
  {
    var numberColumns = "3";

    // Titles for attribute name and value fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("experiment-boldlabel", "attribute name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("experiment-boldlabel", "attribute value"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Attribute name, value and add button fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("experiment-filenodeattributenameid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("experiment-filenodeattributevalueid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var button = me.formHelper.createButton("experiment-filenodeAddAttributeButtonId", me.buttonClass, "Add attribute", me.addAttribute);
    button.setAttribute("resultTextAreaId", "experiment-filenodeattributesid");
    button.setAttribute("attributeNameId", "experiment-filenodeattributenameid");
    button.setAttribute("attributeValueId", "experiment-filenodeattributevalueid");
    cell.appendChild(button);

    // Title for attribute list field
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("experiment-boldlabel", "attribute list"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Attribute list field
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", "3");
    cell.setAttribute("align", "left");
    row.appendChild(cell);
    var textArea = me.formHelper.createTextArea("experiment-filenodeattributesid", me.textAreaClass, "2", "40");
    cell.appendChild(textArea);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("30", numberColumns));

  };

  this.editFileNode = function editFileNode()
  {
    var fileNodeID = document.getElementById("experiment-fileSubTabEditFileId").value;
    var owner = me.user.username;
    var path = document.getElementById("experiment-filenodepathid").value;
    var architecture = document.getElementById("experiment-filenodearchitectureid").value;
    var osType = document.getElementById("experiment-filenodeostypeid").value;
    var version = document.getElementById("experiment-filenodeversionid").value;
    var description = document.getElementById("experiment-filenodedescriptionid").value;

    var username = " ";
    var password = " ";
    try
    {
      username = document.getElementById("experiment-filesystemusernameid").value;
      password = document.getElementById("experiment-filesystempasswordid").value;
    }
    catch (e) {}

    var attributes = new Array();
    try
    {
      var unparsedAttributes = new Array();
      unparsedAttributes = document.getElementById("experiment-filenodeattributesid").value.split("\n");
      for (var i = 0; i < unparsedAttributes.length - 1; i++)
      {
	var attributeName = unparsedAttributes[i].substring(0, unparsedAttributes[i].indexOf("=") - 1);
	if (attributeName.indexOf(" ") != -1)
	{
	  alert("attribute names must not contain spaces: " + attributeName);
	  return;
	}
	var attributeValue = unparsedAttributes[i].substring(unparsedAttributes[i].indexOf("=") + 2);
	attributes[attributeName] = attributeValue;
      }
    }
    catch (e) {}

    // Form checking
    if (path == "please select...")
    {
      alert("you must select an option from the path select box");
      return;
    }
    if (architecture == "")
    {
      alert("you must fill in the architecture box");
      return;
    }
    if (osType == "")
    {
      alert("you must fill in the os type box");
      return;
    }
    if (description == "")
    {
      alert("you must fill in the description");
      return;
    }

    var answer = confirm("Are you sure you want to edit " + fileNodeID + "?");
    if (answer)
    {
      var requestPage =  me.experimentFileURL + "?action=editfilenode" + 
	                 "&filenodeid=" + escape(fileNodeID) + 
	                 "&owner=" +  escape(me.user.username) + 
	                 "&path=" +  escape(path) + 
	                 "&architecture=" +  escape(architecture) + 
	                 "&ostype=" +  escape(osType) +
	                 "&version=" + escape(version) + 
	                 "&mustclone=no" + 
	                 "&description=" + escape(description) +
	                 "&username=" + escape(username) + 
	                 "&password=" + escape(password);

      for (var key in attributes)
	requestPage += "&" + key + "=" + escape(attributes[key]);

      me.setDisableFilesControls(true);
      me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
      me.fileNodeRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleFileNodeReply);
      me.fileNodeRequest.send();
    }
  };

  this.addFileNode = function addFileNode()
  {
    var fileNodeType = document.getElementById("experiment-fileSubTabAddFileId").value;
    var owner = me.user.username;
    var path = document.getElementById("experiment-filenodepathid").value;
    var architecture = document.getElementById("experiment-filenodearchitectureid").value;
    var osType = document.getElementById("experiment-filenodeostypeid").value;
    var version = document.getElementById("experiment-filenodeversionid").value;
    var description = document.getElementById("experiment-filenodedescriptionid").value;

    var attributes = new Array();
    try
    {
      var unparsedAttributes = new Array();
      unparsedAttributes = document.getElementById("experiment-filenodeattributesid").value.split("\n");
      for (var i = 0; i < unparsedAttributes.length - 1; i++)
      {
	var attributeName = unparsedAttributes[i].substring(0, unparsedAttributes[i].indexOf("=") - 1);
	if (attributeName.indexOf(" ") != -1)
	{
	  alert("attribute names must not contain spaces: " + attributeName);
	  return;
	}
	var attributeValue = unparsedAttributes[i].substring(unparsedAttributes[i].indexOf("=") + 2);
	attributes[attributeName] = attributeValue;
      }
    }
    catch (e) {}

    var username = " ";
    var password = " ";
    try
    {
      username = document.getElementById("experiment-filesystemusernameid").value;
      password = document.getElementById("experiment-filesystempasswordid").value;
    }
    catch (e) {}

    // Form checking
    if (path == "please select...")
    {
      alert("you must select an option from the path select box");
      return;
    }
    if (architecture == "")
    {
      alert("you must fill in the architecture box");
      return;
    }
    if (osType == "")
    {
      alert("you must fill in the os type box");
      return;
    }
    if (description == "")
    {
      alert("you must fill in the description");
      return;
    }

    var answer = confirm("Are you sure you want to add the file?");
    if (answer)
    {
      var requestPage =  me.experimentFileURL + "?action=createfilenode" + 
	                 "&filenodetype=" + escape(fileNodeType) + 
	                 "&owner=" +  escape(me.user.username) + 
	                 "&path=" +  escape(path) + 
	                 "&architecture=" +  escape(architecture) + 
	                 "&ostype=" +  escape(osType) +
	                 "&version=" + escape(version) + 
	                 "&mustclone=no" + 
	                 "&description=" + escape(description) +
	                 "&username=" + escape(username) + 
	                 "&password=" + escape(password);

      for (var key in attributes)
	requestPage += "&" + key + "=" + escape(attributes[key]);

      me.setDisableFilesControls(true);
      me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
      me.fileNodeRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleFileNodeReply);
      me.fileNodeRequest.send();
    }
  };

  this.addAttribute = function addAttribute(evt)
  {
    var textArea = document.getElementById(evt.target.getAttribute("resultTextAreaId"));
    var attributeNameBox = document.getElementById(evt.target.getAttribute("attributeNameId"));
    var attributeValueBox = document.getElementById(evt.target.getAttribute("attributeValueId"));

    textArea.value += attributeNameBox.value + " = " + attributeValueBox.value + "\n";

    attributeNameBox.value = "";
    attributeValueBox.value = "";
  };

  this.closePopUp = function closePopUp()
  {
    var popUpDiv = document.getElementById("experiment-floatingInputDivId");
    popUpDiv.style.visibility = "hidden";
  };

  this.showPopUp = function showPopUp(evt)
  {
    var selectBoxID = evt.target.id;
    var box = document.getElementById(selectBoxID);
    var value = box.options[box.selectedIndex].value;
    if (value == "other...")
    {
      if (!me.createdPopUp)
	me.createPopUp();

      var popUpDiv = document.getElementById("experiment-floatingInputDivId");
      var popUpDivLabel = document.getElementById("experiment-floatingInputDivLabelId");
      var popUpDivInput = document.getElementById("experiment-floatingInputDivInputId");
      var inputLabel = box.getAttribute("popuplabel");

      // Clear any existing labels and display the given one
      try
      {
	popUpDivLabel.removeChild(popUpDivLabel.firstChild);
      }
      catch (e) {}
      popUpDivLabel.appendChild(document.createTextNode(inputLabel));
      
      // Save this value so that we can later place the value of the input box back into the select box
      popUpDiv.setAttribute("returnSelectBoxId", selectBoxID);
      
      // Clear any previous input
      popUpDivInput.value = "";

      // Show the div
      popUpDiv.style.visibility = "visible";

      // Give the input box focus
      popUpDivInput.focus();
    }
  };

  this.createPopUp = function createPopUp()
  {
    me.floatingInputDiv = document.createElement("div");
    me.floatingInputDiv.setAttribute("id", "experiment-floatingInputDivId");
    me.floatingInputDiv.setAttribute("class", "experiment-floatinginput");
    me.floatingInputDiv.style.visibility = "hidden";
    me.floatingInputDiv.style.left = me.POP_UP_X_POSITION;
    me.floatingInputDiv.style.top = me.POP_UP_Y_POSITION;
    me.floatingInputDiv.style.width = me.POP_UP_WIDTH;
    me.floatingInputDiv.style.height = me.POP_UP_HEIGHT;

    // Create table for layout
    var table = document.createElement("table");
    table.setAttribute("class", "experiment-layouttable");
    table.setAttribute("width", me.POP_UP_WIDTH);
    me.floatingInputDiv.appendChild(table);
    // First row contains close button
    var row = document.createElement("tr");
    row.setAttribute("class", "experiment-row");
    table.appendChild(row);
    var cell = document.createElement("td");
    row.appendChild(cell);
    cell.setAttribute("align", "right");
    cell.setAttribute("class", "experiment-layoutcell");
    var img = document.createElement("img");
    img.src = "images/close.gif";
    img.onclick = me.closePopUp;
    cell.appendChild(img);

    // Second row contains just a label
    var row = document.createElement("tr");
    row.setAttribute("class", "experiment-row");
    table.appendChild(row);
    var cell = document.createElement("td");
    cell.setAttribute("class", "experiment-layoutcell");
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = document.createElement("label");
    label.setAttribute("id", "experiment-floatingInputDivLabelId");
    label.setAttribute("class", "experiment-boldlabel");
    cell.appendChild(label);

    // Third row contains the input box
    var row = document.createElement("tr");
    row.setAttribute("class", "experiment-row");
    table.appendChild(row);
    var cell = document.createElement("td");
    cell.setAttribute("class", "experiment-layoutcell");
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var input = document.createElement("input");
    cell.appendChild(input);
    input.setAttribute("type", "text");
    input.setAttribute("id", "experiment-floatingInputDivInputId");
    input.setAttribute("value", "");
    input.setAttribute("size", "20");
    input.setAttribute("maxlength", "80");
    input.setAttribute("class", "experiment-longtextinputform");
    // Fourth row contains the submit button
    var row = document.createElement("tr");
    row.setAttribute("class", "experiment-row");
    table.appendChild(row);
    var cell = document.createElement("td");
    cell.setAttribute("class", "experiment-layoutcell");
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var input = document.createElement("input");
    cell.appendChild(input);
    input.setAttribute("type", "button");
    input.setAttribute("value", "Enter");
    input.setAttribute("class", "experiment-simplebuttoninputform");
    input.onclick = me.popInputSubmit;
    // Fifth row is a spacer row
    var row = document.createElement("tr");
    row.setAttribute("class", "experiment-row");
    table.appendChild(row);
    var cell = document.createElement("td");
    cell.setAttribute("class", "experiment-layoutcell");
    row.appendChild(cell);
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("height", "10");
    cell.appendChild(img);

    me.visibilityDivs.push(me.floatingInputDiv);
    me.tabMainDiv.appendChild(me.floatingInputDiv);
    me.createdPopUp = true;
  };

  this.popInputSubmit = function popInputSubmit()
  {
    var popUpDiv = document.getElementById("experiment-floatingInputDivId");
    var popUpDivInput = document.getElementById("experiment-floatingInputDivInputId");

    // Hide the div
    popUpDiv.style.visibility = "hidden";

    // Retrieve the select box that originated the pop-up and populate it with the value of the input
    var selectBox = document.getElementById(popUpDiv.getAttribute("returnSelectBoxId"));
    var value = popUpDivInput.value;

    selectBox[selectBox.options.length - 1] = new Option(value, value);
    selectBox[selectBox.options.length] = new Option("other...", "other...");
    selectBox.selectedIndex = selectBox.options.length - 2;
  };

  this.powerDisplayNodes = function powerDisplayNodes()
  {
    var selectBox = document.getElementById("experiment-powerSelectBoxId");
    var experimentID = selectBox.options[selectBox.selectedIndex].value;

    if (experimentID != "please select")
    {
      me.powerTabXmlHttp2 = new XMLHttpRequest();
      var requestPage = me.experimentHistoryURL + "?username=" + me.user.username + "&experimentid=" + experimentID;
      me.powerTabXmlHttp2.onreadystatechange = me.powerTabHandleNodeIDsReply;
      me.powerTabXmlHttp2.open("GET", requestPage, true);
      me.powerTabXmlHttp2.send(null);
    }
  };

  this.PowerTabEntry = function(nodeID, experimentID, hasPowerSwitch)
  {
    this.nodeID = nodeID;
    this.experimentID = experimentID;
    this.hasPowerSwitch = hasPowerSwitch;
  };


  this.powerTabHandleNodeIDsReply = function powerTabHandleNodeIDsReply()
  {
    if (me.powerTabXmlHttp2.readyState == 4)
    {
      if (me.powerTabXmlHttp2.status == 200)
      {
	var xmlDoc = me.powerTabXmlHttp2.responseXML;
	var experiments = xmlDoc.getElementsByTagName("experiments")[0].getElementsByTagName("experiment");

	// Retrieve all the node ids and put them in an array
	var nodeIDs = new Array();
	for (var i = 0; i < experiments.length; i++)
	{
	  var experimentID = auxiliary.hen.getAttributeValue(experiments[i], "id");
	  var nodes = experiments[i].getElementsByTagName("node");
	  for (var j = 0; j < nodes.length; j++)
	  {
	    var hasPowerSwitch = auxiliary.hen.getAttributeValue(nodes[j], "haspowerswitch");
	    var nodeID = (auxiliary.hen.getAttributeValue(nodes[j], "id"));
	    nodeIDs.push(new me.PowerTabEntry(nodeID, experimentID, hasPowerSwitch));
	  }
	}
	
	// Create the table that will hold the node ids along with a header row, but first
	// erase any previously drawn ones
	var scrollableDiv = document.getElementById("experiment-powerScrollableDivId");
	try
	{
	  var nodesTable = document.getElementById("experiment-powerTableId");
	  scrollableDiv.removeChild(nodesTable);
	}
	catch (e) {}
	var nodesTable = document.createElement("table");
	nodesTable.setAttribute("class", "experiment-powertable");
	nodesTable.setAttribute("id", "experiment-powerTableId");
	nodesTable.setAttribute("align", "center");
	nodesTable.style.width = me.CANVAS_WIDTH - 10;
	scrollableDiv.appendChild(nodesTable);

	// Print the row containing the select all, deselect all buttons
	var row = document.createElement("tr");
	row.setAttribute("class", "experiment-powerrow");
	nodesTable.appendChild(row);
	var cell = document.createElement("td");
	cell.setAttribute("class", "experiment-powercell");
	cell.setAttribute("align", "left");
	cell.setAttribute("colspan", "4");
	row.appendChild(cell);
	var checkBox = document.createElement("input");
	checkBox.setAttribute("type", "checkbox");
	checkBox.setAttribute("class", "experiment-simplecheckboxinput");
	checkBox.setAttribute("id", "experiment-powerCheckBoxAll");
	checkBox.onclick = me.powerTabSelectCheckBoxes;
	cell.appendChild(checkBox);
	var headingLabel = document.createElement("label");
	headingLabel.setAttribute("class", "experiment-boldlabel");
	cell.appendChild(headingLabel);
	headingLabel.appendChild(document.createTextNode("all"));
	var checkBox = document.createElement("input");
	checkBox.setAttribute("type", "checkbox");
	checkBox.setAttribute("class", "experiment-simplecheckboxinput");
	checkBox.setAttribute("id", "experiment-powerCheckBoxNone");
	checkBox.onclick = me.powerTabSelectCheckBoxes;
	cell.appendChild(checkBox);
	var headingLabel = document.createElement("label");
	headingLabel.setAttribute("class", "experiment-boldlabel");
	cell.appendChild(headingLabel);
	headingLabel.appendChild(document.createTextNode("none"));

	var headings = new Array();
	headings.push("select");
	headings.push("node id");
	headings.push("node status");
	headings.push("experiment");
	var headingsRow = document.createElement("tr");
	headingsRow.setAttribute("class", "experiment-powerrow");
	nodesTable.appendChild(headingsRow);
	for (var i = 0; i < headings.length; i++)
	{
	  var headingCell = document.createElement("td");
	  headingCell.setAttribute("class", "experiment-powercell");
	  headingCell.setAttribute("align", "center");
	  headingsRow.appendChild(headingCell);
	  var headingLabel = document.createElement("label");
	  headingLabel.setAttribute("class", "experiment-boldlabel");
	  headingCell.appendChild(headingLabel);
	  headingLabel.appendChild(document.createTextNode(headings[i]));
	}

	// For each node print a row containing a checkbox, the nodeid, and its (for now unknown) power status
	me.powerTabNumberNodes = nodeIDs.length;
	for (var i = 0; i < nodeIDs.length; i++)
	{
	  var row = document.createElement("tr");
	  row.setAttribute("class", "experiment-powerrow");
	  nodesTable.appendChild(row);

	  // Checkbox
	  var cell = document.createElement("td");
	  cell.setAttribute("class", "experiment-powercell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  var checkBox = document.createElement("input");
	  checkBox.setAttribute("type", "checkbox");
	  checkBox.setAttribute("class", "experiment-simplecheckboxinput");
	  checkBox.setAttribute("id", "experiment-powerCheckBox" + i);
	  checkBox.setAttribute("nodeid", nodeIDs[i].nodeID);
	  if (nodeIDs[i].hasPowerSwitch == "no")
	  {
	    checkBox.checked = false;
	    checkBox.disabled = true;
	    checkBox.setAttribute("nopowerswitch", "true");
	  }
	  cell.appendChild(checkBox);

	  // Node id 
	  var cell = document.createElement("td");
	  cell.setAttribute("class", "experiment-powercell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  var label = document.createElement("label");
	  label.setAttribute("class", "experiment-normallabel");
	  cell.appendChild(label);
	  label.appendChild(document.createTextNode(nodeIDs[i].nodeID));

	  // Status 
	  var cell = document.createElement("td");
	  cell.setAttribute("class", "experiment-powercell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  var label = document.createElement("label");
	  label.setAttribute("class", "experiment-normallabel");
	  label.setAttribute("id", "experiment-powerLabel" + nodeIDs[i].nodeID);
	  cell.appendChild(label);
	  if (nodeIDs[i].hasPowerSwitch == "yes")
	    label.appendChild(document.createTextNode("unknown"));
	  else
	    label.appendChild(document.createTextNode("no powerswitch"));

	  // Experiment
	  var cell = document.createElement("td");
	  cell.setAttribute("class", "experiment-powercell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  var label = document.createElement("label");
	  label.setAttribute("class", "experiment-normallabel");
	  cell.appendChild(label);
	  label.appendChild(document.createTextNode(nodeIDs[i].experimentID));
	}

	me.powerRequest(null, true);
      }
    }
  };

  this.powerTabSelectCheckBoxes = function powerTabSelectCheckBoxes(evt)
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
    for (var i = 0; i < me.powerTabNumberNodes; i++)
    {
      var checkBox = document.getElementById("experiment-powerCheckBox" + i);
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

  this.setDisableFilesControls = function setDisableFilesControls(disable)
  {
    document.getElementById("experiment-fileSubTabAddFileId").disabled = disable;
    document.getElementById("experiment-fileSubTabEditFileId").disabled = disable;
    document.getElementById("experiment-fileSubTabDeleteFileId").disabled = disable;
	  // Re-enable submit button
    try
    {
      document.getElementById("experiment-filesystemCreateButtonId").disable = disable;
      document.getElementById("experiment-kernelCreateButtonId").disable = disable;
      document.getElementById("experiment-loaderCreateButtonId").disable = disable;
    }
    catch (e) {}
  };

  this.setDisablePowerControls = function setDisablePowerControls(disable)
  {
    document.getElementById("powerButtonOnId").disabled = disable;
    document.getElementById("powerButtonOffId").disabled = disable;
    document.getElementById("powerButtonRestartId").disabled = disable;
    document.getElementById("powerButtonRefreshId").disabled = disable;
    document.getElementById("experiment-powerSelectBoxId").disabled = disable;
    document.getElementById("experiment-powerCheckBoxNone").disabled = disable;
    document.getElementById("experiment-powerCheckBoxAll").disabled = disable;

    for (var i = 0; i < me.powerTabNumberNodes; i++)
    {
      var checkBox = document.getElementById("experiment-powerCheckBox" + i);
      // Do not change checkboxes that are disabled because the node has no power switch
      if (checkBox.getAttribute("nopowerswitch") != "true")
	document.getElementById("experiment-powerCheckBox" + i).disabled = disable;
    }
  };

  this.powerTabHandleExperimentIDsReply = function powerTabHandleExperimentIDsReply()
  {
    if (me.powerTabXmlHttp.readyState == 4)
    {
      if (me.powerTabXmlHttp.status == 200)
      {
	var selectBox = document.getElementById("experiment-powerSelectBoxId");
	var xmlDoc = me.powerTabXmlHttp.responseXML;
	var experiments = xmlDoc.getElementsByTagName("experiments")[0].getElementsByTagName("experiment");
	
	selectBox.options[0] = new Option("please select", "please select");
	selectBox.options[1] = new Option("all", "all");
	for (var i = 0; i < experiments.length; i++)
	{
	  var experimentID = auxiliary.hen.getAttributeValue(experiments[i], "id");
	  selectBox.options[i + 2] = new Option(experimentID, experimentID);
	}
      }
    }
  };

  this.powerRequest = function powerRequest(evt, statusAllRequest)
  {
    var selectedNodes = new Array();

    if (statusAllRequest != null)
    {
      for (var i = 0; i < me.powerTabNumberNodes; i++)
      {
	var checkBox = document.getElementById("experiment-powerCheckBox" + i);
	if (!checkBox.disabled)
	  selectedNodes.push(checkBox.getAttribute("nodeid"));
      }
    }
    else
    {
      var buttonID = null;
      var action = null;
      try
      {
	buttonID = evt.target.id;
	action = buttonID.substring(buttonID.indexOf("Button") + 6, buttonID.indexOf("Id"));
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

      for (var i = 0; i < me.powerTabNumberNodes; i++)
      {
	var checkBox = document.getElementById("experiment-powerCheckBox" + i);
	if (checkBox.checked && !checkBox.disabled)
	  selectedNodes.push(checkBox.getAttribute("nodeid"));
      }
    }

    if (selectedNodes.length > 0)
    {
      me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
      me.setDisablePowerControls(true);

      var requestPage = me.experimentPowerURL + "?action=" + action + "&numbernodes=" + selectedNodes.length + "&node0=" + selectedNodes[0];
      for (var i = 1; i < selectedNodes.length; i++)
	requestPage += "&node" + i + "=" + selectedNodes[i];

      me.powerTabXmlHttp3 = new XMLHttpRequest();
      me.powerTabXmlHttp3.onreadystatechange = me.powerTabHandlePowerReply;
      me.powerTabXmlHttp3.open("GET", requestPage, true);
      me.powerTabXmlHttp3.send(null);    
    }
  };

  this.powerTabHandlePowerReply = function powerTabHandlePowerReply()
  {
    if (me.powerTabXmlHttp3.readyState == 4)
    {
      if (me.powerTabXmlHttp3.status == 200)
      {
	var xmlDoc = me.powerTabXmlHttp3.responseXML;
	var nodes = xmlDoc.getElementsByTagName("experiments")[0].getElementsByTagName("node");


	for (var i = 0; i < nodes.length; i++)
	{
	  var nodeID = auxiliary.hen.getAttributeValue(nodes[i], "id");
	  var nodeStatus = auxiliary.hen.getAttributeValue(nodes[i], "status");
	  var label = document.getElementById("experiment-powerLabel" + nodeID);
	  label.innerHTML = nodeStatus;
	}

	me.setDisablePowerControls(false);
	me.hideLoadingDiv();

	// Clear all the checkboxes
	for (var i = 0; i < me.powerTabNumberNodes; i++)
	{
	  document.getElementById("experiment-powerCheckBox" + i).checked = false;
	}
      }
    }
  };

  this.toggleTabs = function toggleTabs(evt)
  {
    // When the experiment tab is first shown, the init function calls toggleTabs directly, rather 
    // than by a mouse click as done subsequently
    if (typeof(evt) == "string")
      tab = document.getElementById(evt);
    else
      tab = evt.target;

    if (tab.getAttribute("drawn") == "false")
    {
      var initFunction = me["init" + tab.getAttribute("tabname") + "Tab"];
      initFunction();
      tab.setAttribute("drawn", "true");
    }

    // Tab is currently inactive, activate it
    if (tab.getAttribute("class") == "experimentTab")
    {
      var oldActiveTab = document.getElementById(me.currentActiveCanvasTab);
      oldActiveTab.setAttribute("class", "experimentTab");
      tab.setAttribute("class", "experimentTab activeTab");
      me.currentActiveCanvasTab = tab.id;

      for (var i = 0; i < me.canvasTabDivs.length; i++)
      {
	var tabID = tab.id.substring(0, tab.id.lastIndexOf('TabId'));
	var divID = me.canvasTabDivs[i].id.substring(0, me.canvasTabDivs[i].id.lastIndexOf('TabDivId'));
	if (tabID == divID)
	  me.canvasTabDivs[i].style.visibility = "visible";
	else
	  me.canvasTabDivs[i].style.visibility = "hidden";
      }
    }
  };

  this.handleHistoryReply = function handleHistoryReply()
  {
    if (me.experimentHistoryXmlHttp.readyState == 4)
    {
      if (me.experimentHistoryXmlHttp.status == 200)
      {
	var xmlDoc = me.experimentHistoryXmlHttp.responseXML;
	var experiments = xmlDoc.getElementsByTagName("experiments")[0].getElementsByTagName("experiment");

	// Create the table on the experiment div along with its title
	var historyDiv = document.getElementById("experimentHistoryDivId");
	var historyTable = createTitleTable("Experiment History");
	historyDiv.appendChild(historyTable);

	var table = document.createElement("table");
	table.setAttribute("class", "experiment-historytable");
	table.setAttribute("width", me.HISTORY_DIV_WIDTH);
	historyDiv.appendChild(table);

	var headingsRow = document.createElement("tr");
	headingsRow.setAttribute("class", "experiment-row");
	table.appendChild(headingsRow);

	var headingCell = document.createElement("td");
	headingCell.setAttribute("class", "experiment-cell");
	headingCell.setAttribute("align", "center");
	headingsRow.appendChild(headingCell);
	headingLabel = document.createElement("label");
	headingLabel.setAttribute("class", "experiment-boldlabel");
	headingCell.appendChild(headingLabel);
	headingLabel.appendChild(document.createTextNode("experiment id"));

	headingCell = document.createElement("td");
	headingCell.setAttribute("class", "experiment-cell");
	headingCell.setAttribute("align", "center");
	headingsRow.appendChild(headingCell);
	headingLabel = document.createElement("label");
	headingLabel.setAttribute("class", "experiment-boldlabel");
	headingCell.appendChild(headingLabel);
	headingLabel.appendChild(document.createTextNode("owner"));

	headingCell = document.createElement("td");
	headingCell.setAttribute("class", "experiment-cell");
	headingCell.setAttribute("align", "center");
	headingsRow.appendChild(headingCell);
	headingLabel = document.createElement("label");
	headingLabel.setAttribute("class", "experiment-boldlabel");
	headingCell.appendChild(headingLabel);
	headingLabel.appendChild(document.createTextNode("start date"));

	headingCell = document.createElement("td");
	headingCell.setAttribute("class", "experiment-cell");
	headingCell.setAttribute("align", "center");
	headingsRow.appendChild(headingCell);
	headingLabel = document.createElement("label");
	headingLabel.setAttribute("class", "experiment-boldlabel");
	headingCell.appendChild(headingLabel);
	headingLabel.appendChild(document.createTextNode("end date"));

	headingCell = document.createElement("td");
	headingCell.setAttribute("class", "experiment-cell");
	headingCell.setAttribute("align", "center");
	headingsRow.appendChild(headingCell);
	headingLabel = document.createElement("label");
	headingLabel.setAttribute("class", "experiment-boldlabel");
	headingCell.appendChild(headingLabel);
	headingLabel.appendChild(document.createTextNode("nodes"));

	for (var i = 0; i < experiments.length; i++)
	{
	  var experimentID = auxiliary.hen.getAttributeValue(experiments[i], "id");
	  var startDate = auxiliary.hen.getAttributeValue(experiments[i], "startdate");
	  var endDate = auxiliary.hen.getAttributeValue(experiments[i], "enddate");
	  var owner = auxiliary.hen.getAttributeValue(experiments[i], "owner");

	  // Nodes drop down box
	  var select = document.createElement("select");
	  select.setAttribute("id", "experiment-typeSelectBox" + i + "Id");
	  select.setAttribute("class", "experiment-simpledropdowninputform");
	  select.style.width = "90px";

	  var nodes = experiments[i].getElementsByTagName("node");
	  select.options[0] = new Option("please select...", "please select...")
	  for (var j = 0; j < nodes.length; j++)
	  {
	    nodeID = auxiliary.hen.getAttributeValue(nodes[j], "id");
	    select.options[j + 1] = new Option(nodeID, nodeID);
	  }
	  select.onchange = me.displayNodeLogs;

	  var row = document.createElement("tr");
	  row.setAttribute("class", "experiment-row");
	  table.appendChild(row);

	  var cell = document.createElement("td");
	  cell.setAttribute("class", "experiment-cell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  var label = document.createElement("label");
	  label.setAttribute("class", "experiment-normallabel");
	  cell.appendChild(label);
	  label.appendChild(document.createTextNode(experimentID));

	  cell = document.createElement("td");
	  cell.setAttribute("class", "experiment-cell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  label = document.createElement("label");
	  label.setAttribute("class", "experiment-normallabel");
	  cell.appendChild(label);
	  label.appendChild(document.createTextNode(owner));

	  cell = document.createElement("td");
	  cell.setAttribute("class", "experiment-cell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  label = document.createElement("label");
	  label.setAttribute("class", "experiment-normallabel");
	  cell.appendChild(label);
	  label.appendChild(document.createTextNode(startDate));

	  cell = document.createElement("td");
	  cell.setAttribute("class", "experiment-cell");
	  cell.setAttribute("align", "center");
	  row.appendChild(cell);
	  label = document.createElement("label");
	  label.setAttribute("class", "experiment-normallabel");
	  cell.appendChild(label);
	  label.appendChild(document.createTextNode(endDate));

	  // Append the already-created drop-down box
	  cell = document.createElement("td");
	  cell.setAttribute("class", "experiment-cell");
	  cell.setAttribute("align", "center");
	  cell.appendChild(select);
	  row.appendChild(cell);
	}
      }
    }
  };

  this.displayNodeLogs = function displayNodeLogs(evt)
  {
    var nodeID = evt.target.value;

    if (nodeID == "please select...")
      return;

    var requestPage = me.experimentLogURL + "?action=getlogsbyelement&elementid=" + nodeID;
    me.logRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleLogReply);
    me.logRequest.send();
  };

  this.handleLogReply = function handleLogReply()
  {
    if (me.logRequest.getReadyState() == 4)
    {
      if (me.logRequest.getStatus() == 200)
      {
	var xmlDoc = me.logRequest.getResponseXML();
	var logEntries = xmlDoc.getElementsByTagName("experiments")[0].getElementsByTagName("logentry");

	var outputString = new String();
	for (var i = 0; i < logEntries.length; i++)
	{
	  var date = auxiliary.hen.getAttributeValue(logEntries[i], "date");
	  var time = auxiliary.hen.getAttributeValue(logEntries[i], "time");
	  var author = auxiliary.hen.getAttributeValue(logEntries[i], "author");
	  var description = logEntries[i].getElementsByTagName("description")[0].firstChild.nodeValue;
	  
	  outputString += "\ndate:" + date + " time:" + time + " author:" + author + " affected elements:";
	  var nodes = logEntries[i].getElementsByTagName("element");
	  for (var j = 0; j < nodes.length; j++)
	  {
	    var elementID = auxiliary.hen.getAttributeValue(nodes[j], "id");
	    outputString += elementID + " ";
	  }
	  outputString += "description:" + description;
	}
	alert(outputString);
      }
    }
  };

  var createTitleTable = function createTitleTable(title)
  {
    var titleTable = document.createElement("table");
    titleTable.setAttribute("width", me.CANVAS_WIDTH);

    var spacerRow = document.createElement("tr");
    titleTable.appendChild(spacerRow);
    var spacerCell = document.createElement("td");
    spacerCell.setAttribute("align", "center");
    spacerRow.appendChild(spacerCell);
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("height", "10");
    spacerCell.appendChild(img);

    var titleTableRow = document.createElement("tr");
    titleTable.appendChild(titleTableRow);
    var titleTableCell = document.createElement("td");
    titleTableCell.setAttribute("align", "center");
    titleTableRow.appendChild(titleTableCell);
    var titleTableLabel = document.createElement("label");
    titleTableCell.appendChild(titleTableLabel);
    titleTableLabel.setAttribute("class", "experiment-tabletitlelabel");
    titleTableLabel.appendChild(document.createTextNode(title));

    var spacerRow = document.createElement("tr");
    titleTable.appendChild(spacerRow);
    var spacerCell = document.createElement("td");
    spacerCell.setAttribute("align", "center");
    spacerRow.appendChild(spacerCell);
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("height", "10");
    spacerCell.appendChild(img);

    return titleTable;
  };


  this.createMainDiv = function createMainDiv()
  {
    me.mainNameDiv = document.createElement("div");
    me.mainNameDiv = ("id", "VLANs");
    me.mainNameDiv.appendChild(document.createTextNode("VLANs"));


    me.mainDiv = document.createElement("div");
    me.mainDiv.setAttribute("id", "experimentTabMainDiv");
    return me.mainDiv;
  };

  this.getNodes = function getNodes() {
    me.nodeXHR = new XMLHttpRequest();
    me.nodeXHR.onreadystatechange = me.handleNodeListXHRReply;
    me.nodeXHR.open("GET","/cgi-bin/gui/components/experiment/getnodescgi.py",true);
    me.nodeXHR.send(null);
  };
  
  this.handleNodeListXHRReply = function handleNodeListXHRReply() {
    
    if (me.nodeXHR.readyState == 4) 
    { 
      if (me.nodeXHR.status == 200) 
      {
        var xmlDoc = me.nodeXHR.responseXML;
	var node = xmlDoc.getElementsByTagName("nodes")[0];
        var children = node.childNodes;
	var nodeOptions = new Array();
        for (var i = 0; i < children.length; i++) 
	{
	  if (children[i].nodeType == 1) 
	  {
	    if (children[i].getAttribute("id").match(/computer/)) 
	    {
	      // matches on the computer type nodes
	      nodeOptions.push(children[i].getAttribute("id"));
	    }
	  }
        }
         // populate the drop-down box with available nodes
        //var select = top.document.getElementById("nodeNameDropdownSelectName"); 
        var form = document.getElementById("nodeNameDropdownFormId"); 
        var select = form.firstChild;
        for (var n = 0; n < nodeOptions.length; n++)
        {
          var option = document.createElement("option");
          select.appendChild(option);
          option.setAttribute("value", nodeOptions[n]);
          option.appendChild(document.createTextNode(nodeOptions[n]));
        }
        document.getElementById("experiment-createNodeButtonId").style.visibility = "visible";
      }
    }
  }

  this.doExperimentLoadSelect = function doExperimentLoadSelect() 
  {
    var value = me.configLoadSelectName.options[me.configLoadSelectName.selectedIndex].value;
    window.experimentTabSVGCanvas.doFileLoadRequest(value);
  };



  this.doNodeNameDropdownSelect = function doNodeNameDropdownSelect() 
  {
    document.getElementById("experiment-createNodeButtonId").style.visibility = "hidden";
    var value = me.nodeNameDropdownSelectName.options[me.nodeNameDropdownSelectName.selectedIndex].value;
    window.experimentTabSVGCanvas.doRequest(value);
  };



  // greys out inapplicable areas of the form
  this.doChangeMenu = function doChangeMenu() 
  {
    var value = me.nodeTypesName.options[me.nodeTypesName.selectedIndex].value;
    switch(value) 
    {
      case "node":
        document.getElementById("edgeDivId").style.display = "none";
        document.getElementById("nodeInfoDivId").style.display = "block";
        break;
      case "edge":
        document.getElementById("nodeInfoDivId").style.display = "none";
        document.getElementById("edgeDivId").style.display = "block";
        break;
      default:
        alert("no such option!");
    }
  };
  
  
  
  // requests for the available interfaces asynchronously
  this.getNodeInterfaceCount = function getNodeInterfaceCount(value) 
  {
    me.ifacexhr = new XMLHttpRequest();
    me.ifacexhr.onreadystatechange = me.handleIfaceXHRReply;
    me.ifacexhr.open("GET", "/cgi-bin/gui/components/experiment/vlancgi.py?id=" + value, true);
    me.ifacexhr.send(null);
  };
  
  
  
  this.handleIfaceXHRReply = function handleIfaceXHRReply() 
  {
    if (me.ifacexhr.readyState == 4) 
    {
      if (me.ifacexhr.status == 200) 
      {
        var xmlDoc = me.ifacexhr.responseXML;
        var requestedId = xmlDoc.getElementsByTagName("id");
        var interfaceTags = xmlDoc.getElementsByTagName("interface");

        var selectNames = new Array("startNodeIntId", "endNodeIntId");
        for (var j = 0; j < selectNames.length; j++) 
        {
          var selectBox = document.getElementById(selectNames[j]);
          if (selectBox.selectedIndex < 0) // initial
          {
            for (var i = 0; i < interfaceTags.length; i++) 
            {
              selectBox.options[selectBox.options.length] = new Option("interface" + i, "interface" + i);
            }
          } 
          else 
          {
            if (selectBox.options[selectBox.selectedIndex].value == requestedId) 
            {
              selectBox.options.length = 0;       // clear drop-box
              for (var i = 0; i < interfaceTags.length; i++) 
              {
                selectBox.options[selectBox.options.length] = new Option("interface" + i, "interface" + i);
              }
            }
          }
        }
      } // if (me.ifacexhr.status == 200)
    }
  };



  this.doStartNodeIDNameDropdownSelect = function doStartNodeIDNameDropdownSelect() 
  {
    me.getNodeInterfaceCount(me.startNodeIDName.value);
  };
  
  
  
  this.doEndNodeIDNameDropdownSelect = function doEndNodeIDNameDropdownSelect() 
  {
    me.getNodeInterfaceCount(me.endNodeIDName.value);
  };


  this.doRemoveConfig = function doRemoveConfig() 
  {
    var value = me.configLoadSelectName.options[me.configLoadSelectName.selectedIndex].value;

    me.removeConfigXhr = new XMLHttpRequest();
    me.removeConfigXhr.onreadystatechange = me.handleRemoveConfigXHRReply;
    me.removeConfigXhr.open("GET", "/cgi-bin/gui/components/experiment/deleteconfigcgi.py?id=" + value, true);
    me.removeConfigXhr.send(null);

    me.doRefreshConfigFileList();
  };



  this.handleRemoveConfigXHRReply = function handleRemoveConfigXHRReply() 
  {
    if (me.removeConfigXhr.readyState == 4) 
    {
      if (me.removeConfigXhr.status == 200) 
      {
        // refresh when the file is deleted
        me.doRefreshConfigFileList();
      }
    }
  };
  
  
  
  this.doRefreshConfigFileList = function doRefreshConfigFileList() 
  {
    me.refreshConfigFileListXhr = new XMLHttpRequest();
    me.refreshConfigFileListXhr.onreadystatechange = me.handleRefreshConfigFileListXhrReply;
    me.refreshConfigFileListXhr.open("GET", "/cgi-bin/gui/components/experiment/refreshconfigcgi.py", true);
    me.refreshConfigFileListXhr.send(null);

    setTimeout(me.doRefreshConfigFileList, me.REFRESH_LIST_TIMEOUT_MILISECONDS);
  };



  this.handleRefreshConfigFileListXhrReply = function handleRefreshConfigFileListXhrReply() 
  {
    if (me.refreshConfigFileListXhr.readyState == 4) 
    {
      if (me.refreshConfigFileListXhr.status == 200) 
      {
        var xmlDoc = me.refreshConfigFileListXhr.responseXML;
        var experiment = xmlDoc.getElementsByTagName("experiment");
        var selectBox = document.getElementById("configLoadSelectId");
        // clear the select box
        selectBox.options.length = 0;
        for (var i = 0; i < experiment.length; i++) 
        {
          var expr = experiment[i].getAttribute("id");
          selectBox.options[i] = new Option(expr, expr);
        }
      }
    }
  };

  // Must set up these references so that canvas.js will have access to functions
  // in this class
  window.getNodeInterfaceCount = me.getNodeInterfaceCount;  
  window.doRefreshConfigFileList = me.doRefreshConfigFileList;
  window.doStartNodeIDNameDropdownSelect = me.doStartNodeIDNameDropdownSelect;

} // end class ExperimentTab

// Set up inheritance
components.experiment.experiment.ExperimentTab.prototype = new auxiliary.hen.Tab();
