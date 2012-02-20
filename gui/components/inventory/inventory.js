/** 
 * @fileoverview  Displays and manages the "Inventory" tab of the GUI
 * @version 0.1 
 */
Namespace("components.inventory.inventory");
Import("auxiliary.hen", ".", "/");
Import("auxiliary.draw", ".", "/");

/**
 * Constructs a new components.inventory.inventory.InventoryTab object.
 * @class InventoryTab is a subclass of auxiliary.hen.Tab
 * @constructor
 * @return A new InventoryTab object
 */
components.inventory.inventory.InventoryTab = function()
{
  // Necessary to keep reference to 'this' for event handlers 
  var me = this;
  // The x start position of the control div
  this.X_CONTROL_PANEL_START_POSITION = 10;
  // The y start position of the control div
  this.Y_CONTROL_PANEL_START_POSITION = 45;
  // The width of the control div
  this.CONTROL_PANEL_WIDTH = 160;
  // The height of the control div
  this.CONTROL_PANEL_HEIGHT = 300;
  // The horizontal space in pixels between the control panel and the canvas div
  this.CONTROL_PANEL_SPACER = 10;
  // The vertical distance between the control and legend panels
  this.PANELS_SPACER = 10;
  // The y start position of the legend div
  this.Y_LEGEND_PANEL_START_POSITION = this.Y_CONTROL_PANEL_START_POSITION + this.CONTROL_PANEL_HEIGHT + this.PANELS_SPACER;
  // The height of the legend div
  this.LEGEND_PANEL_HEIGHT = 170;
  // The x position of the canvas div
  this.CANVAS_X_POSITION = this.X_CONTROL_PANEL_START_POSITION + this.CONTROL_PANEL_WIDTH + this.CONTROL_PANEL_SPACER;
  // The y position of the canvas div
  this.CANVAS_Y_POSITION = this.Y_CONTROL_PANEL_START_POSITION;
  // The width of the canvas div
  this.CANVAS_WIDTH = 800;
  // The x position of the pop up div
  this.POP_UP_X_POSITION = 400;
  // The y position of the pop up div
  this.POP_UP_Y_POSITION = 200;
  // The width of the pop up div
  this.POP_UP_WIDTH = 160;
  // The height of the pop up div
  this.POP_UP_HEIGHT = 90;
  // The tab's name
  this.tabLabel = "Inventory";
  // Testbed managers and users can see this tab
  this.allowedGroups.push("henmanager");
  this.allowedGroups.push("henuser");
  // The asynchronous request object used to retrieve the element types currently in the testbed
  this.getTypesXmlHttp = null;
  // The asynchronous request object used to retrieve a brief description of elements of one type
  this.getTypeDescriptionXmlHttp = null;
  // The asynchronous request object used to retrieve an element's full description file
  this.getElementFullInfoXmlHttp = null;
  // The asynchronous request object used to retrieve a brief description of all elements in the testbed
  this.getAllElementsXmlHttp = null;
  // The asynchronous request object used to retrieve all the types that can be added to the testbed
  this.getSupportedTypesXmlHttp = null;
  // The asynchronous request object used to retrieve all the ids of elements currently in the testbed
  this.getAllElementIDsXmlHttp = null;
  // The asynchronous request object used to retrieve all editable information for a particular element
  this.getElementEditInfoXmlHttp = null;
  // The asynchronous request object used to retrieve all the permissible statuses for a particular element type
  this.getTypeStatusesXmlHttp = null;
  // The asynchronous request object used to retrieve orphan mac addresses
  this.getOrphansXmlHttp = null;
  //  The asynchronous request object used to retrieve all the node types supported by the testbed
  this.getNodeTypesXmlHttp = null;
  // Asynchronous request object used to add, edit and delete an element in the testbed
  this.addEditDeleteElementXmlHttpRequest = null;
  // Asynchronous request object used to request information to populate an element's select boxes with
  this.populateSelectBoxesRequest = null;
  // Asynchronous request object used to request information to populate an element's vendor and model select boxes with
  this.populateVendorModelSelectBoxesRequest = null;
  // The URL to the cgi back-end script that gives inventory information
  this.inventoryURL = "/cgi-bin/gui/components/inventory/inventorycgi.py";
  // The background color of the rows in the inventory canvas
  this.statusColors = new Array();
  this.statusColors["operational"] = "#FFFFFF";
  this.statusColors["maintenance"] = "#CCCCCC";
  this.statusColors["retired"] = "#999999";
  this.statusColors["dead"] = "#666666";
  // Used to pop a floating div with an input form
  this.floatingInputDiv = null;
  // Used to create input controls
  this.formHelper = new auxiliary.draw.FormHelper();
  // Used to create divs/tables
  this.drawHelper = new auxiliary.draw.DrawHelper();
  // The class for select boxes in the edit/add canvas
  this.selectBoxClass = "inventory-simpledropdowninputform";
  // The class for text boxes in the edit/add canvas
  this.textBoxClass = "inventory-simpletextinputform";
  // The class for buttons in the edit/add canvas
  this.buttonClass = "inventory-simplebuttoninputform";
  // The class for text areas in the edit/add canvas
  this.textAreaClass = "inventory-simpletextareainputform";
  // Used to keep track of which box to populate status replies into
  this.activeStatusSelectBoxID = null;
  // Used to keep track of how many http requests are outstanding
  this.outstandingPopulateRequests = null;
  // Used to keep track of how many init http requests are outstanding
  this.outstandingInitRequests = null;
  // Used to keep track of the currently selected element id
  this.selectedElementID = null;
  // Used to keep a reference to the pop up input div
  var popUpDiv = null;
  // The x position of the loading animated div
  var LOADING_DIV_X_POSITION = 100;
  // The y position of the loading animated div
  var LOADING_DIV_Y_POSITION = 200;
  // Used to keep track of free ports/units on specific power switches, serial servers and racks
  var unassignedPorts = null;
  // Used to keep track of the testbed's supported hardware
  var supportedHardware = null;
  // Used to keep track of all the input fields for each type of element
  var formFields = new Array();
  
  /**
   * Initializes the tab by drawing the control and legend panels and sending asynchronous requests to 
   * populate the necessary select boxes.
   */
  this.initTab = function initTab()
  {
    me.outstandingInitRequests = 0;
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);

    // **********************************************
    // ******** CONTROL PANEL ***********************
    // **********************************************
    var controlPanelDiv = document.createElement("div");
    me.tabMainDiv.appendChild(controlPanelDiv);
    controlPanelDiv.setAttribute("id", "inventory-controlpaneldivid");
    controlPanelDiv.setAttribute("class", "inventory-controlpaneldiv");
    controlPanelDiv.setAttribute("align", "center");
    controlPanelDiv.style.top = me.Y_CONTROL_PANEL_START_POSITION;
    controlPanelDiv.style.left = me.X_CONTROL_PANEL_START_POSITION;
    controlPanelDiv.style.width = me.CONTROL_PANEL_WIDTH;

    // Create table used for layout
    var table = document.createElement("table");
    table.setAttribute("class", "inventory-layouttable");
    table.setAttribute("width", me.CONTROL_PANEL_WIDTH);
    controlPanelDiv.appendChild(table);
	
    // Create control panel title
    var row = document.createElement("tr");
    row.setAttribute("class", "inventory-row");
    table.appendChild(row);
    var cell = document.createElement("td");
    cell.setAttribute("class", "inventory-layoutcell");
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = document.createElement("label");
    label.setAttribute("class", "inventory-boldlabel");
    label.appendChild(document.createTextNode("Control Panel"));
    cell.appendChild(label);

    // Create view inventory subpanel
    var row = document.createElement("tr");
    row.setAttribute("class", "inventory-row");
    table.appendChild(row);
    var cell = document.createElement("td");
    cell.setAttribute("class", "inventory-layoutcell");
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var viewInventoryPanelDiv = document.createElement("div");
    cell.appendChild(viewInventoryPanelDiv);
    viewInventoryPanelDiv.setAttribute("class", "inventory-controlpanelframingdiv");
    viewInventoryPanelDiv.style.width = me.CONTROL_PANEL_WIDTH - 20;
    var label = document.createElement("label");
    label.setAttribute("class", "inventory-boldlabel");
    viewInventoryPanelDiv.appendChild(label);
    label.appendChild(document.createTextNode("View Inventory"));

    // Type select drop down box
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("inventory-typeselectboxid",  me.selectBoxClass, options, me.viewElements);
    viewInventoryPanelDiv.appendChild(selectBox);
    
    // Create add/edit/delete inventory subpanels only if the user is a manager
    if (me.user.isManager())
    {
      // Create add inventory subpanel
      var row = document.createElement("tr");
      row.setAttribute("class", "inventory-row");
      table.appendChild(row);
      var cell = document.createElement("td");
      cell.setAttribute("class", "inventory-layoutcell");
      cell.setAttribute("align", "center");
      row.appendChild(cell);
      var addInventoryPanelDiv = document.createElement("div");
      cell.appendChild(addInventoryPanelDiv);
      addInventoryPanelDiv.setAttribute("class", "inventory-controlpanelframingdiv");
      addInventoryPanelDiv.style.width = me.CONTROL_PANEL_WIDTH - 20;
      var label = document.createElement("label");
      label.setAttribute("class", "inventory-boldlabel");
      addInventoryPanelDiv.appendChild(label);
      label.appendChild(document.createTextNode("Add Inventory"));
      var options = new Array("please wait...");
      var selectBox = me.formHelper.createSelectBox("inventory-typeselectboxaddid",  me.selectBoxClass, options, me.addElement);
      addInventoryPanelDiv.appendChild(selectBox);
      var p = document.createElement("p");
      addInventoryPanelDiv.appendChild(p);
      var options = new Array("please wait...");
      var selectBox = me.formHelper.createSelectBox("inventory-orphanselectboxaddid",  me.selectBoxClass, options, me.addOrphanElement);
      p.appendChild(selectBox);

      // Create edit inventory subpanel
      var row = document.createElement("tr");
      row.setAttribute("class", "inventory-row");
      table.appendChild(row);
      var cell = document.createElement("td");
      cell.setAttribute("class", "inventory-layoutcell");
      cell.setAttribute("align", "center");
      row.appendChild(cell);
      var editInventoryPanelDiv = document.createElement("div");
      cell.appendChild(editInventoryPanelDiv);
      editInventoryPanelDiv.setAttribute("class", "inventory-controlpanelframingdiv");
      editInventoryPanelDiv.style.width = me.CONTROL_PANEL_WIDTH - 20;
      var label = document.createElement("label");
      label.setAttribute("class", "inventory-boldlabel");
      editInventoryPanelDiv.appendChild(label);
      label.appendChild(document.createTextNode("Edit Inventory"));
      var options = new Array("please wait...");
      var selectBox = me.formHelper.createSelectBox("inventory-typeselectboxeditid", me.selectBoxClass, options, me.editBoxHandler);
      editInventoryPanelDiv.appendChild(selectBox);

      // Create delete inventory subpanel
      var row = document.createElement("tr");
      row.setAttribute("class", "inventory-row");
      table.appendChild(row);
      var cell = document.createElement("td");
      cell.setAttribute("class", "inventory-layoutcell");
      cell.setAttribute("align", "center");
      row.appendChild(cell);
      var deleteInventoryPanelDiv = document.createElement("div");
      cell.appendChild(deleteInventoryPanelDiv);
      deleteInventoryPanelDiv.setAttribute("class", "inventory-controlpanelframingdiv");
      deleteInventoryPanelDiv.style.width = me.CONTROL_PANEL_WIDTH - 20;
      var label = document.createElement("label");
      label.setAttribute("class", "inventory-boldlabel");
      deleteInventoryPanelDiv.appendChild(label);
      label.appendChild(document.createTextNode("Delete Inventory"));
      var options = new Array("please wait...");
      var selectBox = me.formHelper.createSelectBox("inventory-typeselectboxdeleteid", me.selectBoxClass, options, me.deleteElement);
      deleteInventoryPanelDiv.appendChild(selectBox);

      me.getSupportedTypesXmlHttp = new XMLHttpRequest();
      var requestPage = me.inventoryURL + "?retrieve=alltypes";
      me.getSupportedTypesXmlHttp.onreadystatechange = me.handleInventoryAllTypesReply;
      me.getSupportedTypesXmlHttp.open("GET", requestPage, true);
      me.getSupportedTypesXmlHttp.send(null);

      me.getAllElementIDsXmlHttp = new XMLHttpRequest();
      var requestPage = me.inventoryURL + "?retrieve=allelements";
      me.getAllElementIDsXmlHttp.onreadystatechange = me.handleInventoryAllElementsReply;
      me.getAllElementIDsXmlHttp.open("GET", requestPage, true);
      me.getAllElementIDsXmlHttp.send(null);

      me.getOrphansXmlHttp = new XMLHttpRequest();
      var requestPage = me.inventoryURL + "?retrieve=orphans";
      me.getOrphansXmlHttp.onreadystatechange = me.handleOrphansReply;
      me.getOrphansXmlHttp.open("GET", requestPage, true);
      me.getOrphansXmlHttp.send(null);

      me.outstandingInitRequests += 3;
    }

    // Spacer row
    var spacerRow = document.createElement("tr");
    table.appendChild(spacerRow);
    var spacerCell = document.createElement("td");
    spacerCell.setAttribute("align", "center");
    spacerRow.appendChild(spacerCell);
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("height", "10");
    spacerCell.appendChild(img);

    // **********************************************
    // ******** LEGEND PANEL ************************
    // **********************************************
    var legendPanelDiv = document.createElement("div");
    me.tabMainDiv.appendChild(legendPanelDiv);
    legendPanelDiv.setAttribute("id", "inventory-legendpaneldivid");
    legendPanelDiv.setAttribute("class", "inventory-legendpaneldiv");
    legendPanelDiv.setAttribute("align", "center");
    legendPanelDiv.style.top = me.Y_LEGEND_PANEL_START_POSITION;
    legendPanelDiv.style.left = me.X_CONTROL_PANEL_START_POSITION;
    legendPanelDiv.style.width = me.CONTROL_PANEL_WIDTH;
    legendPanelDiv.style.height = me.LEGEND_PANEL_HEIGHT;

    var p = document.createElement("p");
    legendPanelDiv.appendChild(p);
    var label = document.createElement("label");
    label.setAttribute("class", "inventory-boldlabel");
    p.appendChild(label);
    label.appendChild(document.createTextNode("Legend"));	

    // Draw the legend rectangles
    for (var status in me.statusColors)
    {
      p = document.createElement("p");
      legendPanelDiv.appendChild(p);
      var div = document.createElement("div");
      div.setAttribute("class", "inventory-legendrectangle");
      div.appendChild(document.createTextNode(status));
      div.style.backgroundColor = me.statusColors[status];
      p.appendChild(div);
    }
	
    // Main inventory canvas
    var style = "position: absolute;" +
                "top: " + me.CANVAS_Y_POSITION + "px;" +
                "left: " + me.CANVAS_X_POSITION + "px;" +
                "width: " + me.CANVAS_WIDTH + "px;" +
	        "border: 1px solid #ccc;";
    var div = document.createElement("div");
    div.setAttribute("style", style);
    div.setAttribute("id", "inventory-canvasid");
    me.tabMainDiv.appendChild(div);

    me.outstandingInitRequests += 1
    me.getTypesXmlHttp = new XMLHttpRequest();
    var requestPage = me.inventoryURL + "?retrieve=types";
    me.getTypesXmlHttp.onreadystatechange = me.handleInventoryReply;
    me.getTypesXmlHttp.open("GET", requestPage, true);
    me.getTypesXmlHttp.send(null);

    me.setDisableControls(true);
  };

  /**
   * Re-enables controls and removes loading animated gif once all initial asynchronous requests have returned
   */
  this.finishInitLoad = function finishInitLoad()
  {
    --me.outstandingInitRequests;
    if (me.outstandingInitRequests == 0)
    {
      me.hideLoadingDiv();
      me.setDisableControls(false);
    }
  };

  /**
   * Onchange event handler for View inventory select box. This method sends an
   * asynchronous request to retrieve a brief description of all elements of the
   * selected type. The request's handler is {@link components.inventory.inventory.InventoryTab#handleInventoryTypeDescriptionReply}
   */
  this.viewElements = function viewElements()
  {
    var selectBox = document.getElementById("inventory-typeselectboxid");
    var selectedNodeType = selectBox.options[selectBox.selectedIndex].value;

    if (selectedNodeType == "select type...")
      return;

    document.getElementById("inventory-typeselectboxeditid").selectedIndex = 0;
    document.getElementById("inventory-typeselectboxaddid").selectedIndex = 0;
    document.getElementById("inventory-orphanselectboxaddid").selectedIndex = 0;

    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.setDisableControls(true);
    me.clearCanvas();
    if (selectedNodeType == "all")
    {
      me.getAllElementsXmlHttp = new XMLHttpRequest();
      var requestPage = me.inventoryURL + "?retrieve=all";
      me.getAllElementsXmlHttp.onreadystatechange = me.handleInventoryAllReply;
      me.getAllElementsXmlHttp.open("GET", requestPage, true);
      me.getAllElementsXmlHttp.send(null);
    }      
    else
    {
      // Retrieve brief description for all elements of the selected type and 
      // display it in a table on the main inventory canvas
      me.getTypeDescriptionXmlHttp = new XMLHttpRequest();
      var requestPage = me.inventoryURL + "?retrieve=typedescription&type=" + selectedNodeType;
      me.getTypeDescriptionXmlHttp.onreadystatechange = me.handleInventoryTypeDescriptionReply;
      me.getTypeDescriptionXmlHttp.open("GET", requestPage, true);
      me.getTypeDescriptionXmlHttp.send(null);
    }
  };

  /**
   * Onchange event handler for Add inventory select box. This method displays the input
   * boxes for the selected element type by creating the method name to call dynamically;
   * The method name is of the form draw[Elementtype]Fields. if such a method does not exist
   * for the selected element type, an alert is shown.
   */
  this.addElement = function addElement()
  {
    me.mode = "add";
    var selectBox = document.getElementById("inventory-typeselectboxaddid");
    var selectedNodeType = selectBox.options[selectBox.selectedIndex].value;

    if (selectedNodeType == "select type...")
      return;
    
    document.getElementById("inventory-typeselectboxeditid").selectedIndex = 0;
    document.getElementById("inventory-orphanselectboxaddid").selectedIndex = 0;      
    me.clearCanvas();

    // Call the appropiate draw fields method dynamically
    me.setDisableControls(true);
    var createFields = me["draw" + selectedNodeType[0].toUpperCase() + selectedNodeType.substring(1) + "Fields"];
    try
    {
      createFields();
    }
    catch (e)
    {
      alert("function not yet implemented for type " + selectedNodeType);
    }
  };

  /**
   * Onclick event handler for add orphan select box. This function pops up a div that
   * asks the user the node type of the orphan selected.
   * @param {Event} evt The onclick event
   */
  this.addOrphanElement = function addOrphanElement(evt)
  {
    var macAddress = evt.target.value;
    if (macAddress == "select orphan...")
      return;
    
    me.clearCanvas();
    document.getElementById("inventory-typeselectboxeditid").selectedIndex = 0;
    document.getElementById("inventory-typeselectboxaddid").selectedIndex = 0;

    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("inventory-orphantypesid", me.selectBoxClass, options, null);

    // Create pop up div
    popUpDiv = new auxiliary.draw.PopUpInput(me.POP_UP_X_POSITION, me.POP_UP_Y_POSITION, "Select Orphan Type",
                                             selectBox, "inventory-floatingInputDivId", me.popOrphanInputSubmit,
                                             me.tabMainDiv, null, macAddress);
    me.visibilityDivs.push(popUpDiv);

    // Show pop up div
    popUpDiv.showPopUp();


    me.getNodeTypesXmlHttp = new XMLHttpRequest();
    var requestPage = me.inventoryURL + "?retrieve=nodetypes";
    me.getNodeTypesXmlHttp.onreadystatechange = me.handleNodeTypesReply;
    me.getNodeTypesXmlHttp.open("GET", requestPage, true);
    me.getNodeTypesXmlHttp.send(null);    
  };

  /**
   * Onchange handler for orphan select box. Pops up a box requesting the user to select
   * the type of orphan to add.
   * @param {Event} evt The onchange event
   */
  this.popOrphanInputSubmit = function popOrphanInputSubmit(evt)
  {
    var selectedNodeType = document.getElementById("inventory-orphantypesid").value;
    var macAddress = popUpDiv.getDataToStore();

    popUpDiv.closePopUp();
    delete popUpDiv;

    me.clearCanvas();
    // Call the appropiate draw fields method dynamically
    var createFields = me["draw" + selectedNodeType[0].toUpperCase() + selectedNodeType.substring(1) + "Fields"];
    try
    {
      createFields();
    }
    catch (e)
    {
      alert("function not yet implemented for type " + selectedNodeType);
      return;
    }
    
    originalSelectedNodeType = selectedNodeType;
    if (selectedNodeType == "kernel" || selectedNodeType == "loader")
      selectedNodeType = "filesystem";

    // Change mac address box to display orphan's mac address and disable it
    var selectBox = document.getElementById("inventory-" + selectedNodeType + "macaddressid");
    selectBox.options.length = 0;
    selectBox[0] = new Option(macAddress, macAddress);
    selectBox.disabled = true;
  };

  /**
   * Onchange event handler for edit element select box.
   * @param {Event} evt The event
   */
  this.editBoxHandler = function editBoxHandler(evt)
  {
    var selectBox = evt.target;
    var elementType = selectBox.value;
    var elementID = selectBox.options[selectBox.selectedIndex].text;

    // Don't allow objects whose id does not contain its type
    if (elementID.indexOf(elementType) == -1)
    {
      alert("the id " + elementID + " does not have the string " + elementType + " in it, ignoring...");
      return;
    }
    

    var value = evt.target.value;
    if (value == "please wait..." || value == "select element...")
      return;
    me.editElement(value);
  };

  /** 
   * This method displays the input boxes for the selected element type by creating the 
   * method name to call dynamically. The method name is of the form drawElementtypeFields
   * @param {String} selectedElementID The element id to edit information for
   */
  this.editElement = function editElement(selectedElementID)
  {
    me.mode = "edit";
    me.selectedElementID = selectedElementID;
    me.clearCanvas();

    document.getElementById("inventory-typeselectboxaddid").selectedIndex = 0;
    document.getElementById("inventory-orphanselectboxaddid").selectedIndex = 0;      

    var elementType = document.getElementById("inventory-typeselectboxeditid").value;

    // Call the appropiate draw fields method dynamically
    me.setDisableControls(true);
    var createFields = me["draw" + elementType[0].toUpperCase() + elementType.substring(1) + "Fields"];
    createFields();

    originalElementType = elementType;
    if (elementType == "kernel" || elementType == "loader")
      elementType = "filesystem";

    var label = document.getElementById("inventory-" + elementType + "MainTitleId");
    label.removeChild(label.firstChild);
    label.appendChild(document.createTextNode("Edit " + originalElementType));
    var button = document.getElementById("inventory-" + elementType + "CreateButtonId");
    button.setAttribute("value", "Edit " + originalElementType);
    button.onclick = me.editElementRequest;

    disableInputs(new Array("inventory-macaddressid", "inventory-infrastructuremacaddressid", "inventory-managementmacaddressid"));
  };

  /**
   * Onchange event handler for Delete inventory select box, pops up a confirm box, then
   * removes the given element from the testbed.
   * @param {Event} evt The onchange event
   */
  this.deleteElement = function deleteElement(evt)
  {
    var selectBox = document.getElementById("inventory-typeselectboxdeleteid");
    var elementID = selectBox.options[selectBox.selectedIndex].text;

    if (elementID != "select element...")
    {
      document.getElementById("inventory-typeselectboxeditid").selectedIndex = 0;
      document.getElementById("inventory-typeselectboxaddid").selectedIndex = 0;
      document.getElementById("inventory-orphanselectboxaddid").selectedIndex = 0;      

      var answer = confirm("Are you sure you want to permanently delete " + elementID + "?");
      if (answer)
      {
	me.setDisableControls(true);
	me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
	var requestPage = me.inventoryURL + "?retrieve=deleteelement&elementid=" + elementID;
	me.addEditDeleteElementXmlHttpRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleAddEditDeleteElementReply);
	me.addEditDeleteElementXmlHttpRequest.send();	  
      }
      else
	document.getElementById("inventory-typeselectboxdeleteid").selectedIndex = 0;
    }      
  };

  /**
   * Draws input fields for an element of type loader by calling 
   * {@link components.inventory.inventory.InventoryTab#drawFilesystemFields}
   */
  this.drawLoaderFields = function drawLoaderFields()
  {
    // Reuse the filesystem fields, modifying a few things
    me.drawFilesystemFields();
    var label = document.getElementById("inventory-filesystemMainTitleId");
    label.removeChild(label.firstChild);
    label.appendChild(document.createTextNode("Add Loader"));
    var cell = document.getElementById("inventory-filesystemUsernameLabelCellId");
    cell.removeChild(cell.firstChild);
    var cell = document.getElementById("inventory-filesystemPasswordLabelCellId");
    cell.removeChild(cell.firstChild);
    var cell = document.getElementById("inventory-filesystemUsernameCellId");
    cell.removeChild(cell.firstChild);
    var cell = document.getElementById("inventory-filesystemPasswordCellId");
    cell.removeChild(cell.firstChild);
    var button = document.getElementById("inventory-filesystemCreateButtonId");
    button.setAttribute("value", "Add Loader");
  };

  /**
   * Draws input fields for an element of type kernel by calling 
   * {@link components.inventory.inventory.InventoryTab#drawFilesystemFields}
   */
  this.drawKernelFields = function drawKernelFields()
  {
    // Reuse the filesystem fields, modifying a few things
    me.drawFilesystemFields();
    var label = document.getElementById("inventory-filesystemMainTitleId");
    label.removeChild(label.firstChild);
    label.appendChild(document.createTextNode("Add Kernel"));
    var cell = document.getElementById("inventory-filesystemUsernameLabelCellId");
    cell.removeChild(cell.firstChild);
    var cell = document.getElementById("inventory-filesystemPasswordLabelCellId");
    cell.removeChild(cell.firstChild);
    var cell = document.getElementById("inventory-filesystemUsernameCellId");
    cell.removeChild(cell.firstChild);
    var cell = document.getElementById("inventory-filesystemPasswordCellId");
    cell.removeChild(cell.firstChild);
    var button = document.getElementById("inventory-filesystemCreateButtonId");
    button.setAttribute("value", "Add Kernel");
  };

  /**
   * Draws input fields for an element of type filesystem; the function sets the submit
   * button's onclick handler to {@link components.inventory.inventory.InventoryTab#addFilesystem}
   */
  this.drawFilesystemFields = function drawFilesystemFields()
  {
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.outstandingPopulateRequests = 1;
    var canvas = document.getElementById("inventory-canvasid");
    var numberColumns = "4";

    var table = me.drawHelper.createLayoutTable();
    table.setAttribute("width", me.CANVAS_WIDTH);
    canvas.appendChild(table);

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("inventory-tabletitlelabel", "Add Filesystem");
    label.setAttribute("id", "inventory-filesystemMainTitleId");
    cell.appendChild(label);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Title for status
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "status"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Status field
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("inventory-statusid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    me.getTypeStatusesXmlHttp = new XMLHttpRequest();
    var requestPage = me.inventoryURL + "?retrieve=statuses&elementtype=filesystem";
    me.getTypeStatusesXmlHttp.onreadystatechange = me.handleStatusesReply;
    me.getTypeStatusesXmlHttp.open("GET", requestPage, true);
    me.getTypeStatusesXmlHttp.send(null);    
    me.activeStatusSelectBoxID = "inventory-statusid";

    // Titles for path, architecture and os type fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "full path"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "architecture"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "OS type"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));

    // Path, architecture and os type fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-pathid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-architectureid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-ostypeid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Titles for version, mustclone and description
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "version"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "must clone"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "description"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));

    // Version, mustclone and description
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-versionid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("yes", "no");
    var selectBox = me.formHelper.createSelectBox("inventory-mustcloneid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-descriptionid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Titles for owner, username and password fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "owner"));
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("id", "inventory-filesystemUsernameLabelCellId");
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "username"));
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("id", "inventory-filesystemPasswordLabelCellId");
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "password"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));

    // Owner, username and password fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please select...", "root", me.user.username, "other...");
    var select = me.formHelper.createSelectBox("inventory-ownerid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "MAC Address");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("id", "inventory-filesystemUsernameCellId");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-usernameid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("id", "inventory-filesystemPasswordCellId");
    row.appendChild(cell);
    var textBox = me.formHelper.createPasswordBox("inventory-passwordid", me.textBoxClass);
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Titles for attribute name, value and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute value"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute list"));

    // Attribute name, value, add button and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeNameId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeValueId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-AddAttributeButtonId", me.buttonClass, "Add attribute", me.addAttribute);
    button.setAttribute("resultTextAreaId", "inventory-AttributeListId");
    button.setAttribute("attributeNameId", "inventory-AttributeNameId");
    button.setAttribute("attributeValueId", "inventory-AttributeValueId");
    cell.appendChild(button);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textArea = me.formHelper.createTextArea("inventory-AttributeListId", me.textAreaClass, "2", "40");
    cell.appendChild(textArea);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("30", numberColumns));

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-filesystemCreateButtonId", me.buttonClass, "Add Filesystem", me.addElementRequest);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("inventory-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button);

    // Create list of all inputs for later use
    formFields["filesystem"] = new Array("status", "path", "architecture", 
					 "ostype", "version", "mustclone", 
					 "description", "owner", "username",
					 "password");
    formFields["kernel"] = new Array("status", "path", "architecture", 
				     "ostype", "version", "mustclone", 
				     "description", "owner");
    formFields["loader"] = new Array("status", "path", "architecture", 
				     "ostype", "version", "mustclone", 
				     "description", "owner");

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

  };

  /**
   * Draws input fields for an element of type rack; The function sets the submit
   * button's onclick handler to {@link components.inventory.inventory.InventoryTab#addRack}
   */
  this.drawRackFields = function drawRackFields()
  {
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.outstandingPopulateRequests = 1;
    var canvas = document.getElementById("inventory-canvasid");
    var numberColumns = "4";

    var table = me.drawHelper.createLayoutTable();
    table.setAttribute("width", me.CANVAS_WIDTH);
    canvas.appendChild(table);

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("inventory-tabletitlelabel", "Add Rack");
    label.setAttribute("id", "inventory-rackMainTitleId");
    cell.appendChild(label);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Title for status
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "status"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Status field
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("inventory-statusid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    me.getTypeStatusesXmlHttp = new XMLHttpRequest();
    var requestPage = me.inventoryURL + "?retrieve=statuses&elementtype=rack";
    me.getTypeStatusesXmlHttp.onreadystatechange = me.handleStatusesReply;
    me.getTypeStatusesXmlHttp.open("GET", requestPage, true);
    me.getTypeStatusesXmlHttp.send(null);    
    me.activeStatusSelectBoxID = "inventory-statusid";

    // Titles for vendor, model, description and building fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "vendor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "model"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "description"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "building"));

    // Vendor, model, description and building fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-vendorid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-modelid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-descriptionid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-buildingid", me.textBoxClass, "malet place");
    cell.appendChild(textBox);

    // Titles for floor, room, rackrow and rowposition fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "floor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "room"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack row"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "row position"));

    // Floor, room, rackrow and rowposition fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-floorid", me.textBoxClass, "4");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-roomid", me.textBoxClass, "4.15");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-rackrowid", me.textBoxClass, "1");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-rowpositionid", me.textBoxClass, "");
    cell.appendChild(textBox);

    // Titles for height, width, depth and # units fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "height(cm)"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "width(cm)"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "depth(cm)"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "# units"));

    // Height, width, depth and # units fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-heightid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-widthid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-depthid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-numberunitsid", me.textBoxClass, "");
    cell.appendChild(textBox);

    // Titles for rear right and left slots
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "# rear left slots"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "# rear right slots"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Rear right and left slots fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("1", "2", "3", "4");
    var selectBox = me.formHelper.createSelectBox("inventory-rearleftslotsid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("1", "2", "3", "4");
    var selectBox = me.formHelper.createSelectBox("inventory-rearrightslotsid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Titles for attribute name, value and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute value"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute list"));

    // Attribute name, value, add button and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeNameId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeValueId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-AddAttributeButtonId", me.buttonClass, "Add attribute", me.addAttribute);
    button.setAttribute("resultTextAreaId", "inventory-AttributeListId");
    button.setAttribute("attributeNameId", "inventory-AttributeNameId");
    button.setAttribute("attributeValueId", "inventory-AttributeValueId");
    cell.appendChild(button);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textArea = me.formHelper.createTextArea("inventory-AttributeListId", me.textAreaClass, "2", "40");
    cell.appendChild(textArea);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("30", numberColumns));

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-rackCreateButtonId", me.buttonClass, "Add Rack", me.addElementRequest);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("inventory-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Create list of all inputs for later use
    formFields["rack"] = new Array("status", "vendor", "model", 
				   "description", "building", "floor", 
				   "room", "rackrow", "height", 
				   "width", "depth", "numberunits",
				   "rearrightslots", "rearleftslots", "rowposition");
  };

  /**
   * Draws input fields for an element of type router
   */
  this.drawRouterFields = function drawRouterFields()
  {
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.outstandingPopulateRequests = 2;
    var canvas = document.getElementById("inventory-canvasid");
    var numberColumns = "4";

    var table = me.drawHelper.createLayoutTable();
    table.setAttribute("width", me.CANVAS_WIDTH);
    canvas.appendChild(table);

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("inventory-tabletitlelabel", "Add Router");
    label.setAttribute("id", "inventory-routerMainTitleId");
    cell.appendChild(label);    

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Title for status
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "status"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "number of ports"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Status field
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("inventory-statusid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-numberportsid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    me.getTypeStatusesXmlHttp = new XMLHttpRequest();
    var requestPage = me.inventoryURL + "?retrieve=statuses&elementtype=router";
    me.getTypeStatusesXmlHttp.onreadystatechange = me.handleStatusesReply;
    me.getTypeStatusesXmlHttp.open("GET", requestPage, true);
    me.getTypeStatusesXmlHttp.send(null);    
    me.activeStatusSelectBoxID = "inventory-statusid";

    // Titles for mac address, vendor, model and infrastructure fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "mac address"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "vendor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "model"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "infrastructure"));

    // Mac address, vendor, model and infrastructure fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please select...", "other...");
    var select = me.formHelper.createSelectBox("inventory-macaddressid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "MAC Address");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-vendorid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-modelid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("yes", "no");
    var selectBox = me.formHelper.createSelectBox("inventory-infrastructureid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);

    // Titles for serial/port, powerswitch/port fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "serial"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "serial port"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch port"));

    // Serial/port, powerswitch/port fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serialid", me.selectBoxClass, options, me.populateSerialPorts);
    select.setAttribute("popuplabel", "Serial");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serialportid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Serial Port");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchid", me.selectBoxClass, options, me.populatePowerPorts);
    select.setAttribute("popuplabel", "Power Switch");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchportid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Power Switch Port");
    cell.appendChild(select);

    // Titles for building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "building"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "floor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "room"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack row #"));

    // Building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-buildingid", me.textBoxClass, "malet place");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-floorid", me.textBoxClass, "4");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-roomid", me.textBoxClass, "4.15");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-rackrowid", me.textBoxClass, "1");
    cell.appendChild(textBox);

    // Titles for rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack start unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack end unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "front/back position"));

    // Rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-racknameid", me.selectBoxClass, options, me.populateRackUnits);
    select.setAttribute("popuplabel", "Rack Name");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackstartunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack Start Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackendunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack End Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("front", "rear", "both");
    var select = me.formHelper.createSelectBox("inventory-nodepositionid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Front/Rear Position");
    cell.appendChild(select);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Titles for attribute name, value and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute value"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute list"));

    // Attribute name, value, add button and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeNameId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeValueId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-AddAttributeButtonId", me.buttonClass, "Add attribute", me.addAttribute);
    button.setAttribute("resultTextAreaId", "inventory-AttributeListId");
    button.setAttribute("attributeNameId", "inventory-AttributeNameId");
    button.setAttribute("attributeValueId", "inventory-AttributeValueId");
    cell.appendChild(button);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textArea = me.formHelper.createTextArea("inventory-AttributeListId", me.textAreaClass, "2", "40");
    cell.appendChild(textArea);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("30", numberColumns));

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-routerCreateButtonId", me.buttonClass, "Add Router", me.addElementRequest);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("inventory-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Create list of all inputs for later use
    formFields["router"] = new Array("status", "macaddress", "vendor",
				     "model", "infrastructure", "serial", 
				     "serialport", "powerswitch", "powerswitchport", 
				     "building", "floor", "room", 
				     "rackrow", "rackname", "rackstartunit", 
				     "rackendunit", "nodeposition", "numberports");

    // Send request for information to populate select boxes with
    var requestPage = me.inventoryURL + "?retrieve=populateselectboxes"
    me.populateSelectBoxesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePopulateSelectBoxesReply);
    me.populateSelectBoxesRequest.send();
  };

  /**
   * Draws input fields for an element of type switch; The function sets the submit
   * button's onclick handler to {@link components.inventory.inventory.InventoryTab#addSwitch}
   */
  this.drawSwitchFields = function drawSwitchFields()
  {
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.outstandingPopulateRequests = 3;
    var canvas = document.getElementById("inventory-canvasid");
    var numberColumns = "4";

    var table = me.drawHelper.createLayoutTable();
    table.setAttribute("width", me.CANVAS_WIDTH);
    canvas.appendChild(table);

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("inventory-tabletitlelabel", "Add Switch");
    label.setAttribute("id", "inventory-switchMainTitleId");
    cell.appendChild(label);    

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Title for status
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "status"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "number of ports"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Status field
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("inventory-statusid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-numberportsid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    me.getTypeStatusesXmlHttp = new XMLHttpRequest();
    var requestPage = me.inventoryURL + "?retrieve=statuses&elementtype=switch";
    me.getTypeStatusesXmlHttp.onreadystatechange = me.handleStatusesReply;
    me.getTypeStatusesXmlHttp.open("GET", requestPage, true);
    me.getTypeStatusesXmlHttp.send(null);    
    me.activeStatusSelectBoxID = "inventory-statusid";

    // Titles for mac address, vendor, model and infrastructure fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "mac address"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "vendor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "model"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "infrastructure"));

    // Mac address, vendor, model and infrastructure fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please select...", "other...");
    var select = me.formHelper.createSelectBox("inventory-macaddressid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "MAC Address");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-vendorid", me.selectBoxClass, options, me.populateModels);
    select.setAttribute("popuplabel", "Vendor");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-modelid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "Model");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("yes", "no");
    var selectBox = me.formHelper.createSelectBox("inventory-infrastructureid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);

    // Titles for serial/port, powerswitch/port fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "serial"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "serial port"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch port"));

    // Serial/port, powerswitch/port fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serialid", me.selectBoxClass, options, me.populateSerialPorts);
    select.setAttribute("popuplabel", "Serial");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serialportid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Serial Port");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchid", me.selectBoxClass, options, me.populatePowerPorts);
    select.setAttribute("popuplabel", "Power Switch");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchportid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Power Switch Port");
    cell.appendChild(select);

    // Titles for building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "building"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "floor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "room"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack row #"));

    // Building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-buildingid", me.textBoxClass, "malet place");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-floorid", me.textBoxClass, "4");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-roomid", me.textBoxClass, "4.15");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-rackrowid", me.textBoxClass, "1");
    cell.appendChild(textBox);

    // Titles for rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack start unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack end unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "front/back position"));

    // Rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-racknameid", me.selectBoxClass, options, me.populateRackUnits);
    select.setAttribute("popuplabel", "Rack Name");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackstartunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack Start Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackendunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack End Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("front", "rear", "both");
    var select = me.formHelper.createSelectBox("inventory-nodepositionid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Front/Rear Position");
    cell.appendChild(select);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Titles for attribute name, value and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute value"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute list"));

    // Attribute name, value, add button and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeNameId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeValueId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-AddAttributeButtonId", me.buttonClass, "Add attribute", me.addAttribute);
    button.setAttribute("resultTextAreaId", "inventory-AttributeListId");
    button.setAttribute("attributeNameId", "inventory-AttributeNameId");
    button.setAttribute("attributeValueId", "inventory-AttributeValueId");
    cell.appendChild(button);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textArea = me.formHelper.createTextArea("inventory-AttributeListId", me.textAreaClass, "2", "40");
    cell.appendChild(textArea);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("30", numberColumns));

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-switchCreateButtonId", me.buttonClass, "Add Switch", me.addElementRequest);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("inventory-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Create list of all inputs for later use
    formFields["switch"] = new Array("status", "macaddress", "vendor",
				     "model", "infrastructure", "serial", 
				     "serialport", "powerswitch", "powerswitchport", 
				     "building", "floor", "room", 
				     "rackrow", "rackname", "rackstartunit", 
				     "rackendunit", "nodeposition", "numberports");

    // Send request for information to populate select boxes with
    var requestPage = me.inventoryURL + "?retrieve=populateselectboxes"
    me.populateSelectBoxesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePopulateSelectBoxesReply);
    me.populateSelectBoxesRequest.send();
    // Send request for information to populate vendor and model select boxes with
    var requestPage = me.inventoryURL + "?retrieve=supportedhardware&elementtype=switch"
    me.populateVendorModelSelectBoxesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePopulateVendorModelSelectBoxesReply);
    me.populateVendorModelSelectBoxesRequest.send();

  };

  /**
   * Draws input fields for an element of type powerswitch; The function sets the submit
   * button's onclick handler to {@link components.inventory.inventory.InventoryTab#addPowerSwitch}
   */
  this.drawPowerswitchFields = function drawPowerswitchFields()
  {
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.outstandingPopulateRequests = 3;
    var canvas = document.getElementById("inventory-canvasid");
    var numberColumns = "4";

    var table = me.drawHelper.createLayoutTable();
    table.setAttribute("width", me.CANVAS_WIDTH);
    canvas.appendChild(table);

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("inventory-tabletitlelabel", "Add Power Switch");
    label.setAttribute("id", "inventory-powerswitchMainTitleId");
    cell.appendChild(label);    

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Title for status
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "status"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "number of ports"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Status field
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("inventory-statusid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-numberportsid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    me.getTypeStatusesXmlHttp = new XMLHttpRequest();
    var requestPage = me.inventoryURL + "?retrieve=statuses&elementtype=powerswitch";
    me.getTypeStatusesXmlHttp.onreadystatechange = me.handleStatusesReply;
    me.getTypeStatusesXmlHttp.open("GET", requestPage, true);
    me.getTypeStatusesXmlHttp.send(null);    
    me.activeStatusSelectBoxID = "inventory-statusid";

    // Titles for mac address, vendor and model fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "mac address"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "vendor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "model"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));

    // Mac address, vendor and model fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please select...", "other...");
    var select = me.formHelper.createSelectBox("inventory-macaddressid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "MAC Address");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-vendorid", me.selectBoxClass, options, me.populateModels);
    select.setAttribute("popuplabel", "Vendor");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.setAttribute("colspan", "2");
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-modelid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "Model");
    cell.appendChild(select);

    // Titles for serial/port, username and password fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "serial"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "serial port"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "username"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "password"));

    // serial/port, username and password fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serialid", me.selectBoxClass, options, me.populateSerialPorts);
    select.setAttribute("popuplabel", "Serial");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serialportid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Serial Port");
    cell.appendChild(select);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-usernameid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createPasswordBox("inventory-passwordid", me.textBoxClass);
    cell.appendChild(textBox);

    // Titles for building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "building"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "floor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "room"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack row #"));

    // Building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-buildingid", me.textBoxClass, "malet place");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-floorid", me.textBoxClass, "4");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-roomid", me.textBoxClass, "4.15");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-rackrowid", me.textBoxClass, "1");
    cell.appendChild(textBox);

    // Titles for rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack start unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack end unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "front/back position"));

    // Rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-racknameid", me.selectBoxClass, options, me.populateRackUnits);
    select.setAttribute("popuplabel", "Rack Name");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackstartunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack Start Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackendunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack End Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("front", "rear", "both");
    var select = me.formHelper.createSelectBox("inventory-nodepositionid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Front/Rear Position");
    cell.appendChild(select);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Titles for attribute name, value and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute value"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute list"));

    // Attribute name, value, add button and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeNameId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeValueId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-AddAttributeButtonId", me.buttonClass, "Add attribute", me.addAttribute);
    button.setAttribute("resultTextAreaId", "inventory-AttributeListId");
    button.setAttribute("attributeNameId", "inventory-AttributeNameId");
    button.setAttribute("attributeValueId", "inventory-AttributeValueId");
    cell.appendChild(button);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textArea = me.formHelper.createTextArea("inventory-AttributeListId", me.textAreaClass, "2", "40");
    cell.appendChild(textArea);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("30", numberColumns));

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-powerswitchCreateButtonId", me.buttonClass, "Add Powerswitch", me.addElementRequest);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("inventory-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button); 

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Create list of all inputs for later use
    formFields["powerswitch"] = new Array("status", "macaddress", "vendor",
					  "model", "serial", "serialport", 
					  "username", "password", "building", 
					  "floor", "room", "rackrow", 
					  "rackname", "rackstartunit", "rackendunit", 
					  "nodeposition", "numberports");

    // Send request for information to populate select boxes with
    var requestPage = me.inventoryURL + "?retrieve=populateselectboxes"
    me.populateSelectBoxesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePopulateSelectBoxesReply);
    me.populateSelectBoxesRequest.send();
    // Send request for information to populate vendor and model select boxes with
    var requestPage = me.inventoryURL + "?retrieve=supportedhardware&elementtype=powerswitch"
    me.populateVendorModelSelectBoxesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePopulateVendorModelSelectBoxesReply);
    me.populateVendorModelSelectBoxesRequest.send();
  };

  /**
   * Draws input fields for an element of type serial; The function sets the submit
   * button's onclick handler to {@link components.inventory.inventory.InventoryTab#addSerial}
   */
  this.drawSerialFields = function drawSerialFields()
  {
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.outstandingPopulateRequests = 3;
    var canvas = document.getElementById("inventory-canvasid");
    var numberColumns = "4";

    var table = me.drawHelper.createLayoutTable();
    table.setAttribute("width", me.CANVAS_WIDTH);
    canvas.appendChild(table);

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("inventory-tabletitlelabel", "Add Serial")
    label.setAttribute("id", "inventory-serialMainTitleId");
    cell.appendChild(label);    

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Title for status
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "status"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "number of ports"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Status field
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("inventory-statusid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-numberportsid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    me.getTypeStatusesXmlHttp = new XMLHttpRequest();
    var requestPage = me.inventoryURL + "?retrieve=statuses&elementtype=serial";
    me.getTypeStatusesXmlHttp.onreadystatechange = me.handleStatusesReply;
    me.getTypeStatusesXmlHttp.open("GET", requestPage, true);
    me.getTypeStatusesXmlHttp.send(null);    
    me.activeStatusSelectBoxID = "inventory-statusid";

    // Titles for mac address, vendor and model fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "mac address"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "vendor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "model"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));

    // Mac address, vendor and model fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please select...", "other...");
    var select = me.formHelper.createSelectBox("inventory-macaddressid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "MAC Address");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-vendorid", me.selectBoxClass, options, me.populateModels);
    select.setAttribute("popuplabel", "Vendor");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.setAttribute("colspan", "2");
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-modelid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "Model");
    cell.appendChild(select);

    // Titles for powerswitch/port, username and password fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch port"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "username"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "password"));

    // Powerswitch/port, username and password fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchid", me.selectBoxClass, options, me.populatePowerPorts);
    select.setAttribute("popuplabel", "Power Switch");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchportid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Power Switch Port");
    cell.appendChild(select);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-usernameid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createPasswordBox("inventory-passwordid", me.textBoxClass);
    cell.appendChild(textBox);

    // Titles for building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "building"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "floor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "room"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack row #"));

    // Building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-buildingid", me.textBoxClass, "malet place");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-floorid", me.textBoxClass, "4");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-roomid", me.textBoxClass, "4.15");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-rackrowid", me.textBoxClass, "1");
    cell.appendChild(textBox);

    // Titles for rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack start unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack end unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "front/back position"));

    // Rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-racknameid", me.selectBoxClass, options, me.populateRackUnits);
    select.setAttribute("popuplabel", "Rack Name");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackstartunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack Start Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackendunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack End Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("front", "rear", "both");
    var select = me.formHelper.createSelectBox("inventory-nodepositionid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Front/Rear Position");
    cell.appendChild(select);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Titles for attribute name, value and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute value"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute list"));

    // Attribute name, value, add button and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeNameId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeValueId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-AddAttributeButtonId", me.buttonClass, "Add attribute", me.addAttribute);
    button.setAttribute("resultTextAreaId", "inventory-AttributeListId");
    button.setAttribute("attributeNameId", "inventory-AttributeNameId");
    button.setAttribute("attributeValueId", "inventory-AttributeValueId");
    cell.appendChild(button);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textArea = me.formHelper.createTextArea("inventory-AttributeListId", me.textAreaClass, "2", "40");
    cell.appendChild(textArea);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("30", numberColumns));

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-serialCreateButtonId", me.buttonClass, "Add Serial", me.addElementRequest);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("inventory-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Create list of all inputs for later use
    formFields["serial"] = new Array("status", "macaddress", "vendor",
				     "model", "powerswitch", "powerswitchport", 
				     "username", "password", "building", 
				     "floor", "room", "rackrow", 
				     "rackname", "rackstartunit", "rackendunit", 
				     "nodeposition", "numberports");

    // Send request for information to populate select boxes with
    var requestPage = me.inventoryURL + "?retrieve=populateselectboxes"
    me.populateSelectBoxesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePopulateSelectBoxesReply);
    me.populateSelectBoxesRequest.send();
    // Send request for information to populate vendor and model select boxes with
    var requestPage = me.inventoryURL + "?retrieve=supportedhardware&elementtype=serial"
    me.populateVendorModelSelectBoxesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePopulateVendorModelSelectBoxesReply);
    me.populateVendorModelSelectBoxesRequest.send();
  };

  /**
   * Draws input fields for an element of type serviceprocessor; The function sets the submit
   * button's onclick handler to {@link components.inventory.inventory.InventoryTab#addServiceProcessor}
   */
  this.drawServiceprocessorFields = function drawServiceprocessorFields()
  {
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.outstandingPopulateRequests = 3;
    var canvas = document.getElementById("inventory-canvasid");
    var numberColumns = "4";

    var table = me.drawHelper.createLayoutTable();
    table.setAttribute("width", me.CANVAS_WIDTH);
    canvas.appendChild(table);

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("inventory-tabletitlelabel", "Add Service Processor");
    label.setAttribute("id", "inventory-serviceprocessorMainTitleId");
    cell.appendChild(label);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Title for status
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "status"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Status field
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("inventory-statusid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    me.getTypeStatusesXmlHttp = new XMLHttpRequest();
    var requestPage = me.inventoryURL + "?retrieve=statuses&elementtype=serviceprocessor";
    me.getTypeStatusesXmlHttp.onreadystatechange = me.handleStatusesReply;
    me.getTypeStatusesXmlHttp.open("GET", requestPage, true);
    me.getTypeStatusesXmlHttp.send(null);    
    me.activeStatusSelectBoxID = "inventory-statusid";

    // Titles for mac address, power switch/port fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "mac address"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch port"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Mac address, power switch/port fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please select...", "other...");
    var select = me.formHelper.createSelectBox("inventory-macaddressid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "MAC Address");
    cell.appendChild(select);
    
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchid", me.selectBoxClass, options, me.populatePowerPorts);
    select.setAttribute("popuplabel", "Power Switch");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchportid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Power Switch Port");
    cell.appendChild(select);    
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Titles for vendor, model, username and password
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "vendor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "model"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "username"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "password"));

    // Vendor, model, username and password
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-vendorid", me.selectBoxClass, options, me.populateModels);
    select.setAttribute("popuplabel", "Vendor");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-modelid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "Model");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-usernameid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createPasswordBox("inventory-passwordid", me.textBoxClass);
    cell.appendChild(textBox);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Titles for attribute name, value and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute value"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute list"));

    // Attribute name, value, add button and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeNameId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeValueId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-AddAttributeButtonId", me.buttonClass, "Add attribute", me.addAttribute);
    button.setAttribute("resultTextAreaId", "inventory-AttributeListId");
    button.setAttribute("attributeNameId", "inventory-AttributeNameId");
    button.setAttribute("attributeValueId", "inventory-AttributeValueId");
    cell.appendChild(button);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textArea = me.formHelper.createTextArea("inventory-AttributeListId", me.textAreaClass, "2", "40");
    cell.appendChild(textArea);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("30", numberColumns));

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-serviceprocessorCreateButtonId", me.buttonClass, "Add Serviceprocess", me.addElementRequest);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("inventory-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Create list of all inputs for later use
    formFields["serviceprocessor"] = new Array("status", "macaddress", "powerswitch", 
					       "powerswitchport", "vendor", "model", 
					       "username", "password");

    // Send request for information to populate select boxes with
    var requestPage = me.inventoryURL + "?retrieve=populateselectboxes"
    me.populateSelectBoxesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePopulateSelectBoxesReply);
    me.populateSelectBoxesRequest.send();
    // Send request for information to populate vendor and model select boxes with
    var requestPage = me.inventoryURL + "?retrieve=supportedhardware&elementtype=serviceprocessor"
    me.populateVendorModelSelectBoxesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePopulateVendorModelSelectBoxesReply);
    me.populateVendorModelSelectBoxesRequest.send();
  };

  /**
   * Draws input fields for an element of type server by calling 
   * {@link components.inventory.inventory.InventoryTab#drawComputerFields}
   */
  this.drawServerFields = function drawServerFields()
  {
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.outstandingPopulateRequests = 2;
    var canvas = document.getElementById("inventory-canvasid");
    var numberColumns = "4";

    var table = me.drawHelper.createLayoutTable();
    table.setAttribute("width", me.CANVAS_WIDTH);
    canvas.appendChild(table);

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("inventory-tabletitlelabel", "Add Server");
    label.setAttribute("id", "inventory-serverMainTitleId");
    cell.appendChild(label);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Titles for status, vendor and model
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "status"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "vendor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "model"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Status, vendor and model fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("inventory-statusid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-vendorid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-modelid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    me.getTypeStatusesXmlHttp = new XMLHttpRequest();
    var requestPage = me.inventoryURL + "?retrieve=statuses&elementtype=server";
    me.getTypeStatusesXmlHttp.onreadystatechange = me.handleStatusesReply;
    me.getTypeStatusesXmlHttp.open("GET", requestPage, true);
    me.getTypeStatusesXmlHttp.send(null);    
    me.activeStatusSelectBoxID = "inventory-statusid";

    // Titles for mac address, service processor, netbootable and infrastructure fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "infrastructure mac address"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "service processor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "netbootable"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "infrastructure"));

    // Mac address, service processor, netbootable and infrastructure fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please select...", "none", "other...");
    var select = me.formHelper.createSelectBox("inventory-infrastructuremacaddressid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "Infrastructure MAC Address");
    cell.appendChild(select);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serviceprocessorid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Service Processor");
    cell.appendChild(select);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("no");
    var selectBox = me.formHelper.createSelectBox("inventory-netbootableid", me.selectBoxClass, options, null);
    selectBox.disabled = true;
    cell.appendChild(selectBox)

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("yes");
    var selectBox = me.formHelper.createSelectBox("inventory-infrastructureid", me.selectBoxClass, options, null);
    selectBox.disabled = true;
    cell.appendChild(selectBox);
    
    // Titles for external mac, ip and subnet
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "management mac address"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "external mac address"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "external ip address"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "external subnet"));

    // External mac, ip and subnet fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please select...", "none", "other...");
    var select = me.formHelper.createSelectBox("inventory-managementmacaddressid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "Management MAC Address");
    cell.appendChild(select);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please select...", "none", "other...");
    var select = me.formHelper.createSelectBox("inventory-externalmacaddressid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "External MAC Address");
    cell.appendChild(select);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-externalipid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-externalsubnetid", me.textBoxClass, "");
    cell.appendChild(textBox);

    // Titles for power switch and serial fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch port"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "serial"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "serial port"));

    // Powerswitch and serial fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchid", me.selectBoxClass, options, me.populatePowerPorts);
    select.setAttribute("popuplabel", "Power Switch");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchportid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Power Switch Port");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serialid", me.selectBoxClass, options, me.populateSerialPorts);
    select.setAttribute("popuplabel", "Serial");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serialportid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Serial Port");
    cell.appendChild(select);

    // Titles for building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "building"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "floor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "room"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack row #"));

    // Building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-buildingid", me.textBoxClass, "malet place");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-floorid", me.textBoxClass, "4");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-roomid", me.textBoxClass, "4.15");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-rackrowid", me.textBoxClass, "1");
    cell.appendChild(textBox);

    // Titles for rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack start unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack end unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "front/back position"));

    // Rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-racknameid", me.selectBoxClass, options, me.populateRackUnits);
    select.setAttribute("popuplabel", "Rack Name");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackstartunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack Start Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackendunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack End Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("front", "rear", "both");
    var select = me.formHelper.createSelectBox("inventory-nodepositionid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Front/Rear Position");
    cell.appendChild(select);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Titles for attribute name, value and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute value"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute list"));

    // Attribute name, value, add button and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeNameId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeValueId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-AddAttributeButtonId", me.buttonClass, "Add attribute", me.addAttribute);
    button.setAttribute("resultTextAreaId", "inventory-AttributeListId");
    button.setAttribute("attributeNameId", "inventory-AttributeNameId");
    button.setAttribute("attributeValueId", "inventory-AttributeValueId");
    cell.appendChild(button);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textArea = me.formHelper.createTextArea("inventory-AttributeListId", me.textAreaClass, "2", "40");
    cell.appendChild(textArea);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("30", numberColumns));

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-serverCreateButtonId", me.buttonClass, "Add server", me.addElementRequest);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("inventory-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Create list of all inputs for later use
    formFields["server"] = new Array("status", "infrastructuremacaddress", "serviceprocessor", 
				     "managementmacaddress", "externalmacaddress", "externalip", 
				     "externalsubnet", "powerswitch", "powerswitchport", 
				     "serial", "serialport", "building", 
				     "floor", "room", "rackrow", 
				     "rackname", "rackstartunit", "rackendunit", 
				     "nodeposition", "vendor", "model");

    // Send request for information to populate select boxes with
    var requestPage = me.inventoryURL + "?retrieve=populateselectboxes"
    me.populateSelectBoxesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePopulateSelectBoxesReply);
    me.populateSelectBoxesRequest.send();
  };

  /**
   * Onclick event handler for cancel button, pops up a confirm box and clears the central canvas if
   * the answer is yes
   */
  this.cancelAction = function cancelAction()
  {
    var answer = confirm("Are you sure you want to cancel?");
    if (answer)
    {
      me.clearCanvas();
      document.getElementById("inventory-typeselectboxaddid").selectedIndex = 0;
      document.getElementById("inventory-typeselectboxeditid").selectedIndex = 0;
      document.getElementById("inventory-orphanselectboxaddid").selectedIndex = 0;      
    }
  };

  /**
   * Draws input fields for an element of type computer; The function sets the submit
   * button's onclick handler to {@link components.inventory.inventory.InventoryTab#addComputer}
   */
  this.drawComputerFields = function drawComputerFields()
  {
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
    me.outstandingPopulateRequests = 2;
    var canvas = document.getElementById("inventory-canvasid");
    var numberColumns = "4";

    var table = me.drawHelper.createLayoutTable();
    table.setAttribute("width", me.CANVAS_WIDTH);
    canvas.appendChild(table);

    // Main title
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var label = me.drawHelper.createLabel("inventory-tabletitlelabel", "Add Computer");
    label.setAttribute("id", "inventory-computerMainTitleId");
    cell.appendChild(label);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Titles for status, vendor and model
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "status"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "vendor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "model"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    // Status, vendor and model fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var selectBox = me.formHelper.createSelectBox("inventory-statusid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-vendorid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-modelid", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);

    me.getTypeStatusesXmlHttp = new XMLHttpRequest();
    var requestPage = me.inventoryURL + "?retrieve=statuses&elementtype=computer";
    me.getTypeStatusesXmlHttp.onreadystatechange = me.handleStatusesReply;
    me.getTypeStatusesXmlHttp.open("GET", requestPage, true);
    me.getTypeStatusesXmlHttp.send(null);    
    me.activeStatusSelectBoxID = "inventory-statusid";

    // Titles for mac address, service processor, netbootable and infrastructure fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "mac address"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "service processor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "netbootable"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "infrastructure"));

    // Mac address, service processor, netbootable and infrastructure fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please select...", "other...");
    var select = me.formHelper.createSelectBox("inventory-macaddressid", me.selectBoxClass, options, me.showPopUp);
    select.setAttribute("popuplabel", "MAC Address");
    cell.appendChild(select);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serviceprocessorid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Service Processor");
    cell.appendChild(select);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("yes", "no");
    var selectBox = me.formHelper.createSelectBox("inventory-netbootableid", me.selectBoxClass, options, null);
    cell.appendChild(selectBox)

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("no");
    var selectBox = me.formHelper.createSelectBox("inventory-infrastructureid", me.selectBoxClass, options, null);
    selectBox.disabled = true;
    cell.appendChild(selectBox);
    
    // Titles for power switch and serial fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "powerswitch port"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "serial"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "serial port"));

    // Powerswitch and serial fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchid", me.selectBoxClass, options, me.populatePowerPorts);
    select.setAttribute("popuplabel", "Power Switch");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-powerswitchportid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Power Switch Port");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serialid", me.selectBoxClass, options, me.populateSerialPorts);
    select.setAttribute("popuplabel", "Serial");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-serialportid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Serial Port");
    cell.appendChild(select);

    // Titles for building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "building"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "floor"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "room"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack row #"));

    // Building, floor, room and rackrow fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-buildingid", me.textBoxClass, "malet place");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-floorid", me.textBoxClass, "4");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-roomid", me.textBoxClass, "4.15");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-rackrowid", me.textBoxClass, "1");
    cell.appendChild(textBox);

    // Titles for rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack start unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "rack end unit"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "front/back position"));

    // Rackname, rack start unit, rack end unit and position fields
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-racknameid", me.selectBoxClass, options, me.populateRackUnits);
    select.setAttribute("popuplabel", "Rack Name");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackstartunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack Start Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("please wait...");
    var select = me.formHelper.createSelectBox("inventory-rackendunitid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Rack End Unit");
    cell.appendChild(select);    

    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var options = new Array("front", "rear", "both");
    var select = me.formHelper.createSelectBox("inventory-nodepositionid", me.selectBoxClass, options, null);
    select.setAttribute("popuplabel", "Front/Rear Position");
    cell.appendChild(select);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Titles for attribute name, value and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute name"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute value"));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", ""));
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.appendChild(me.drawHelper.createLabel("inventory-boldlabel", "attribute list"));

    // Attribute name, value, add button and attribute list
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeNameId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var textBox = me.formHelper.createTextBox("inventory-AttributeValueId", me.textBoxClass, "");
    cell.appendChild(textBox);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("valign", "top");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-AddAttributeButtonId", me.buttonClass, "Add attribute", me.addAttribute);
    button.setAttribute("resultTextAreaId", "inventory-AttributeListId");
    button.setAttribute("attributeNameId", "inventory-AttributeNameId");
    button.setAttribute("attributeValueId", "inventory-AttributeValueId");
    cell.appendChild(button);
    var cell = me.drawHelper.createLayoutCell();
    row.appendChild(cell);
    var textArea = me.formHelper.createTextArea("inventory-AttributeListId", me.textAreaClass, "2", "40");
    cell.appendChild(textArea);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("30", numberColumns));

    // Submit button row
    var row = me.drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = me.drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var button = me.formHelper.createButton("inventory-computerCreateButtonId", me.buttonClass, "Add computer", me.addElementRequest);
    cell.appendChild(button);
    cell.appendChild(me.drawHelper.createHorizontalSpacer("10"));
    var button = me.formHelper.createButton("inventory-cancelButtonId", me.buttonClass, "Cancel", me.cancelAction);
    cell.appendChild(button);

    // Spacer row
    table.appendChild(me.drawHelper.createLayoutSpacerRow("10", numberColumns));

    // Create list of all inputs for later use
    formFields["computer"] = new Array("status", "macaddress", "serviceprocessor",
				       "netbootable", "infrastructure", "powerswitch",
				       "powerswitchport", "serial", "serialport",
				       "building", "floor", "room",
				       "rackrow", "rackname", "rackstartunit",
				       "rackendunit", "nodeposition", "vendor",
				       "model");

    // Send request for information to populate select boxes with
    var requestPage = me.inventoryURL + "?retrieve=populateselectboxes"
    me.populateSelectBoxesRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handlePopulateSelectBoxesReply);
    me.populateSelectBoxesRequest.send();
  };

  /**
   * Performs various checks on the user's inputs and sends a request to add
   * an element to the testbed.
   */
  this.addElementRequest = function addElementRequest()
  {
    var elementType = document.getElementById("inventory-typeselectboxaddid").value;
    // Get user confirmation
    if (!confirmAdd()) return;
    // Check that the form is ok
    if (!me["verify" + elementType[0].toUpperCase() + elementType.substring(1) + "Form"]()) return;
    var attributes = checkAndRetrieveAttributes(elementType);
    if (!attributes) return;
    // Gather the information from the inputs and send the request
    var inputValues = retrieveInputValues(formFields[elementType]);
    sendAddRequest(inputValues, attributes);
  };

  /**
   * Performs various checks on the user's inputs and sends a request to edit
   * an element to the testbed.
   */
  this.editElementRequest = function editElementRequest()
  {
    var elementType = document.getElementById("inventory-typeselectboxeditid").value;
    // Get user confirmation
    if (!confirmEdit()) return;
    // Check that the form is ok
    if (!me["verify" + elementType[0].toUpperCase() + elementType.substring(1) + "Form"]()) return;
    var attributes = checkAndRetrieveAttributes(elementType);
    if (!attributes) return;
    // Gather the information from the inputs and send the request
    var inputValues = retrieveInputValues(formFields[elementType]);
    sendEditRequest(inputValues, attributes);
  };

  /**
   * Checks a computer form for input correctness.
   * @return {boolean} true if the form is correct, false otherwise
   */
  this.verifyComputerForm = function verifyComputerForm()
  {
    textBoxesIDs = new Array("inventory-buildingid", "inventory-floorid", "inventory-roomid", 
			     "inventory-rackrowid", "inventory-vendorid", "inventory-modelid");
    selectBoxesIDs = new Array("inventory-statusid", "inventory-serviceprocessorid", "inventory-powerswitchid", 
			       "inventory-serialid", "inventory-racknameid", "inventory-rackstartunitid", 
			       "inventory-rackendunitid", "inventory-macaddressid");

    if (!areTextBoxesFilled(textBoxesIDs)) return false;
    if (!areValuesSelected(selectBoxesIDs)) return false;
    if (!verifyNoneSelectBoxes(new Array("serial", "powerswitch"))) return false;
    if (!verifyMACAddressInputs(new Array("inventory-macaddressid"))) return false;
    if (!verifyRackUnits) return false;

    // Form ok
    return true;
  };

  /**
   * Checks a service processor form for input correctness.
   * @return {boolean} true if the form is correct, false otherwise
   */
  this.verifyServiceprocessorForm = function verifyServiceprocessorForm()
  {
    selectBoxesIDs = new Array("inventory-statusid", "inventory-powerswitchid", "inventory-macaddressid",
			       "inventory-vendorid", "inventory-modelid");

    if (!verifyNoneSelectBoxes(new Array("powerswitch"))) return false;
    if (!areValuesSelected(selectBoxesIDs)) return;
    if (!verifyMACAddressInputs(new Array("inventory-macaddressid"))) return false;

    // Form ok
    return true;
  };

  /**
   * Checks a server form for input correctness.
   * @return {boolean} true if the form is correct, false otherwise
   */
  this.verifyServerForm = function verifyServerForm()
  {

    // Make sure that text boxes are filled
    textBoxesIDs = new Array("inventory-buildingid", "inventory-floorid", "inventory-roomid", 
			     "inventory-rackrowid", "inventory-vendorid", "inventory-modelid");
    selectBoxesIDs = new Array("inventory-statusid", "inventory-infrastructuremacaddressid", "inventory-serviceprocessorid", 
			       "inventory-managementmacaddressid", "inventory-externalmacaddressid", "inventory-powerswitchid",
			       "inventory-serialid", "inventory-racknameid", "inventory-rackstartunitid", 
			       "inventory-rackendunitid");

    if (!areTextBoxesFilled(textBoxesIDs)) return false;
    if (!areValuesSelected(selectBoxesIDs)) return false;
    if (!verifyNoneSelectBoxes(new Array("serial", "powerswitch"))) return false;
    if (!verifyRackUnits) return false;

    // Make sure that mac addresses are valid and that at least one of the is set to something other than 'none'
    var infrastructureMACAddress = document.getElementById("inventory-infrastructuremacaddressid").value;
    var managementMACAddress = document.getElementById("inventory-managementmacaddressid").value;
    var externalMACAddress = document.getElementById("inventory-externalmacaddressid").value;
    if (infrastructureMACAddress == "none" && managementMACAddress == "none" && externalMACAddress == "none")
    {
      alert("you must specify at least one mac address");
      return false;
    };
    if (infrastructureMACAddress != "none" && !isMACAddress(infrastructureMACAddress))
    {
      alert("invalid infrastructure mac address: " + infrastructureMACAddress);
      return false;
    }
    if (managementMACAddress != "none" && !isMACAddress(managementMACAddress))
    {
      alert("invalid management mac address: " + managementMACAddress);
      return false;
    }
    if (externalMACAddress != "none" && !isMACAddress(externalMACAddress))
    {
      alert("invalid external mac address: " + externalMACAddress);
      return false;
    }

    // If an external mac address is given, make sure that its ip and subnet are given as well and that these have the correct ipv4 format
    if (externalMACAddress != "none")
    {
      var externalIP = document.getElementById("inventory-externalipid").value;
      var externalSubnet = document.getElementById("inventory-externalsubnetid").value;

      if (externalIP == "" || externalSubnet == "")
      {
	alert("you've given an external mac address, so you must specify both its ip address and subnet");
	return false;
      }
      if (!isIPAddress(externalIP))
      {
	alert("invalid external ip address: " + externalIP + " (example:128.123.34.3)");
	return false;
      }
      if (!isIPAddress(externalSubnet))
      {
	alert("invalid subnet address: " + externalSubnet + " (example:255.255.255.0)");
	return false;
      }
    }
    
    // Form ok
    return true;
  };

  /**
   * Checks a serial form for input correctness.
   * @return {boolean} true if the form is correct, false otherwise
   */
  this.verifySerialForm = function verifySerialForm()
  {
    textBoxesIDs = new Array("inventory-buildingid", "inventory-floorid", "inventory-roomid", 
			     "inventory-rackrowid", "inventory-numberportsid");
    selectBoxesIDs = new Array("inventory-statusid", "inventory-powerswitchid", "inventory-macaddressid",
			       "inventory-vendorid", "inventory-modelid", "inventory-racknameid",
			       "inventory-rackstartunitid", "inventory-rackendunitid");
    integerTextBoxesIDs = new Array("inventory-numberportsid");

    if (!areTextBoxesFilled(textBoxesIDs)) return false;
    if (!areValuesSelected(selectBoxesIDs)) return false;
    if (!verifyNoneSelectBoxes(new Array("powerswitch"))) return false;
    if (!verifyMACAddressInputs(new Array("inventory-macaddressid"))) return false;
    if (!verifyRackUnits) return false;
    if (!areValuesIntegers(integerTextBoxesIDs)) return false;

    // Form ok
    return true;
  };

  /**
   * Checks a power switch form for input correctness.
   * @return {boolean} true if the form is correct, false otherwise
   */
  this.verifyPowerswitchForm = function verifyPowerswitchForm()
  {
    textBoxesIDs = new Array("inventory-buildingid", "inventory-floorid", "inventory-roomid", 
			     "inventory-rackrowid", "inventory-numberportsid");
    selectBoxesIDs = new Array("inventory-statusid", "inventory-serialid", "inventory-serialportid", 
			       "inventory-racknameid", "inventory-rackstartunitid", "inventory-rackendunitid",
			       "inventory-macaddressid");
    integerTextBoxesIDs = new Array("inventory-numberportsid");

    if (!areTextBoxesFilled(textBoxesIDs)) return false;
    if (!areValuesSelected(selectBoxesIDs)) return false;
    if (!verifyNoneSelectBoxes(new Array("serial"))) return false;
    if (!verifyMACAddressInputs(new Array("inventory-macaddressid"))) return false;
    if (!verifyRackUnits) return false;
    if (!areValuesIntegers(integerTextBoxesIDs)) return false;

    // Form ok
    return true;
  };

  /**
   * Checks a switch form for input correctness.
   * @return {boolean} true if the form is correct, false otherwise
   */
  this.verifySwitchForm = function verifySwitchForm()
  {
    textBoxesIDs = new Array("inventory-buildingid", "inventory-floorid", "inventory-roomid", 
			     "inventory-rackrowid", "inventory-numberportsid");
    selectBoxesIDs = new Array("inventory-statusid", "inventory-macaddressid", 
			       "inventory-vendorid", "inventory-modelid", "inventory-powerswitchid",
			       "inventory-powerswitchportid", "inventory-serialid", "inventory-serialportid", 
			       "inventory-racknameid", "inventory-rackstartunitid", "inventory-rackendunitid");    
    integerTextBoxesIDs = new Array("inventory-numberportsid");

    if (!areTextBoxesFilled(textBoxesIDs)) return false;
    if (!areValuesSelected(selectBoxesIDs)) return false;
    if (!verifyNoneSelectBoxes(new Array("serial", "powerswitch"))) return false;
    if (!verifyMACAddressInputs(new Array("inventory-macaddressid"))) return false;
    if (!verifyRackUnits) return false;
    if (!areValuesIntegers(integerTextBoxesIDs)) return false;

    // Form ok
    return true;
  };

  /**
   * Checks a router form for input correctness.
   * @return {boolean} true if the form is correct, false otherwise
   */
  this.verifyRouterForm = function verifyRouterForm()
  {
    textBoxesIDs = new Array("inventory-buildingid", "inventory-floorid", "inventory-roomid", 
			     "inventory-rackrowid", "inventory-vendorid",
			     "inventory-modelid");
    selectBoxesIDs = new Array("inventory-statusid", "inventory-macaddressid", "inventory-powerswitchid",
			       "inventory-powerswitchportid", "inventory-serialid", "inventory-serialportid", 
			       "inventory-racknameid", "inventory-rackstartunitid", "inventory-rackendunitid");    
    integerTextBoxesIDs = new Array("inventory-numberportsid");

    if (!areTextBoxesFilled(textBoxesIDs)) return false;
    if (!areValuesSelected(selectBoxesIDs)) return false;
    if (!verifyNoneSelectBoxes(new Array("serial", "powerswitch"))) return false;
    if (!verifyMACAddressInputs(new Array("inventory-macaddressid"))) return false;
    if (!verifyRackUnits) return false;
    if (!areValuesIntegers(integerTextBoxesIDs)) return false;

    // Form ok
    return true;
  };

  /**
   * Checks a rack form for input correctness.
   * @return {boolean} true if the form is correct, false otherwise
   */
  this.verifyRackForm = function verifyRackForm()
  {
    textBoxesIDs = new Array("inventory-vendorid", "inventory-modelid", "inventory-descriptionid",
			     "inventory-buildingid", "inventory-floorid", "inventory-roomid", 
			     "inventory-rackrowid", "inventory-rowpositionid", "inventory-heightid",
			     "inventory-widthid", "inventory-depthid", "inventory-numberunitsid");
    selectBoxesIDs = new Array("inventory-statusid", "inventory-rearrightslotsid", "inventory-rearleftslotsid");

    integerTextBoxesIDs = new Array("inventory-rowpositionid", "inventory-heightid", "inventory-widthid", 
				    "inventory-depthid", "inventory-numberunitsid");

    if (!areTextBoxesFilled(textBoxesIDs)) return false;
    if (!areValuesSelected(selectBoxesIDs)) return false;
    if (!areValuesIntegers(integerTextBoxesIDs)) return false;

    // Form ok
    return true;
  };

  /**
   * Checks a filesystem form for input correctness.
   * @return {boolean} true if the form is correct, false otherwise
   */
  this.verifyFilesystemForm = function verifyFilesystemFrom()
  {
    textBoxesIDs = new Array("inventory-pathid", "inventory-architectureid", "inventory-ostypeid", 
			     "inventory-descriptionid");
    selectBoxesIDs = new Array("inventory-statusid", "inventory-ownerid")

    if (!areTextBoxesFilled(textBoxesIDs)) return false;
    if (!areValuesSelected(selectBoxesIDs)) return false;

    // Form ok
    return true;
  };

  /**
   * Checks a kernel form for input correctness.
   * @return {boolean} true if the form is correct, false otherwise
   */
  this.verifyKernelForm = function verifyKernelForm()
  {
    textBoxesIDs = new Array("inventory-pathid", "inventory-architectureid", "inventory-ostypeid", 
			     "inventory-descriptionid");
    selectBoxesIDs = new Array("inventory-statusid", "inventory-ownerid")

    if (!areTextBoxesFilled(textBoxesIDs)) return false;
    if (!areValuesSelected(selectBoxesIDs)) return false;

    // Form ok
    return true;
  };

  /**
   * Checks a loader form for input correctness.
   * @return {boolean} true if the form is correct, false otherwise
   */
  this.verifyLoaderForm = function verifyLoaderForm()
  {
    textBoxesIDs = new Array("inventory-pathid", "inventory-architectureid", "inventory-ostypeid", 
			     "inventory-descriptionid");
    selectBoxesIDs = new Array("inventory-statusid", "inventory-ownerid")

    if (!areTextBoxesFilled(textBoxesIDs)) return false;
    if (!areValuesSelected(selectBoxesIDs)) return false;

    // Form ok
    return true;
  };

  /**
   * Deletes an option from a select box based on its text
   * @param {string} selectBoxID The id of the select box to delete from
   * @param {string} text The text to match on
   */
  var deleteSelectBoxOptionByText = function deleteSelectBoxOptionByText(selectBoxID, text)
  {
    var selectBox = document.getElementById(selectBoxID);
    for (var i = 0; i < selectBox.options.length; i++)
      if (selectBox.options[i].text == text)
	selectBox.options[i] = null;
  };

  /**
   * Sends a request to add an element to the testbed.
   * @param {associative array} inputValues The names and values of the inputs
   * @param {associative array} attributes The names and values of the attributes
   */
  var sendAddRequest = function sendAddRequest(inputValues, attributes)
  {
    var elementType = document.getElementById("inventory-typeselectboxaddid").value;
    var requestPage =  me.inventoryURL + "?retrieve=addelement&elementtype=" + escape(elementType);

    for (var key in inputValues)
      requestPage += "&" + key + "=" + escape(inputValues[key]);

    for (var key in attributes)
      requestPage += "&" + key + "=" + escape(attributes[key]);

    me.addEditDeleteElementXmlHttpRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleAddEditDeleteElementReply);
    me.addEditDeleteElementXmlHttpRequest.send();
    me.setDisableControls(true);
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
  };

  /**
   * Sends a request to edit an element to the testbed.
   * @param {associative array} inputValues The names and values of the inputs
   * @param {associative array} attributes The names and values of the attributes
   */
  var sendEditRequest = function sendEditRequest(inputValues, attributes)
  {
    var selectBox = document.getElementById("inventory-typeselectboxeditid");
    var elementID = selectBox.options[selectBox.selectedIndex].text;

    var requestPage =  me.inventoryURL + "?retrieve=editelement&elementid=" + elementID;

    for (var key in inputValues)
      requestPage += "&" + key + "=" + escape(inputValues[key]);

    for (var key in attributes)
      requestPage += "&" + key + "=" + escape(attributes[key]);

    me.addEditDeleteElementXmlHttpRequest = new auxiliary.hen.AsynchronousRequest(requestPage, me.handleAddEditDeleteElementReply);
    me.addEditDeleteElementXmlHttpRequest.send();
    me.setDisableControls(true);
    me.showLoadingDiv(LOADING_DIV_X_POSITION, LOADING_DIV_Y_POSITION);
  };

  /**
   * Shows a reminder alert if the input values for the given input names are 'none'. The 
   * id of each input should be of the form 'inventory-' + inputName + 'id'. If an input's
   * value is 'none', then the function makes sure that a value is selected for the input
   * of the form 'inventory-' + inputName + 'portid'.
   * @param {list of string} inputNames The names of the inputs to verify
   * @return {boolean} True if the condiction described above is met, false otherwise
   */
  var verifyNoneSelectBoxes = function verifyNoneSelectBoxes(inputNames)
  {
    for (var i = 0; i < inputNames.length; i++)
    {
      var value = document.getElementById("inventory-" + inputNames[i] + "id");
      if (value == "none")
	alert("you're setting " + inputNames[i] + " to none, please remember to specify it later");
      else if (!areValuesSelected(new Array("inventory-" + inputNames[i] + "portid")))
	return false;
    }
    return true;
  };

  /**
   * Disables the given inputs
   * @param {list of string} inputIDs The ids of the inputs to disable
   */
  var disableInputs = function disableInputs(inputIDs)
  {
    for (var i = 0; i < inputIDs.length; i++)
      try { document.getElementById(inputIDs[i]).disabled = true; } catch (e) {}
  };

  /**
   * Shows a confirm box asking whether to add an element to the testbed
   * @return {boolean} The answer to the confirm box
   */
  var confirmAdd = function confirmAdd()
  {
    var elementType = document.getElementById("inventory-typeselectboxaddid").value;
    return confirm("Are you sure you want to add the " + elementType + "?");
  };

  /**
   * Shows a confirm box asking whether to edit an element to the testbed
   * @return {boolean} The answer to the confirm box
   */
  var confirmEdit = function confirmEdit()
  {
    var selectBox = document.getElementById("inventory-typeselectboxeditid");
    var elementID = selectBox.options[selectBox.selectedIndex].text;
    return confirm("Are you sure you want to edit " + elementID + "?");
  };

  /**
   * Makes sure that the start unit for a rack is less than the end unit and that the range does 
   * not span unavailable units. If any of these conditions is not met, an alert is shown and false
   * is returned.
   * @return {boolean} true if the above conditions are met, false otherwise
   */
  var verifyRackUnits = function verifyRackUnits()
  {
    // Make sure that start unit is less than end unit and that the range does not span unavailable units
    var rackStartUnit = document.getElementById("inventory-rackstartunitid").value;
    var rackEndUnit = document.getElementById("inventory-rackendunitid").value;
    if (parseInt(rackStartUnit) > parseInt(rackEndUnit))
    {
      alert("rack start unit " + rackStartUnit + " should be less than rack end unit " + rackEndUnit);
      return false;
    }
    var selectBox = document.getElementById("inventory-rackstartunitid");
    for (var i = parseInt(rackStartUnit); i < parseInt(rackEndUnit); i++)
      if (!isInSelectBox(selectBox, new String(i)))
      {
	alert("rack unit range " + rackStartUnit + "-" + rackEndUnit + " includes unavailable unit " + i);
	return false;
      }
    return true;
  };

  /**
   * Given a list of input ids, verifies that their values are valid mac addresses. If any of the inputs
   * has an invalid mac address, an alert is shown and the function returns false.
   * @param {list of string} inputsIDs The ids of the inputs to verify.
   * @return {boolean} true if all the inputs have valid mac addresses, false otherwise
   */
  var verifyMACAddressInputs = function verifyMACAddressInputs(inputsIDs)
  {
    for (var i = 0; i < inputsIDs.length; i++)
    {
      var macAddress = document.getElementById(inputsIDs[i]).value;
      if (!isMACAddress(macAddress))
      {
	alert("invalid mac address: " + macAddress);
	return false;
      }
    }
    return true;
  };

  /**
   * Makes sure that attribute names have no spaces and parses the attributes currently in
   * the text area. Also ensures that no attributes have the same name as the inputs in the form.
   * @return {associative array} An array whose keys are the attribute names and whose values the attributes' values
   */
  var checkAndRetrieveAttributes = function checkAndRetrieveAttributes(elementType)
  {
    var attributes = new Array();
    try
    {
      var unparsedAttributes = new Array();
      unparsedAttributes = document.getElementById("inventory-AttributeListId").value.split("\n");
      for (var i = 0; i < unparsedAttributes.length - 1; i++)
      {
	var attributeName = unparsedAttributes[i].substring(0, unparsedAttributes[i].indexOf("=") - 1);
	if (attributeName.indexOf(" ") != -1)
	{
	  alert("attribute names must not contain spaces: " + attributeName);
	  return null;
	}

	inputNames = formFields[elementType];
	for (var j = 0; j < inputNames.length; j++)
	  if (attributeName.toUpperCase() == inputNames[j].toUpperCase())
	  {
	    alert("attribute names cannot be the same as input names: " + attributeName);
	    return null;
	  }

	var attributeValue = unparsedAttributes[i].substring(unparsedAttributes[i].indexOf("=") + 2);
	attributes[attributeName] = attributeValue;
      }
    }
    catch (e) {}
    
    return attributes;
  };

  /** 
   * Given a list of input names, this function retrieves their values and puts the results into a dictionary
   * whose keys are the input names and whose values are the input values. Note that the ids of the inputs 
   * should follow the form: 'inventory-[inputname]id'
   * @param {Array of string} inputNames The names of the inputs to obtain values from
   * @return {Associative Array} A dictionary with the results
   */
  var retrieveInputValues = function retrieveInputValues(inputNames)
  {
    var values = new Array();
    for (var i = 0; i < inputNames.length; i++)
    {
      var value = document.getElementById("inventory-" + inputNames[i] + "id").value;
      if ((value == "please select...") || (value == ""))
	value = "none";
      values[inputNames[i]] = value;
    };

    return values;
  };
    
  /**
   * Checks that the given parameter is a valid mac address
   * @param {string} macAddress The string to test
   * @return {boolean} true if the given string is a valid mac address, false otherwise
   */
  var isMACAddress = function isMACAddress(macAddress)
  {
    var macAddressRegEx = "^([0-9|a-f|A-F][0-9|a-f|A-F]:){5}([0-9|a-f|A-F][0-9|a-f|A-F])$";
    if (macAddress.match(macAddressRegEx))
      return true;
    return false;
  };

  /**
   * Checks that the given parameter is a valid ipv4 address
   * @param {string} ipAddress The string to test
   * @return {boolean} true if the given string is a valid ipv4 address, false otherwise
   */
  var isIPAddress = function isIPAddress(ipAddress)
  {
    var octets = ipAddress.split(".");
    if (octets.length != 4)
      return false;

    for (var i = 0; i < octets.length; i++)
    {
      if (isNaN(octets[i]) || parseInt(octets[i]) < 0 || parseInt(octets[i]) > 255)
	return false;
    }
    return true;
  };

  /**
   * Checks to see whether the given string is in the given select box
   * @param {HTML select box} selectBox The HTML select box to search in
   * @param {string} element The element to search for
   * @return {boolean} true if the element is in the select box, false otherwise
   */
  var isInSelectBox = function isInSelectBox(selectBox, element)
  {
    for (var i = 0; i < selectBox.options.length; i++)
      if (selectBox[i].value == element)
	return true;
    return false;
  };

  /**
   * Checks that none of the select boxes given have 'please select...', 'please wait...'
   * or 'other...' as their values.
   * @param {Array of string} selectBoxesIDs The ids of the select boxes to check
   * @return {boolean} true if none of the select boxes have the values described above, false otherwise
   */
  var areValuesSelected = function areValuesSelected(selectBoxesIDs)
  {
    for (var i = 0; i < selectBoxesIDs.length; i++)
    {
      var value = document.getElementById(selectBoxesIDs[i]).value;
      if (value == "please select..." || value == "please wait..." || value == "other...")
      {
	var selectBoxName = selectBoxesIDs[i].substring(selectBoxesIDs[i].indexOf("-") + 1, selectBoxesIDs[i].length - 2);
	alert(value + " is not a valid value for " + selectBoxName);
	return false;
      }
    }
    return true;
  };

  /**
   * Checks whether the values of the given inputs are all integeres. If the value is 'none', the 
   * value is ignored
   * @param {Array of string} inputIDs The ids of the inputs to check
   * @return {boolean} true if all the inputs are integers, false otherwise
   */
  var areValuesIntegers = function areValuesIntegers(inputIDs)
  {
    for (var i = 0; i < inputIDs.length; i++)
    {
      var value = document.getElementById(inputIDs[i]).value;
      if (isNaN(value) && value != "none")
      {
	var selectBoxName = inputIDs[i].substring(inputIDs[i].indexOf("-") + 1, inputIDs[i].length - 2);
	alert(selectBoxName + " must be an integer, value given: " + value);
	return false;
      }
    }
    return true;
  };

  /**
   * Checks whether all the text boxes given are filled.
   * @param {Array of string} textBoxesIDs The ids of the text boxes to check
   * @return {boolean} true if all the boxes are filled, false otherwise
   */
  var areTextBoxesFilled = function areTextBoxesFilled(textBoxesIDs)
  {
    for (var i = 0; i < textBoxesIDs.length; i++)
    {
      var value = document.getElementById(textBoxesIDs[i]).value;
      if (value == "")
      {
        var textBoxName = textBoxesIDs[i].substring(textBoxesIDs[i].indexOf("-") + 1, textBoxesIDs[i].length - 2);
        alert("you must fill in the " + textBoxName + " text box");
        return false;
      }
    }
    return true;
  };

  /**
   * When a user clicks on an element id link to edit it, the event handler displays the fields and 
   * asynchronous requests are fired to populate select boxes. At the same time, an asynchronous request
   * is sent to retrieve the element's current values. As a result, depending on the order of the replies,
   * the element's current value may get over-written by the request to populate the select boxes. To prevent
   * this, the draw function for the element to edit states how many requests it sends, and each of the handlers 
   * for these calls this function when finished. If the number of outstanding requests is 0 and we are in edit mode,
   * we send the request to retrieve the element's current values.
   */
  this.countOutstandingReplies = function countOutstandingReplies()
  {
    --me.outstandingPopulateRequests;

    if ((me.outstandingPopulateRequests == 0) && (me.mode == "edit"))
    {
      me.getElementEditInfoXmlHttp = new XMLHttpRequest();
      var selectBox = document.getElementById("inventory-typeselectboxeditid");
      var elementID = selectBox.options[selectBox.selectedIndex].text;
      var requestPage = me.inventoryURL + "?retrieve=elementedit&elementid=" + elementID;
      me.getElementEditInfoXmlHttp.onreadystatechange = me.handleEditReply;
      me.getElementEditInfoXmlHttp.open("GET", requestPage, true);
      me.getElementEditInfoXmlHttp.send(null);    
    }
    else if (me.outstandingPopulateRequests == 0)
    {
      me.setDisableControls(false);
      me.hideLoadingDiv();
    }
  };

  /**
   * Onchange event handler for vendor select box. This function populates the model select box
   * with the models that the testbed supports.
   * @param {Event} evt The onchange event
   */
  this.populateModels = function populateModels(evt)
  {
    var vendor = evt.target.value;
    var modelsSelectBox = document.getElementById("inventory-modelid");
    if (vendor == "other...")
    {
      modelsSelectBox.options.length = 0;
      modelsSelectBox[0] = new Option("please select...", "please select...");
      modelsSelectBox[1] = new Option("other...", "other...");
      me.showPopUp(null, "inventory-vendorid");
      return;
    }

    var models = supportedHardware[vendor];
    modelsSelectBox.options.length = 0;
    modelsSelectBox[0] = new Option("please select...", "please select...");

    if (models)
    {
      for (var i = 0; i < models.length; i++)
      {
	modelsSelectBox[i + 1] = new Option(models[i], models[i]);
      }
    }
    modelsSelectBox[modelsSelectBox.options.length] = new Option("other...", "other...");
  };

  /**
   * Onchange event handler for rack name select box. This function populates the rack start unit and end
   * start unit select boxes with the units that are available on the selected rack.
   * @param {Event} evt The onchange event
   */
  this.populateRackUnits = function populateRackUnits(evt)
  {
    var rackID = evt.target.value;
    var rackStartUnitSelectBox = document.getElementById("inventory-rackstartunitid");
    var rackEndUnitSelectBox = document.getElementById("inventory-rackendunitid");
    var units = unassignedPorts[rackID];

    rackStartUnitSelectBox.options.length = 0;
    rackStartUnitSelectBox[0] = new Option("please select...", "please select...");
    rackEndUnitSelectBox.options.length = 0;
    rackEndUnitSelectBox[0] = new Option("please select...", "please select...");
    
    for (var i = 0; i < units.length; i++)
    {
      rackStartUnitSelectBox[i + 1] = new Option(units[i], units[i]);
      rackEndUnitSelectBox[i + 1] = new Option(units[i], units[i]);
    }
  };

  /**
   * Onchange event handler for powerswitch select box. This function populates the powerswitch port
   * select box with the ports that are free on the selected power switch. If there are no
   * ports (meaning the power switch select box is set to 'none'), then 'none' is set for the power switch
   * ports box and its controls disabled.
   * @param {Event} evt The onchange event
   */
  this.populatePowerPorts = function populatePowerPorts(evt)
  {
    var powerSwitchID = evt.target.value;
    var powerSwitchPortsSelectBox = document.getElementById("inventory-powerswitchportid");
    var ports = unassignedPorts[powerSwitchID];

    powerSwitchPortsSelectBox.disabled = false;
    powerSwitchPortsSelectBox.options.length = 0;
    if (ports)
    {
      powerSwitchPortsSelectBox[0] = new Option("please select...", "please select...");
      for (var i = 0; i < ports.length; i++)
	powerSwitchPortsSelectBox[i + 1] = new Option(ports[i], ports[i]);
    }
    else
    {
      powerSwitchPortsSelectBox[0] = new Option("none", "none");
      powerSwitchPortsSelectBox.disabled = true;
    }
  };

  /**
   * Onchange event handler for serial select box. This function populates the serial port
   * select box with the ports that are free on the selected serial server. If there are no
   * ports (meaning the serial select box is set to 'none'), then 'none' is set for the serial
   * ports box and its controls disabled.
   * @param {Event} evt The onchange event
   */
  this.populateSerialPorts = function populateSerialPorts(evt)
  {
    var serialServerID = evt.target.value;
    var serialServerPortsSelectBox = document.getElementById("inventory-serialportid");
    var ports = unassignedPorts[serialServerID];

    serialServerPortsSelectBox.disabled = false;
    serialServerPortsSelectBox.options.length = 0;

    if (ports)
    {    
      serialServerPortsSelectBox[0] = new Option("please select...", "please select...");
      for (var i = 0; i < ports.length; i++)
	serialServerPortsSelectBox[i + 1] = new Option(ports[i], ports[i]);
    }
    else
    {
      serialServerPortsSelectBox[0] = new Option("none", "none");
      serialServerPortsSelectBox.disabled = true;
    }
  };

  /**
   * Populates the input fields of an element based on the parameters given. For this operation to be successful, the
   * id of the input to be populated needs to follow the format: inventory-[elementType][propertyTagName]id, all in lower caps.
   * @param elementType The element's type
   * @param properties An xml object containing property tags
   * @param attributes An xml object containing attribute tags
   * @param originalElementType The element's original type, in case it is reusing the draw functions of another type
   */
  this.populateFields = function populateFields(elementType, properties, attributes)
  {
    for (var i = 0; i < properties.length; i++)
    {
      var propertyName = auxiliary.hen.getAttributeValue(properties[i], "name");
      var propertyValue = auxiliary.hen.getAttributeValue(properties[i], "value");
      
      var input = document.getElementById("inventory-" + propertyName + "id");

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
  };

  /**
   * Onclick event handler for Add attribute button. The button should have threee attributes
   * set: an attributeNameId, attributeValueId pair and resultTextAreaId, indicating which text area
   * to add the new attribute to.
   * @param evt The event
   */
  this.addAttribute = function addAttribute(evt)
  {
    var textArea = document.getElementById(evt.target.getAttribute("resultTextAreaId"));
    var attributeNameBox = document.getElementById(evt.target.getAttribute("attributeNameId"));
    var attributeValueBox = document.getElementById(evt.target.getAttribute("attributeValueId"));

    textArea.value += attributeNameBox.value + " = " + attributeValueBox.value + "\n";

    attributeNameBox.value = "";
    attributeValueBox.value = "";
  };

  /**
   * Removes any children from the id inventory-canvasid
   */
  this.clearCanvas = function clearCanvas()
  {
    var canvas = document.getElementById("inventory-canvasid");
   
    while (canvas.hasChildNodes())
    {
      canvas.removeChild(canvas.firstChild);
    }
  };

  /**
   * Shows the pop up box. If evt is null, the entered value will be populated into the select box whose
   * id is given
   * @param {Event} evt The event
   * @param {string} theSelectBoxID The id of the select box to populate, used if evt is null
   */
  this.showPopUp = function showPopUp(evt, theSelectBoxID)
  {
    var selectBoxID = null;
    var selectBox = null;
    if (!evt)
    {
      selectBoxID = theSelectBoxID;
      selectBox = document.getElementById(selectBoxID);      
    }
    else
    {
      selectBoxID = evt.target.id;
      selectBox = evt.target;
    }

    if (selectBox.value != "other...")
      return;

    var title = selectBox.getAttribute("popuplabel");

    // Create input box for pop up div
    var input = document.createElement("input");
    input.setAttribute("id", "inventory-floatingInputDivInputId");
    input.setAttribute("type", "text");
    input.setAttribute("value", "");
    input.setAttribute("size", "20");
    input.setAttribute("maxlength", "80");
    input.setAttribute("class", "inventory-longtextinputform");

    // Create pop up div
    popUpDiv = new auxiliary.draw.PopUpInput(me.POP_UP_X_POSITION, me.POP_UP_Y_POSITION, title, 
					     input, "inventory-floatingInputDivId", me.popInputSubmit, 
					     me.tabMainDiv, selectBoxID);
    me.visibilityDivs.push(popUpDiv);

    // Show pop up div
    popUpDiv.showPopUp();
  };

  /**
   * Onclick event handler for the pop up box's submit button. Upon submit, hides the pop up box, delete it and adds the
   * typed in text as an option to the select box, leaving "other..." as the last option in it
   */
  this.popInputSubmit = function popInputSubmit()
  {
    var popUpDivInput = document.getElementById("inventory-floatingInputDivInputId");
    
    // Retrieve the select box that originated the pop-up and populate it with the value of the input
    var selectBox = document.getElementById(popUpDiv.getResultTargetID());
    var value = popUpDivInput.value;

    selectBox[selectBox.options.length - 1] = new Option(value, value);
    selectBox[selectBox.options.length] = new Option("other...", "other...");
    selectBox.selectedIndex = selectBox.options.length - 2;

    // Close and delete the pop up div
    popUpDiv.closePopUp();
    delete popUpDiv;
  };

  /**
   * Onclick event handler for links found in View inventory table's element id column, displays
   * the element's full xml description file
   */
  this.elementIDClick = function elementIDClick(evt)
  {
    var elementID = evt.target.id;
    elementID = elementID.substring(elementID.indexOf("clickdiv") + 8);
    me.displayElementFullInfo(elementID);
  };

  /**
   * Sends an asynchronous request to display an element's full description file.
   * @param selectedElementID The id of the element to retrieve information for.
   */
  this.displayElementFullInfo = function displayElementFullInfo(selectedElementID)
  {
    me.getElementFullInfoXmlHttp = new XMLHttpRequest();

    if (selectedElementID == "select element...")
      return;

    // Retrieve full information for request element
    var requestPage = me.inventoryURL + "?retrieve=element&elementid=" + selectedElementID;
    me.getElementFullInfoXmlHttp.onreadystatechange = me.handleInventoryElementReply;
    me.getElementFullInfoXmlHttp.open("GET", requestPage, true);
    me.getElementFullInfoXmlHttp.send(null);
  };

  /**
   * Sets the disabled property of all inputs in the control panel as well as any submit buttons.
   * (note that any buttons are hidden rather than disabled)
   * @param {boolean} disable Whether to disable the controls or not
   */
  this.setDisableControls = function setDisableControls(disable)
  {
    try { document.getElementById("inventory-typeselectboxid").disabled = disable; } catch (e) {}
    try { document.getElementById("inventory-typeselectboxaddid").disabled = disable } catch (e) {}
    try { document.getElementById("inventory-orphanselectboxaddid").disabled = disable; } catch (e) {}
    try { document.getElementById("inventory-typeselectboxeditid").disabled = disable; } catch (e) {}
    try { document.getElementById("inventory-typeselectboxdeleteid").disabled = disable; } catch (e) {}

    var visibility = "visible";
    if (disable)
      visibility = "hidden";

    try { document.getElementById("inventory-filesystemCreateButtonId").style.visibility = visibility; } catch (e) {}
    try { document.getElementById("inventory-rackCreateButtonId").style.visibility = visibility; } catch (e) {}
    try { document.getElementById("inventory-switchCreateButtonId").style.visibility = visibility; } catch (e) {}
    try { document.getElementById("inventory-powerswitchCreateButtonId").style.visibility = visibility; } catch (e) {}
    try { document.getElementById("inventory-serialCreateButtonId").style.visibility = visibility; } catch (e) {}
    try { document.getElementById("inventory-serviceprocessorCreateButtonId").style.visibility = visibility; } catch (e) {}
    try { document.getElementById("inventory-computerCreateButtonId").style.visibility = visibility; } catch (e) {}
  };

  /**
   * Handles a reply to an add, edit or delete element request, displaying error messages if the operation
   * failed.
   */
  this.handleAddEditDeleteElementReply = function handleAddEditDeleteElementReply()
  {
    if (me.addEditDeleteElementXmlHttpRequest.getReadyState() == 4)
    {
      if (me.addEditDeleteElementXmlHttpRequest.getStatus() == 200)
      {
	me.setDisableControls(false);
	me.hideLoadingDiv();
	me.clearCanvas();
	document.getElementById("inventory-typeselectboxaddid").selectedIndex = 0;
	document.getElementById("inventory-typeselectboxeditid").selectedIndex = 0;
	document.getElementById("inventory-typeselectboxdeleteid").selectedIndex = 0;
	document.getElementById("inventory-orphanselectboxaddid").selectedIndex = 0;

	var result = me.addEditDeleteElementXmlHttpRequest.getResponseXML().getElementsByTagName("inventory")[0].getElementsByTagName("result")[0];
	var operationType = auxiliary.hen.getAttributeValue(result, "operation");
	var elementID = auxiliary.hen.getAttributeValue(result, "elementid");
	var elementType = auxiliary.hen.getAttributeValue(result, "elementtype");
	var operationValue = auxiliary.hen.getAttributeValue(result, "value");
	
	if (operationType == "create")
	{
	  if (operationValue == "0")
	  {
	    // Add a new entry to the edit and delete boxes. 
	    var selectBox = document.getElementById("inventory-typeselectboxdeleteid");
	    selectBox[selectBox.options.length] = new Option(elementID, elementType);
	    var selectBox = document.getElementById("inventory-typeselectboxeditid");
	    selectBox[selectBox.options.length] = new Option(elementID, elementType);
	    alert("success! created " + elementID);
	  }
	  else
	    // In case of error, elementID contains the error's description
	    alert("error while creating new element: " + elementID)
	}
	else if (operationType == "edit")
	{
	  if (operationValue == "0")
	  {
	    alert("successfully edited " + elementID);
	  }
	  else
	    // In case of error, elementID contains the error's description
	    alert("error while editing element: " + elementID)
	}
	else if (operationType == "delete")
	{
	  if (operationValue == "0")
	  {
	    deleteSelectBoxOptionByText("inventory-typeselectboxeditid", elementID);
	    deleteSelectBoxOptionByText("inventory-typeselectboxdeleteid", elementID);
	    alert("successfully deleted " + elementID);
	  }
	  else
	    // In case of error, elementID contains the error's description
	    alert("error while deleting element: " + elementID)
	}
      }
    }
  };

  /** 
   * Asynchrounous request handler for Add Inventory select box. Populates the vendor and model select boxes.
   */
  this.handlePopulateVendorModelSelectBoxesReply = function handlePopulateVendorModelSelectBoxesReply()
  {
    if (me.populateVendorModelSelectBoxesRequest.getReadyState() == 4)
    {
      if (me.populateVendorModelSelectBoxesRequest.getStatus() == 200)
      {
	var vendors = me.populateVendorModelSelectBoxesRequest.getResponseXML().getElementsByTagName("inventory")[0].getElementsByTagName("vendor");
	var selectBox = document.getElementById("inventory-vendorid");
	if (selectBox == null)
	  return;
	selectBox.options.length = 0;
	selectBox[0] = new Option("please select...", "please select...");	

	supportedHardware = new Array();

	for (var i = 0; i < vendors.length; i++)
	{
	  var vendor = auxiliary.hen.getAttributeValue(vendors[i], "id");
	  selectBox[i + 1] = new Option(vendor, vendor);
	  var models = vendors[i].getElementsByTagName("model");
	  supportedHardware[vendor] = new Array();
	  for (var j = 0; j < models.length; j++)
	  {
	    var model = auxiliary.hen.getAttributeValue(models[j], "id");
	    supportedHardware[vendor].push(model);
	  }
	}
	selectBox[selectBox.options.length] = new Option("other...", "other...");
	me.countOutstandingReplies();
      }
    }
  };

  /** 
   * Asynchrounous request handler for Add Inventory select box. Populates the service processor,
   * powerswitch, serial and rack name select boxes, and saves information regarding which ports/units
   * are free on these for later use.
   */
  this.handlePopulateSelectBoxesReply = function handlePopulateSelectBoxesReply()
  {
    if (me.populateSelectBoxesRequest.getReadyState() == 4)
    {
      if (me.populateSelectBoxesRequest.getStatus() == 200)
      {
	var xmlDoc = me.populateSelectBoxesRequest.getResponseXML();
	var serviceProcessors = xmlDoc.getElementsByTagName("inventory")[0].getElementsByTagName("serviceprocessor");
	var powerSwitches = xmlDoc.getElementsByTagName("inventory")[0].getElementsByTagName("powerswitch");
	var serialServers = xmlDoc.getElementsByTagName("inventory")[0].getElementsByTagName("serial");
	var racks = xmlDoc.getElementsByTagName("inventory")[0].getElementsByTagName("rack");

	unassignedPorts = new Array();

	// Parse service processor information
	var serviceProcessorSelectBox = document.getElementById("inventory-serviceprocessorid");
	if (serviceProcessorSelectBox != null)
	{
	  serviceProcessorSelectBox.options.length = 0;
	  serviceProcessorSelectBox[0] = new Option("please select...", "please select...");
	  serviceProcessorSelectBox[1] = new Option("none", "none");
	  for (var i = 0; i < serviceProcessors.length; i++)
	  {
	    var serviceProcessorID = auxiliary.hen.getAttributeValue(serviceProcessors[i], "id");
	    serviceProcessorSelectBox[i + 2] = new Option(serviceProcessorID, serviceProcessorID);
	  }
	}

	// Parse power switch information
	var powerSwitchSelectBox = document.getElementById("inventory-powerswitchid");
	if (powerSwitchSelectBox != null)
	{
	  powerSwitchSelectBox.options.length = 0;
	  powerSwitchSelectBox[0] = new Option("please select...", "please select...");
	  powerSwitchSelectBox[1] = new Option("none", "none");
	  for (var i = 0; i < powerSwitches.length; i++)
	  {
	    var powerSwitchID = auxiliary.hen.getAttributeValue(powerSwitches[i], "id");
	    powerSwitchSelectBox[i + 2] = new Option(powerSwitchID, powerSwitchID);
	    unassignedPorts[powerSwitchID] = new Array();
	    var ports = powerSwitches[i].getElementsByTagName("port");
	    
	    // Save the port numbers for when the user selects a power switch
	    for (var j = 0; j < ports.length; j++)
	      unassignedPorts[powerSwitchID].push(auxiliary.hen.getAttributeValue(ports[j], "number"));
	  }
	}

	// Parse serial server information
	var serialServerSelectBox = document.getElementById("inventory-serialid");
	if (serialServerSelectBox != null)
	{
	  serialServerSelectBox.options.length = 0;
	  serialServerSelectBox[0] = new Option("please select...", "please select...");
	  serialServerSelectBox[1] = new Option("none", "none");
	  for (var i = 0; i < serialServers.length; i++)
	  {
	    var serialServerID = auxiliary.hen.getAttributeValue(serialServers[i], "id");
	    serialServerSelectBox[i + 2] = new Option(serialServerID, serialServerID);
	    unassignedPorts[serialServerID] = new Array();
	    var ports = serialServers[i].getElementsByTagName("port");
	    
	    // Save the port numbers for when the user selects a serial server
	    for (var j = 0; j < ports.length; j++)
	      unassignedPorts[serialServerID].push(auxiliary.hen.getAttributeValue(ports[j], "number"));
	  }
	}

	// Parse rack information
	var rackSelectBox = document.getElementById("inventory-racknameid");
	if (rackSelectBox != null)
	{
	  rackSelectBox.options.length = 0;
	  rackSelectBox[0] = new Option("please select...", "please select...");
	  for (var i = 0; i < racks.length; i++)
	  {
	    var rackID = auxiliary.hen.getAttributeValue(racks[i], "id");
	    rackSelectBox[i + 1] = new Option(rackID, rackID);
	    unassignedPorts[rackID] = new Array();
	    var units = racks[i].getElementsByTagName("unit");

	    // Save the rack unit numbers for when the user selects a rack 
	    for (var j = 0; j < units.length; j++)
	      unassignedPorts[rackID].push(auxiliary.hen.getAttributeValue(units[j], "number"));
	  }
	}
	me.countOutstandingReplies();
      }
    }
  };

  /**
   * Asynchronous reply handler for orpahns request. This function
   * displays populates the select box in the add inventory section of the control panel.
   */
  this.handleNodeTypesReply = function handleNodeTypesReply()
  {
    if (me.getNodeTypesXmlHttp.readyState == 4)
    {
      if (me.getNodeTypesXmlHttp.status == 200)
      {
	var xmlDoc = me.getNodeTypesXmlHttp.responseXML;
	var types = xmlDoc.getElementsByTagName("inventory")[0].getElementsByTagName("elementtype");
	var selectBox = document.getElementById("inventory-orphantypesid");

	selectBox.options.length = 0;
	selectBox.options[0] = new Option("select type...", "select type...");
	for (var i = 0; i < types.length; i++)
        {
	  var type = auxiliary.hen.getAttributeValue(types[i], "value");
	  selectBox.options[i + 1] = new Option(type, type);
	}
      }
    }
  };

  /**
   * Asynchronous reply handler for orpahns request. This function
   * displays populates the select box in the add inventory section of the control panel.
   */
  this.handleOrphansReply = function handleOrphansReply()
  {
    if (me.getOrphansXmlHttp.readyState == 4)
    {
      if (me.getOrphansXmlHttp.status == 200)
      {
	var xmlDoc = me.getOrphansXmlHttp.responseXML;
	var nodes = xmlDoc.getElementsByTagName("inventory")[0].getElementsByTagName("node");
	var selectBox = document.getElementById("inventory-orphanselectboxaddid");

	selectBox.options.length = 0;
	selectBox.options[0] = new Option("select orphan...", "select orphan...");
	for (var i = 1; i <= nodes.length; i++)
        {
	  var newMACAddress = auxiliary.hen.getAttributeValue(nodes[i - 1], "mac");
	  selectBox.options[i] = new Option(newMACAddress, newMACAddress);
	}
	me.finishInitLoad();
      }
    }
  };

  /**
   * Asynchronous reply handler for brief description of all elements in the testbed request. This function
   * displays a table with all the received information.
   */
  this.handleInventoryAllReply = function handleInventoryAllReply()
  {
    if (me.getAllElementsXmlHttp.readyState == 4)
    {
      if (me.getAllElementsXmlHttp.status == 200)
      {
	me.hideLoadingDiv();
	me.setDisableControls(false);
	document.getElementById("inventory-typeselectboxid").selectedIndex = 0;
	var xmlDoc = me.getAllElementsXmlHttp.responseXML;
	var elementTypes = xmlDoc.getElementsByTagName("inventory")[0].getElementsByTagName("elementtype");
	var canvas = document.getElementById("inventory-canvasid");
	me.clearCanvas();

	for (var i = 0; i < elementTypes.length; i++)
	{
	  var elementType = auxiliary.hen.getAttributeValue(elementTypes[i], "type");
	  var elements = elementTypes[i].getElementsByTagName("element");

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
	  titleTableLabel.setAttribute("class", "inventory-tabletitlelabel");
	  titleTableLabel.appendChild(document.createTextNode(elementType));

	  var spacerRow = document.createElement("tr");
	  titleTable.appendChild(spacerRow);
	  var spacerCell = document.createElement("td");
	  spacerCell.setAttribute("align", "center");
	  spacerRow.appendChild(spacerCell);
	  var img = document.createElement("img");
	  img.src = "images/transparent.gif";
	  img.setAttribute("height", "10");
	  spacerCell.appendChild(img);
	  canvas.appendChild(titleTable);

	  var table = document.createElement("table");
	  table.setAttribute("class", "inventory-table");
	  table.setAttribute("width", me.CANVAS_WIDTH);
	  canvas.appendChild(table);

	  var headingsRow = document.createElement("tr");
	  headingsRow.setAttribute("class", "inventory-row");
	  table.appendChild(headingsRow);
	  try
	  {
	    var attributes = elements[0].getElementsByTagName("attribute");

	    for (var j = 0; j < attributes.length; j++)
	    {
	      var headingTitle = auxiliary.hen.getAttributeValue(attributes[j], "name");
	      var headingCell = document.createElement("td");
	      headingCell.setAttribute("class", "inventory-cell");
	      headingCell.setAttribute("align", "center");
	      headingsRow.appendChild(headingCell);
	      var headingLabel = document.createElement("label");
	      headingLabel.setAttribute("class", "inventory-boldlabel");
	      headingCell.appendChild(headingLabel);
	      headingLabel.appendChild(document.createTextNode(headingTitle));
	    }
	    }
	    catch (e) {}

	  try
	  {
	    for (var j = 0; j < elements.length; j++)
	    {
	      var elementStatus = auxiliary.hen.getAttributeValue(elements[j], "status");

	      var row = document.createElement("tr");
	      row.setAttribute("class", "inventory-row");
	      row.style.backgroundColor = me.statusColors[elementStatus];
	      table.appendChild(row);
	      var attributes = elements[j].getElementsByTagName("attribute");
	      for (var k = 0; k < attributes.length; k++)
	      {
		var attributeValue = auxiliary.hen.getAttributeValue(attributes[k], "value");
		var cell = document.createElement("td");
		cell.setAttribute("class", "inventory-cell");
		cell.setAttribute("align", "center");
		cell.style.backgroundColor = me.statusColors[elementStatus];
		row.appendChild(cell);

		if (k == 0)
		{
		  var link = document.createElement("a");
		  link.setAttribute("id", "inventory-clickdiv" + attributeValue);
		  link.onclick = me.elementIDClick;
		  cell.appendChild(link);
		  var label = document.createElement("label");
		  label.setAttribute("class", "inventory-linklabel");
		  label.setAttribute("id", "inventory-clickdiv" + attributeValue);
		  link.appendChild(label);
		  label.appendChild(document.createTextNode(attributeValue));
		}
		else
		{
		  var label = document.createElement("label");
		  label.setAttribute("class", "inventory-normallabel");
		  cell.appendChild(label);
		  label.appendChild(document.createTextNode(attributeValue));
		}
	      }
	    }
	  }
	  catch (e) {}
	}
      }
    }
  };

  /**
   * Asynchronous reply handler for brief description of all elements of one type request. This function
   * displays a table with all the received information.
   */
  this.handleInventoryTypeDescriptionReply = function handleInventoryTypeDescriptionReply()
  {
    if (me.getTypeDescriptionXmlHttp.readyState == 4)
    {
      if (me.getTypeDescriptionXmlHttp.status == 200)
      {
	me.hideLoadingDiv();
	me.setDisableControls(false);
	document.getElementById("inventory-typeselectboxid").selectedIndex = 0;
	var xmlDoc = me.getTypeDescriptionXmlHttp.responseXML;
	var elements = xmlDoc.getElementsByTagName("inventory")[0].getElementsByTagName("element");

	// Create the table on the canvas, but first clear the canvas of previous table
	var canvas = document.getElementById("inventory-canvasid");
	me.clearCanvas();
	var table = document.createElement("table");
	table.setAttribute("class", "inventory-table");
	table.setAttribute("width", me.CANVAS_WIDTH);
	canvas.appendChild(table);

	var headingsRow = document.createElement("tr");
	headingsRow.setAttribute("class", "inventory-row");
	table.appendChild(headingsRow);
	var attributes = elements[0].getElementsByTagName("attribute");
	for (var i = 0; i < attributes.length; i++)
	{
	  var headingTitle = auxiliary.hen.getAttributeValue(attributes[i], "name");
	  var headingCell = document.createElement("td");
	  headingCell.setAttribute("class", "inventory-cell");
	  headingCell.setAttribute("align", "center");
	  headingsRow.appendChild(headingCell);
	  var headingLabel = document.createElement("label");
	  headingLabel.setAttribute("class", "inventory-boldlabel");
	  headingCell.appendChild(headingLabel);
	  headingLabel.appendChild(document.createTextNode(headingTitle));
	}

	for (var i = 0; i < elements.length; i++)
	{
	  var elementStatus = auxiliary.hen.getAttributeValue(elements[i], "status");
	  var row = document.createElement("tr");
	  row.setAttribute("class", "inventory-row");
	  row.style.backgroundColor = me.statusColors[elementStatus];
	  table.appendChild(row);
	  var attributes = elements[i].getElementsByTagName("attribute");
	  for (var j = 0; j < attributes.length; j++)
	  {
	    var attributeValue = auxiliary.hen.getAttributeValue(attributes[j], "value");
	    var cell = document.createElement("td");
	    cell.setAttribute("class", "inventory-cell");
	    cell.setAttribute("align", "center");
	    cell.style.backgroundColor = me.statusColors[elementStatus];
	    row.appendChild(cell);
	    if (j == 0)
	    {
	      var link = document.createElement("a");
	      link.setAttribute("id", "inventory-clickdiv" + attributeValue);
	      link.onclick = me.elementIDClick;
	      cell.appendChild(link);
	      var label = document.createElement("label");
	      label.setAttribute("class", "inventory-linklabel");
	      label.setAttribute("id", "inventory-clickdiv" + attributeValue);
	      link.appendChild(label);
	      label.appendChild(document.createTextNode(attributeValue));
	    }
	    else
	    {
	      var label = document.createElement("label");
	      label.setAttribute("class", "inventory-normallabel");
	      cell.appendChild(label);
	      label.appendChild(document.createTextNode(attributeValue));
	    }
	  }
	}
      }
    }
  };

  /**
   * Asynchronous reply handler for full description of an element request. This function
   * displays a table with all the received information.
   */
  this.handleInventoryElementReply = function handleInventoryElementReply()
  {
    if (me.getElementFullInfoXmlHttp.readyState == 4)
    {
      if (me.getElementFullInfoXmlHttp.status == 200)
      {
	var xmlDoc = me.getElementFullInfoXmlHttp.responseXML;
	var inventory = xmlDoc.getElementsByTagName("inventory")[0];
	var items = inventory.getElementsByTagName("item");

	// Create the table on the canvas, but first clear the canvas of previous table
	var canvas = document.getElementById("inventory-canvasid");
	me.clearCanvas();
	var table = document.createElement("table");
	table.setAttribute("class", "inventory-table");
	table.setAttribute("width", me.CANVAS_WIDTH);
	canvas.appendChild(table);

	for (var i = 0; i < items.length; i++)
	{
	  // For some reason the xml contains <item/> tags with nothing in between them
	  // The try/catch prevents errors arising from them.
	  try
	  {
	    var value = items[i].childNodes[0].nodeValue;
	    var row = document.createElement("tr");
	    table.appendChild(row);
	    var cell = document.createElement("td");
	    row.appendChild(cell);
	    var label = document.createElement("label");
	    cell.appendChild(label);
	    label.setAttribute("class", "inventory-normallabel");	
	    label.appendChild(document.createTextNode(value));
	  }
	  catch(e) {}
	}
      }
    }
  };

  /**
   * Asynchronous reply handler for all types currently on the testbed request. This function
   * populates the View inventory select box
   */
  this.handleInventoryReply = function handleInventoryReply()
  {
    if (me.getTypesXmlHttp.readyState == 4)
    {
      if (me.getTypesXmlHttp.status == 200)
      {
	var xmlDoc = me.getTypesXmlHttp.responseXML;
	var types = xmlDoc.getElementsByTagName("inventory")[0];
	var nodeTypes = types.getElementsByTagName("nodetype");
	var infrastructureTypes = types.getElementsByTagName("infrastructuretype");
	var fileNodeTypes = types.getElementsByTagName("filenodetype");

	var select = document.getElementById("inventory-typeselectboxid");
	var count = 2;
	select.options[0] = new Option("select type...", "select type...");
	select.options[1] = new Option("all", "all");	 

	// Populate nodes
	for (var i = 0; i < nodeTypes.length; i++)
	{
	  var nodeType = auxiliary.hen.getAttributeValue(nodeTypes[i], "value");
	  select.options[i + 2] = new Option(nodeType, nodeType);
	}
	// Populate infrastructures
	for (var i = 0; i < infrastructureTypes.length; i++)
	{
	  var infrastructureType =  auxiliary.hen.getAttributeValue(infrastructureTypes[i], "value");
	  select.options[i + nodeTypes.length + 2] = new Option(infrastructureType, infrastructureType);
	}	
	// Populate file nodes
	for (var i = 0; i < fileNodeTypes.length; i++)
	{
	  var fileNodeType =  auxiliary.hen.getAttributeValue(fileNodeTypes[i], "value");
	  select.options[i + nodeTypes.length + infrastructureTypes.length + 2] = new Option(fileNodeType, fileNodeType);
	}
	me.finishInitLoad();
      }
    }    
  };

  /**
   * Asynchronous reply handler for all types supported by the testbed request. This function
   * populates the Add Inventory select box
   */
  this.handleInventoryAllTypesReply = function handleInventoryAllTypesReply()
  {
    if (me.getSupportedTypesXmlHttp.readyState == 4)
    {
      if (me.getSupportedTypesXmlHttp.status == 200)
      {
	var xmlDoc = me.getSupportedTypesXmlHttp.responseXML;
	var types = xmlDoc.getElementsByTagName("inventory")[0];
	var elementTypes = types.getElementsByTagName("elementtype");

	var selectBox = document.getElementById("inventory-typeselectboxaddid");

	selectBox.options[0] = new Option("select type...", "select type...");
	for (var i = 0; i < elementTypes.length; i++)
	{
	  var elementType = auxiliary.hen.getAttributeValue(elementTypes[i], "value");
	  selectBox.options[i + 1] = new Option(elementType, elementType);
	}
	me.finishInitLoad();
      }
    }
  };

  /**
   * Asynchronous reply handler for ids of all elements in the testbed. This function
   * populates the Delete Inventory select box
   */
  this.handleInventoryAllElementsReply = function handleInventoryAllElementsReply()
  {
    if (me.getAllElementIDsXmlHttp.readyState == 4)
    {
      if (me.getAllElementIDsXmlHttp.status == 200)
      {
	var xmlDoc = me.getAllElementIDsXmlHttp.responseXML;
	var elements = xmlDoc.getElementsByTagName("inventory")[0];
	var elementIDs = elements.getElementsByTagName("element");

	var deleteSelectBox = document.getElementById("inventory-typeselectboxdeleteid");
	deleteSelectBox.options[0] = new Option("select element...", "select element...");
	var editSelectBox = document.getElementById("inventory-typeselectboxeditid");
	editSelectBox.options[0] = new Option("select element...", "select element...");
	for (var i = 1; i < elementIDs.length; i++)
	{
	  var elementID = auxiliary.hen.getAttributeValue(elementIDs[i], "id");
	  var elementType = auxiliary.hen.getAttributeValue(elementIDs[i], "type");
	  deleteSelectBox.options[i] = new Option(elementID, elementType);
	  editSelectBox.options[i] = new Option(elementID, elementType);
	}
	me.finishInitLoad();
      }
    }
  };

  /**
   * Asynchronous reply handler for all statuses allowed for a given element. This function
   * populates the status select box
   */
  this.handleStatusesReply = function handleStatusesReply()
  {
    if (me.getTypeStatusesXmlHttp.readyState == 4)
    {
      if (me.getTypeStatusesXmlHttp.status == 200)
      {
	var selectBox = document.getElementById(me.activeStatusSelectBoxID);
	var xmlDoc = me.getTypeStatusesXmlHttp.responseXML;
	var statuses = xmlDoc.getElementsByTagName("inventory")[0].getElementsByTagName("status");

	selectBox[0] = new Option("please select...", "please select...");
	for (var i = 0; i < statuses.length; i++)
	{
	  var status = auxiliary.hen.getAttributeValue(statuses[i], "id");
	  selectBox[i + 1] = new Option(status, status);
	}
	me.countOutstandingReplies();
      }
    }
  };

  /**
   * Asynchronous reply handler for the current information for an element's editable fields. This function
   * populates all of the input fields of the element with the returned information.
   */
  this.handleEditReply = function handleEditReply()
  {
    if (me.getElementEditInfoXmlHttp.readyState == 4)
    {
      if (me.getElementEditInfoXmlHttp.status == 200)
      {
	var xmlDoc = me.getElementEditInfoXmlHttp.responseXML;
	var element = null;
	try
	{
	  var element = xmlDoc.getElementsByTagName("inventory")[0].getElementsByTagName("element")[0];
	}
	catch (e) 
	{
	  alert("could not retrieve element's information, back-end returned error or incomplete xml");
	  me.hideLoadingDiv();
	  me.setDisableControls(false);
	  document.getElementById("inventory-typeselectboxeditid").selectedIndex = 0;
	  return;
	}
	var elementType = auxiliary.hen.getAttributeValue(element, "type");
	var properties = element.getElementsByTagName("property");
	var attributes = element.getElementsByTagName("attribute");

	if (elementType == "kernel" || elementType == "loader")
	  elementType = "filesystem";

	me.populateFields(elementType, properties, attributes);

	// Populate attributes text area, which is common to all elements
	var textArea = document.getElementById("inventory-AttributeListId");
	for (var i = 0; i < attributes.length; i++)
	{
	  var attributeName = auxiliary.hen.getAttributeValue(attributes[i], "name");
	  var attributeValue = auxiliary.hen.getAttributeValue(attributes[i], "value");
	  textArea.value += attributeName + " = " + attributeValue + "\n";
	}
	me.setDisableControls(false);
	me.hideLoadingDiv();
      }
    }
  };


} // end class InventoryTab

// Set up inheritance
components.inventory.inventory.InventoryTab.prototype = new auxiliary.hen.Tab();
