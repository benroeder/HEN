//**********************************************************************************
//**********************************************************************************
// Implements the components.experiment.canvas namespace
//
// CLASSES
// --------------------------------------------
// SVGCanvas    Displays and manages the SVG canvas in the "Experiment" tab
//
//
// $Id: canvas.js 181 2006-08-11 09:45:50Z munlee $ 
//**********************************************************************************
//**********************************************************************************
top.Namespace("components.experiment.canvas");
top.Import("auxiliary.draw", ".", "/");


  
// ***************************************************
// ***** CLASS: SVGCanvas ****************************
// ***************************************************
top.components.experiment.canvas.SVGCanvas = function()
{
  // Necessary to keep reference to 'this' for event handlers 
  var me = this;
  // Used to create various form elements 
  this.formHelper = new top.auxiliary.draw.FormHelper();
  // The asynchronous request object 
  this.xhr = null;
  // Used as the parent for the node info panel
  this.tabMainDiv = null; 
  // Used to tell the tab manager about divs that need manual show/hide
  this.visibilityDivs = null;

  this.SVGDocument = null;
  this.SVGRoot = null;

  this.BackDrop = null;
  this.DragTarget = null;

  this.CursorX = null;
  this.CursorY = null;

  this.NodeCX = 30;
  this.NodeCY = 30;
  this.NodeRadius = 18;
  this.InterfaceRadius = 4;

  this.OutOfBounds = false;

  this.SnapBackToPointX = 0;
  this.SnapBackToPointY = 0;
  this.SVGNS = "http://www.w3.org/2000/svg";

  this.objectToDelete = null;  
  this.valueCounter = 0;
  this.nodeCounter = 0;

  this.writeConfigXHR = null;
  this.filelistXHR;

  this.nodeOptions = null;


  this.doRequest = function doRequest(value) 
  {
    me.xhr = new XMLHttpRequest();
    me.xhr.onreadystatechange = me.handleNodePropertiesReply;
    me.xhr.open("GET", "/cgi-bin/gui/components/experiment/vlancgi.py?id=" + value, true);
    me.xhr.send(null);
  };
    
        
          
  this.handleNodePropertiesReply = function handleNodePropertiesReply() 
  {
    if (me.xhr.readyState == 4) 
    {
      if (me.xhr.status == 200) 
      {
        var xmlDoc = me.xhr.responseXML;     
        var nodeTag = xmlDoc.getElementsByTagName("node")[0];

        var nodeTable = top.document.getElementById("nodeTableId");
        nodeTable.replaceChild(document.createTextNode(nodeTag.getAttribute("ident")), nodeTable.firstChild);

        var motherboardTable = top.document.getElementById("motherboardTableId");
        motherboardTable.replaceChild(document.createTextNode(nodeTag.getAttribute("motherboard")), motherboardTable.firstChild);

        var cpuTypeTable = top.document.getElementById("cputypeTableId");
        cpuTypeTable.replaceChild(document.createTextNode(nodeTag.getAttribute("cputype")), cpuTypeTable.firstChild);

        var cpuSpeedTable = top.document.getElementById("cpuspeedTableId");
        cpuSpeedTable.replaceChild(document.createTextNode(nodeTag.getAttribute("cpuspeed")), cpuSpeedTable.firstChild);

        var multiProcessorTable = top.document.getElementById("multiprocessorTableId");
        multiProcessorTable.replaceChild(document.createTextNode(nodeTag.getAttribute("multiproc")), multiProcessorTable.firstChild);

        var memoryTable = top.document.getElementById("memoryTableId");
        memoryTable.replaceChild(document.createTextNode(nodeTag.getAttribute("memory")), memoryTable.firstChild);

        me.clearInterfaceTable();

        var nodeInfoTable = top.document.getElementById("nodeInfoTableId");
        var interfaceTags = xmlDoc.getElementsByTagName("interface");

        for (var i = 0; i < interfaceTags.length; i++) 
        {
          var mac = interfaceTags[i].getAttribute("mac");
          me.interfaceTableEntry(i, "mac", mac);
          var model = interfaceTags[i].getAttribute("model");
          me.interfaceTableEntry(i, "model", model);
          var port = interfaceTags[i].getAttribute("port");
          me.interfaceTableEntry(i, "port", port);
          var sw = interfaceTags[i].getAttribute("switch");
          me.interfaceTableEntry(i, "switch", sw);

          var ip = interfaceTags[i].getAttribute("ip");
          me.interfaceTableEntry(i, "ip", ip);
        }

        if (nodeInfoTable.style.visibility == "hidden")
          nodeInfoTable.style.visibility = "visible";

        // enable the mouse click handler
        var targetElement = top.document.getElementById("nodeTypeInputFormId");
        targetElement.onclick = top.doCreateNode;
	
	top.document.getElementById("experiment-createNodeButtonId").style.visibility = "visible";
      } // if (me.xhr.status == 200) {
    }
  }; 


  
  this.clearInterfaceTable = function clearInterfaceTable() 
  {
    var tbody = top.document.getElementById("nodeInfoTableTbody");
    while (true) 
    {
      var child = tbody.lastChild;
      if (child.getAttribute("class") == "interfaceClass" ||
          child.getAttribute("class") == "interfaceHeaderClass") 
      {
        tbody.removeChild(child);
      } 
      else 
      {      
        break;
      }
    }
  };
  
  
  
  this.doCreateNode = function doCreateNode() 
  {
    var nameid = top.document.forms.nodeNameDropdownFormName.nodeNameDropdownSelectName.value;

    if (!me.validateNodeId(nameid)) 
    {
      alert("Node ID already exist!");
      return 0;
    } 

    var svgDoc = me.SVGDocument.getElementById("svgDoc");
    var nodeGroup = me.SVGDocument.createElementNS(me.SVGNS, "g");
    
    nodeGroup.setAttributeNS(null, "id", "NodeGroup" + me.nodeCounter);
    me.nodeCounter++;
    svgDoc.appendChild(nodeGroup)

    ///////////////////////////////////////////////////////////////////////////////
    // create SVG node object on the canvas
    ///////////////////////////////////////////////////////////////////////////////
    var circle = me.SVGDocument.createElementNS(me.SVGNS, "circle");
    nodeGroup.appendChild(circle);
    circle.setAttributeNS(null, "id", nameid);
    circle.setAttributeNS(null, "type", "computer");
    circle.setAttributeNS(null, "cx", me.NodeCX);
    circle.setAttributeNS(null, "cy", me.NodeCY);
    circle.setAttributeNS(null, "grabX", "");
    circle.setAttributeNS(null, "grabY", "");
    circle.setAttributeNS(null, "r", me.NodeRadius);
    circle.setAttributeNS(null, "fill", "blue");
    circle.setAttributeNS(null, "stroke", "black");

    ///////////////////////////////////////////////////////////////////////////////
    // custom attributes
    ///////////////////////////////////////////////////////////////////////////////
    var mobo = top.document.getElementById("motherboardTableId");
    var cputype = top.document.getElementById("cputypeTableId");
    var cpuspeed = top.document.getElementById("cpuspeedTableId");
    var mpu = top.document.getElementById("multiprocessorTableId");
    var memory = top.document.getElementById("memoryTableId");

    circle.setAttributeNS(null, "motherboard", mobo.firstChild.nodeValue);
    circle.setAttributeNS(null, "cputype", cputype.firstChild.nodeValue);
    circle.setAttributeNS(null, "cpuspeed", cpuspeed.firstChild.nodeValue);
    circle.setAttributeNS(null, "mpu", mpu.firstChild.nodeValue);
    circle.setAttributeNS(null, "memory", memory.firstChild.nodeValue);


    circle.setAttributeNS(null, "loader", top.document.getElementById("loaderForm").value);
    circle.setAttributeNS(null, "filesystem", top.document.getElementById("filesystemForm").value);
    circle.setAttributeNS(null, "kernel", top.document.getElementById("kernelForm").value);

    circle.addEventListener("mouseover", me.hover, false);

    ///////////////////////////////////////////////////////////////////////////////
    // get all interface entries
    ///////////////////////////////////////////////////////////////////////////////
    var portsArray;
    var nodeInfoTable = top.document.getElementById("nodeInfoTableId");
    var ths = nodeInfoTable.getElementsByTagName("th");
    var ports = new Array();
    for (var i = 0; i < ths.length; i++) 
    {
      if (ths[i].getAttributeNS(null, "class") == "interfaceHeaderClass") 
      {
        ports.push(ths[i]);
      }
    }

    portsArray = ports;

    ///////////////////////////////////////////////////////////////////////////////
    // create SVG interface object on the canvas
    ///////////////////////////////////////////////////////////////////////////////
    var angle = 30.0 * Math.PI / 180.0;
    for (var i = 0; i < portsArray.length; i++) 
    {
      circle = me.SVGDocument.createElementNS(me.SVGNS, "circle");
      nodeGroup.appendChild(circle);
      circle.setAttributeNS(null, "id", nameid + "interface" + i);
      //alert("in canvas::doCreateNode: " + nameid + "interface" + i);
      circle.setAttributeNS(null, "type", "experimental");
      circle.setAttributeNS(null, "r", me.InterfaceRadius);
      circle.setAttributeNS(null, "fill", "red");
      circle.setAttributeNS(null, "stroke", "black");

      ///////////////////////////////////////////////////////////////////////////////
      // custom attributes
      ///////////////////////////////////////////////////////////////////////////////
      var mac = top.document.getElementById("Interface" + i + "mac");
      var model = top.document.getElementById("Interface" + i + "model");
      var port = top.document.getElementById("Interface" + i + "port");
      var sw = top.document.getElementById("Interface" + i + "switch");

      // since the interface headers are always cleared when a node is
      // selected from the drop-box, this will always return the correct
      // interfaces.
      var formObject = top.document.getElementById("interface" + i + "ipInputFormId");
      var cidr = formObject.value;
      var ip = "";
      var subnet = "";

      if (cidr != "") 
      {
        // split the cidr address into ip/network parts.
        var cidrArray = cidr.split("/");

        for (var r = 0; r < cidrArray.length; r++)
          if (isNaN(parseInt(cidrArray[r]))) 
          {
            me.doClearCanvas();
            alert(cidr + " is incorrect format. It has to be in x.x.x.x/y format.");
            return;
          }

        ip = cidrArray[0];
        var network = cidrArray[1];;
        if (network == null) 
        {
          // remove all objects from the canvas if the network format is incorrect
          me.doClearCanvas();
          alert(cidr + " is incorrect format. It has to be in x.x.x.x/y format.");
          return
        }
        subnet = me.getSubnetFromCIDR(network);
      }

      circle.setAttributeNS(null, "mac", mac.lastChild.lastChild.nodeValue);
      circle.setAttributeNS(null, "model", model.lastChild.lastChild.nodeValue);
      circle.setAttributeNS(null, "port", port.lastChild.lastChild.nodeValue);
      circle.setAttributeNS(null, "switch", sw.lastChild.lastChild.nodeValue);
      circle.setAttributeNS(null, "ip", ip);
      circle.setAttributeNS(null, "subnet", subnet);
      circle.setAttributeNS(null, "edgeId", "");
      circle.setAttributeNS(null, "vlan", "");

      circle.addEventListener("mouseover", me.hover, false);

    
      var temp2X = Math.cos(Math.PI * 4 * i * angle / 8);
      var xval = me.NodeCX + (me.NodeRadius - me.InterfaceRadius) * temp2X;

      if (temp2X == 1)
        xval--;
      
      var yval = me.NodeCY + (me.NodeRadius - me.InterfaceRadius) * Math.sin(Math.PI * 4 * i * angle / 8);

      circle.setAttributeNS(null, "cx", xval);
      circle.setAttributeNS(null, "cy", yval);
      circle.setAttributeNS(null, "grabX", "");
      circle.setAttributeNS(null, "grabY", "");
    }

    // remove this selection from the drop down box
    var selectBox = top.document.forms.nodeNameDropdownFormName.nodeNameDropdownSelectName;
    selectBox.options[selectBox.selectedIndex] = null;

    if (selectBox.options.length == 0) 
    {
      var element = top.document.getElementById("nodeInfoTableId");
      element.style.visibility = "hidden";
    } 
    else 
    {
      me.doRequest(selectBox.options[0].value);
    }

    // refresh the nodes in the 'start node' drop-box
    selectBox = top.document.forms.edgeInputForm.startNodeIDName;
    selectBox.options[selectBox.options.length] = new Option(nameid, nameid);
    top.getNodeInterfaceCount(nameid);

    // refresh the nodes in the 'end node' drop-box
    selectBox = top.document.forms.edgeInputForm.endNodeIDName;
    selectBox.options[selectBox.options.length] = new Option(nameid, nameid);
    top.getNodeInterfaceCount(nameid);


    // disable the mouse click handler
    var targetElement = top.document.getElementById("nodeTypeInputFormId");
    targetElement.onclick = null;    
    
  };



  this.getSubnetFromCIDR = function getSubnetFromCIDR(network) 
  {
    var subnet = "";
    var binString = "";
    for (var i = 0; i < network; i++) 
    {
      binString += "1";
    }
    var remainingBits = 32 - network;

    for (var i = 0; i < remainingBits; i++) 
    {
      binString += "0";
    }

    for (var j = 0; j < binString.length; j += 8) 
    {
      var octet = binString.substring(j, j + 8);
      subnet += parseInt(octet, 2);
      subnet += ".";
    }
    subnet = subnet.substring(0, subnet.length - 1);
    return subnet;
  };
  

  
  this.hover = function hover(evt) 
  {
    // stores the id of the object to be deleted
    me.objectToDelete = evt.target.id;
    me.toggleNodeInfoWindow(evt);
  };



  this.isWithinBounds = function isWithinBounds() 
  {
    var icx = parseInt(me.DragTarget.getAttributeNS(null, "cx"));
    var icy = parseInt(me.DragTarget.getAttributeNS(null, "cy"));
    var ir = parseInt(me.DragTarget.getAttributeNS(null, "r"));
    var ncx;
    var ncy;
    var nr;

    var nodes = me.DragTarget.parentNode.childNodes;
    for (var i = 0; i < nodes.length; i++) 
    {
      if (nodes[i].getAttributeNS(null, "type") == "computer") 
      {
        ncx = parseInt(nodes[i].getAttribute("cx"));
        ncy = parseInt(nodes[i].getAttribute("cy"));
        nr = parseInt(nodes[i].getAttribute("r"));
      }
    }

    if ((ncx + nr > icx + ir) &&
        (ncx - nr < icx - ir) &&
        (ncy + nr > icy + ir) &&
        (ncy - nr < icy - ir)) 
    {
      return true;
    } 
    else 
    {
      return false;
    }
  }; 


  this.createNodeInfoWindow = function createNodeInfoWindow(evt) 
  {
    if (top && top.document) 
    {
      var propMenu = top.document.getElementById(evt.target.id + "propMenuId");
      if (propMenu) 
      {
        propMenu.style.visibility = "visible";
      } 
      else 
      {
        me.drawNewPropMenu(evt);
      }
    }
    
    return evt.target.id;
  };



  this.drawNewPropMenu = function drawNewPropMenu(evt) 
  {
    var targetElement = evt.target;

    // When calling from an SVG namespace, we'll need to explicitly
    // specify a different namespace.
    var propMenuDiv = document.createElementNS(me.formHelper.XHTMLNS, "div");
    me.visibilityDivs.push(propMenuDiv);
    me.tabMainDiv.appendChild(propMenuDiv);
    propMenuDiv.setAttribute("id", evt.target.id + "propMenuId");
    propMenuDiv.setAttribute("class", "experiment-nodeinfodivpanel");

    var propTable = document.createElementNS(me.formHelper.XHTMLNS, "table");
    propMenuDiv.appendChild(propTable);
    propTable.setAttribute("border", "0");
    propTable.setAttribute("width", "200px");
    propTable.setAttribute("id", "propTableId");
    propTable.setAttribute("name", "propTableName");

    if (targetElement.getAttributeNS(null, "type") == "computer") 
    {
      var id = targetElement.getAttribute("id");
      var mobo = targetElement.getAttribute("motherboard");
      var cputype = targetElement.getAttribute("cputype");
      var cpuspeed = targetElement.getAttribute("cpuspeed");
      var mpu = targetElement.getAttribute("mpu");
      var memory = targetElement.getAttribute("memory");

      // Node type property
      var td = document.createElementNS(me.formHelper.XHTMLNS, "td");
      propTable.appendChild(td);
      td.appendChild(me.createTableEntry("Node ID", "NodeIdInfoWindow", "NodeIdPropMenuClass", id));
      td.appendChild(me.createTableEntry("Motherboard", "MotherboardInfoWindow", "MotherboardPropMenuClass", mobo));
      td.appendChild(me.createTableEntry("CPU Type", "CpuTypeInfoWindow", "CPUTypePropMenuClass", cputype));
      td.appendChild(me.createTableEntry("CPU Speed", "CpuSpeedInfoWindow", "CPUSpeedPropMenuClass", cpuspeed));
      td.appendChild(me.createTableEntry("Multi Processors", "MpuInfoWindow", "MPUPropMenuClass", mpu));
      td.appendChild(me.createTableEntry("Memory", "MemoryInfoWindow", "MemoryPropMenuClass", memory));
      propMenuDiv.appendChild(me.attachTextForm(id, "loader"));
      propMenuDiv.appendChild(me.attachTextForm(id, "filesystem"));
      propMenuDiv.appendChild(me.attachTextForm(id, "kernel"));
      propMenuDiv.appendChild(me.attachDeleteButton());
    } 
    else if (targetElement.getAttributeNS(null, "type") == "experimental") 
    {
      var id = targetElement.getAttributeNS(null, "id");
      var mac = targetElement.getAttributeNS(null, "mac");
      var model = targetElement.getAttributeNS(null, "model");
      var port = targetElement.getAttributeNS(null, "port");
      var sw = targetElement.getAttributeNS(null, "switch");
      var ip = targetElement.getAttributeNS(null, "ip");
      var subnet = targetElement.getAttributeNS(null, "subnet");

      var td = document.createElementNS(me.formHelper.XHTMLNS, "td");
      propTable.appendChild(td);
      td.appendChild(me.createTableEntry("Interface ID", "InterfaceIdInfoWindow", "InterfaceIdPropMenuClass", id));
      td.appendChild(me.createTableEntry("mac", "InterfaceMacInfoWindow", "InterfaceMacPropMenuClass", mac));
      td.appendChild(me.createTableEntry("model", "InterfaceModelInfoWindow", "InterfaceModelPropMenuClass", model));
      td.appendChild(me.createTableEntry("port", "InterfacePortInfoWindow", "InterfacePortPropMenuClass", port));
      td.appendChild(me.createTableEntry("switch", "InterfaceSwitchInfoWindow", "InterfaceSwitchPropMenuClass", sw));
      propMenuDiv.appendChild(me.attachTextForm(id, "ip"));
      propMenuDiv.appendChild(me.attachTextForm(id, "subnet"));
    } 
    else if (targetElement.getAttributeNS(null, "type") == "edge") 
    {
      var id = targetElement.getAttributeNS(null, "vlan");

      var td = document.createElementNS(me.formHelper.XHTMLNS, "td");
      propTable.appendChild(td);
      td.appendChild(me.createTableEntry("VLAN Name", "VlanNameInfoWindow", "VlanNamePropMenuClass", id));
      propMenuDiv.appendChild(me.attachDeleteButton());
    }
  };



  this.attachDeleteButton = function attachDeleteButton() 
  {
    // Create node button
    var div = document.createElementNS(me.formHelper.XHTMLNS, "div");
    var p = document.createElementNS(me.formHelper.XHTMLNS, "p");
    div.appendChild(p);
    var form = document.createElementNS(me.formHelper.XHTMLNS, "form");
    p.appendChild(form);
    form.setAttributeNS(null, "id", "svgObjectDeleteButtonId");
    form.setAttributeNS(null, "name", "svgObjectDeleteButtonName");
    var input = document.createElementNS(me.formHelper.XHTMLNS, "input");
    form.appendChild(input);
    input.setAttributeNS(null, "type", "button");
    input.setAttributeNS(null, "value", "Delete object");
    input.setAttribute("class", "experiment-boldbuttoninputform");
    input.onclick = me.doDeleteSVGObject;
    return div;
  };
  
  
  
  this.attachTextForm = function attachTextForm(targetid, value) 
  {    
    var formvalue = me.SVGDocument.getElementById(targetid).getAttribute(value);
    var div = document.createElementNS(me.formHelper.XHTMLNS, "div");
    var p = document.createElementNS(me.formHelper.XHTMLNS, "p");
    div.appendChild(p);

    var label = document.createElement("label");
    p.appendChild(label);
    label.setAttribute("for", value + "PropChangeFormId");
    label.appendChild(document.createTextNode(value));

    var form = document.createElementNS(me.formHelper.XHTMLNS, "form");
    p.appendChild(form);
    form.setAttributeNS(null, "id", value + "PropChangeFormId");
    form.setAttributeNS(null, "name", value + "PropChangeFormName");
    form.setAttributeNS(null, "owner", targetid);
    var input = document.createElementNS(me.formHelper.XHTMLNS, "input");
    form.appendChild(input);
    input.setAttributeNS(null, "type", "text");
    input.setAttributeNS(null, "value", formvalue);
    input.setAttribute("class", "experiment-simpletextinputform");
    input.setAttribute("maxlength", "80");
    input.disabled = true;

    return div;
  };



  this.doLoaderPropChange = function doLoaderPropChange() 
  {
    var element = top.document.getElementById("loaderPropChangeFormId");
    var value = element.firstChild.value;
    var owner = element.getAttribute("owner");

    me.SVGDocument.getElementById(owner).setAttributeNS(null, "loader", value);
  };



  this.doFilesystemPropChange = function doFilesystemPropChange() 
  {
    var element = top.document.getElementById("filesystemPropChangeFormId");
    var value = element.firstChild.value;
    var owner = element.getAttribute("owner");
    me.SVGDocument.getElementById(owner).setAttributeNS(null, "filesystem", value);
  };



  this.doKernelPropChange = function doKernelPropChange() 
  {
    var element = top.document.getElementById("kernelPropChangeFormId");
    var value = element.firstChild.value;
    var owner = element.getAttribute("owner");

    me.SVGDocument.getElementById(owner).setAttributeNS(null, "kernel", value);
  };



  this.doIPPropChange = function doIPPropChange() 
  {
    var element = top.document.getElementById("ipPropChangeFormId");
    var value = element.firstChild.value;
    var owner = element.getAttribute("owner");

    me.SVGDocument.getElementById(owner).setAttributeNS(null, "ip", value);
  };



  this.doSubnetPropChange = function doSubnetPropChange() 
  {
    var element = top.document.getElementById("subnetPropChangeFormId");
    var value = element.firstChild.value;
    var owner = element.getAttribute("owner");

    me.SVGDocument.getElementById(owner).setAttributeNS(null, "subnet", value);
  };



  this.doDeleteSVGObject = function doDeleteSVGObject() 
  {
    var target = me.SVGDocument.getElementById(me.objectToDelete);
    var interfaces = new Array();
    if (target.getAttribute("type") == "computer") 
    {
      var p = target.parentNode;

      // get interface references
      var kids = p.childNodes;
      for (var k = 0; k < kids.length; k++) 
      {
        if (kids[k].getAttribute("type") == "experimental") 
        {
          interfaces.push(kids[k]);
        }
      }

      // remove children
      while (p.hasChildNodes()) 
      {
        p.removeChild(p.lastChild);
      }
      // remove the parent itself
      p.parentNode.removeChild(p);
    } 
    else if (target.getAttribute("type") == "edge") 
    {
      target.parentNode.removeChild(target);
    }

    // remove the properties table
    var propid = me.objectToDelete + "propMenuId";
    var propObj = top.document.getElementById(propid);
    propObj.parentNode.removeChild(propObj);

    // remove dangling edges if any
    for (var k = 0; k < interfaces.length; k++) 
    {
      var edgeid = interfaces[k].getAttribute("edgeId");
      if (edgeid != "") 
      {
        var edgeIds = edgeid.split(" ");
        if (edgeIds.length > 0) 
        {
          for (var j = 0; j < edgeIds.length; j++) 
          {
            var targetEdge = document.getElementById(edgeIds[j]);
            targetEdge.parentNode.removeChild(targetEdge);
          }
        } 
        else 
        {
          var targetEdge = document.getElementById(edgeid);
          targetEdge.parentNode.removeChild(targetEdge);
        }
      }
    }

    // return the selected 'host' node to the drop-down box
    if (target.getAttribute("type") == "computer") 
    {
      var selectBox = top.document.forms.nodeNameDropdownFormName.nodeNameDropdownSelectName;
      selectBox.options[selectBox.options.length] = new Option(me.objectToDelete, me.objectToDelete);      
      me.doRequest(target.id);
      top.document.getElementById("nodeInfoDivId").style.visibility = "visible";
    }
  };



  this.toggleNodeInfoWindow = function toggleNodeInfoWindow(evt) 
  {
    if (top && top.document) 
    {
      var exists = false;
      for (var i = 0; i < me.tabMainDiv.childNodes.length; i++) 
      {
        if (me.tabMainDiv.childNodes[i].getAttribute("class") == "experiment-nodeinfodivpanel") 
        {
          if (me.tabMainDiv.childNodes[i].getAttribute("id") != evt.target.id) 
          {
            me.tabMainDiv.childNodes[i].style.visibility = "hidden";
          }
          if (me.tabMainDiv.childNodes[i].getAttribute("id") == evt.target.id) 
          {
            me.tabMainDiv.childNodes[i].style.visibility = "visible";
            exists = true;
          }
        }
      }
      if (exists == false) 
      {
        me.createNodeInfoWindow(evt);
      }
    }
  }; 



  // connect the edges to two nodes
  this.doCreateEdge = function doCreateEdge() 
  {
    var name = top.document.edgeInputForm.edgeName.value;

    // validate if id is entered
    if (name == "") 
    {
      alert("You'll need some sort of name for your VLAN.");
      return;
    }

    var startNode = top.document.edgeInputForm.startNodeIDName.value;
    var startNodeIF = top.document.edgeInputForm.startNodeIntName.value;
    var endNode = top.document.edgeInputForm.endNodeIDName.value;
    var endNodeIF = top.document.edgeInputForm.endNodeIntName.value;

    // 'edgeid' attribute is used for dragging, so they must be unique.
    // 'vlanid' attribute is to indicate that different nodes with the same
    // value are connected to the same vlan.
    var vlanid = name;
    var edgeid = name + me.valueCounter;
    me.valueCounter++;

    // validate if start and end nodes are the same
    if (startNode == endNode) 
    {
      alert("Start and end node should be different!");
      return;
    }

    // validate if these nodes actually exist on the canvas
    if (!me.validateNodeExistence(startNode)) 
    {
      alert("Start node has to exist first!");
      return;
    }
    if (!me.validateNodeExistence(startNode + startNodeIF)) 
    {
      alert("Start node interface has to exist first!");
      return;
    }
    if (!me.validateNodeExistence(endNode)) 
    {
      alert("End node has to exist first!");
      return;
    }
    if (!me.validateNodeExistence(endNode + endNodeIF)) 
    {
      alert("End node interface has to exist first!");
      return;
    }

    var sNode = document.getElementById(startNode);
    var eNode = document.getElementById(endNode);


    // get start and end node interfaces
    var edgeStart = me.SVGDocument.getElementById(startNode + startNodeIF);
    var edgeEnd = me.SVGDocument.getElementById(endNode + endNodeIF);

    x1 = edgeStart.cx.baseVal.value;
    y1 = edgeStart.cy.baseVal.value;
    x2 = edgeEnd.cx.baseVal.value;
    y2 = edgeEnd.cy.baseVal.value;

    var line = me.SVGDocument.createElementNS(me.SVGNS, "line");
    line.setAttributeNS(null, "id", edgeid);
    line.setAttributeNS(null, "x1", x1);
    line.setAttributeNS(null, "y1", y1);
    line.setAttributeNS(null, "x2", x2);
    line.setAttributeNS(null, "y2", y2);
    line.setAttributeNS(null, "type", "edge");
    line.setAttributeNS(null, "stroke", "green");
    line.setAttributeNS(null, "stroke-width", "2");
    line.setAttributeNS(null, "vlan", vlanid);

    line.setAttributeNS(null, "edgeStart", startNode + startNodeIF);
    line.setAttributeNS(null, "edgeEnd", endNode + endNodeIF);

    line.addEventListener("mouseover", me.hover, false);

    // Change the attributes on the interfaces. Append to the existing
    // values when possible.
    if (edgeStart.getAttributeNS(null, "edgeId") != "") 
    {
      var oldEdgeStart = edgeStart.getAttributeNS(null, "edgeId");
      var newEdgeStart = oldEdgeStart + " " + edgeid;
      edgeStart.setAttributeNS(null, "edgeId", newEdgeStart);
    } 
    else 
    {
      edgeStart.setAttributeNS(null, "edgeId", edgeid);
    }

    if (edgeEnd.getAttributeNS(null, "edgeId") != "") 
    {
      var oldEdgeEnd = edgeEnd.getAttributeNS(null, "edgeId");
      var newEdgeEnd = oldEdgeEnd + " " + edgeid;
      edgeEnd.setAttributeNS(null, "edgeId", newEdgeEnd);
    }
    else
    {
      edgeEnd.setAttributeNS(null, "edgeId", edgeid);
    }


    edgeStart.setAttributeNS(null, "vlan", vlanid);
    edgeEnd.setAttributeNS(null, "vlan", vlanid);

    var svgDoc = me.SVGDocument.getElementById("svgDoc");
    svgDoc.appendChild(line);
  };



  this.updateSingleEdge = function updateSingleEdge(target) 
  {
    if (target.getAttributeNS(null, "type") == "experimental") 
    {
      var edgeid = target.getAttributeNS(null, "edgeId");
      if (edgeid != "") 
      {
	var edgeIds = edgeid.split(" ");

        for (var i = 0; i < edgeIds.length; i++) 
	{
	  var edge = me.SVGDocument.getElementById(edgeIds[i]);

	  var startRef = edge.getAttributeNS(null, "edgeStart");
	  var endRef = edge.getAttributeNS(null, "edgeEnd");

	  var edgeStart = me.SVGDocument.getElementById(startRef);
	  var edgeEnd = me.SVGDocument.getElementById(endRef);

	  edge.setAttributeNS(null, "x1", edgeStart.getAttributeNS(null, "cx"));
	  edge.setAttributeNS(null, "y1", edgeStart.getAttributeNS(null, "cy"));

	  edge.setAttributeNS(null, "x2", edgeEnd.getAttributeNS(null, "cx"));
	  edge.setAttributeNS(null, "y2", edgeEnd.getAttributeNS(null, "cy"));
	}
      }
    }
  };



  this.updateMultipleEdge = function updateMultipleEdge(target) 
  {
    if (target.getAttributeNS(null, "type") == "computer") 
    {
      var iArray = new Array();

      for (var i = 0; i < target.parentNode.childNodes.length; i++) 
      {
        if (target.parentNode.childNodes[i] == "interface") 
        {
          iArray.push(target.parentNode.childNodes[i]);
        }
      }

      for (var i = 0; i < iArray.length; i++) 
      {
        me.updateSingleEdge(iArray[i]);
      }
    }
  };



  this.validateNodeId = function validateNodeId(nodeid) 
  {
    var svgDoc = me.SVGDocument.getElementById("svgDoc");
    var circle = svgDoc.getElementsByTagName("circle");
    for (var i = 0; i < circle.length; i++) 
    {
      if (circle[i].getAttribute("id") == nodeid) 
      {
        return false;
      }
    }
    return true;
  };


  this.validateNodeExistence = function validateNodeExistence(nodeid) 
  {
    var svgDoc = me.SVGDocument.getElementById("svgDoc");
    var circle = svgDoc.getElementsByTagName("circle");
    for (var i = 0; i < circle.length; i++) 
    {
      if (circle[i].getAttribute("id") == nodeid) 
      {
        return true;
      }
    }
    return false;
  };
  
  
  
  this.marshalXMLString = function marshalXMLString() 
  {
    var motherboard = "";
    var cputype = "";
    var cpuspeed = "";
    var mpu = "";
    var memory = "";
    var loader = "";
    var filesystem = "";
    var kernel = "";

    var experimentid = top.document.forms.experimentIdInputFormName.experimentIdName.value;
    var startDate = top.document.forms.experimentIdInputFormName.startDateInputFormName.value;
    var endDate = top.document.forms.experimentIdInputFormName.endDateInputFormName.value;
    var description = top.document.forms.experimentIdInputFormName.experimentDescription.value;

    var username = top.document.forms.userDetailsInputFormName.usernameInputFormName.value;
    var password = top.document.forms.userDetailsInputFormName.passwordInputFormName.value;
    var email = top.document.forms.userDetailsInputFormName.emailInputFormName.value;

    var svgDoc = me.SVGDocument.getElementById("svgDoc");
    var g = svgDoc.getElementsByTagName("g");
    var lines = svgDoc.getElementsByTagName("line");

    // marshall parameters for the POST method to be sent to the CGI script
    var xmlString = "";
    xmlString += me.addExperimentTopologyTag(experimentid, startDate, endDate);
    xmlString += me.addExperimentDescriptionTag(description);
    xmlString += me.addExperimentUsermanagementTag(username, password, email);

    for (var i = 0; i < g.length; i++) 
    {
      var circle = g[i].childNodes;
      for (var j = 0; j < circle.length; j++) 
      {
        if (circle[j].getAttribute("type") == "computer") 
        {
          //alert(circle[j].getAttribute("id"));
          xmlString += me.addExperimentNodeTag(
              circle[j].getAttribute("id"),
              circle[j].getAttribute("type"),
              circle[j].getAttribute("cx"),
              circle[j].getAttribute("cy"));
          motherboard = circle[j].getAttribute("motherboard");
          cputype = circle[j].getAttribute("cputype");
          cpuspeed = circle[j].getAttribute("cpuspeed");
          mpu = circle[j].getAttribute("mpu");
          memory = circle[j].getAttribute("memory");

          loader = circle[j].getAttribute("loader");
          filesystem = circle[j].getAttribute("filesystem");
          kernel = circle[j].getAttribute("kernel");

        } 
        else if (circle[j].getAttribute("type") == "experimental") 
        {
          //alert(circle[j].getAttribute("id") + " " + circle[j].getAttribute("mac"));
          xmlString += me.addExperimentInterfaceTag(
              circle[j].getAttribute("id"),
              circle[j].getAttribute("type"),
              circle[j].getAttribute("mac"),
              circle[j].getAttribute("model"),
              circle[j].getAttribute("port"),
              circle[j].getAttribute("switch"),
              circle[j].getAttribute("ip"),
              circle[j].getAttribute("subnet"),
              circle[j].getAttribute("vlan"),
              circle[j].getAttribute("cx"),
              circle[j].getAttribute("cy"),
              circle[j].getAttribute("edgeId"));
        }
      }


      xmlString += me.addExperimentAttributeTag("motherboard", motherboard);
      xmlString += me.addExperimentAttributeTag("cputype", cputype);
      xmlString += me.addExperimentAttributeTag("cpuspeed", cpuspeed);
      xmlString += me.addExperimentAttributeTag("mpu", mpu);
      xmlString += me.addExperimentAttributeTag("memory", memory);

      xmlString += me.addExperimentNetbootInfoTag(loader, filesystem, kernel);

      xmlString += "<\/node>\n";     // close the node tag!
    }

    // add the lines (edges/vlans) to the xml
    if (lines.length > 0) 
    {
      for (var i = 0; i < lines.length; i++) 
      {
        xmlString += me.addExperimentEdgeTag(
            lines[i].getAttribute("id"),
            lines[i].getAttribute("type"),
            lines[i].getAttribute("x1"),
            lines[i].getAttribute("y1"),
            lines[i].getAttribute("x2"),
            lines[i].getAttribute("y2"),
            lines[i].getAttribute("edgeStart"),
            lines[i].getAttribute("edgeEnd"),
            lines[i].getAttribute("vlan"));
      }
    }

    xmlString += "<\/topology>";     // close the topology tag!
    return xmlString;
  }

//function dummyHandler() {
//    if (me.xhr.readyState == 4) {
//        if (me.xhr.status == 200) {
//            // nothing to do here
//        }
//    }
//}


  this.doFileLoadRequest = function doFileLoadRequest(value) 
  {
    me.filelistXHR = new XMLHttpRequest();
    me.filelistXHR.onreadystatechange = me.handleRefreshFileXMLReply;
    me.filelistXHR.open("GET", "/cgi-bin/gui/components/experiment/loadconfigcgi.py?filename=" + value + ".xml", true);

    me.filelistXHR.setRequestHeader("Content-Type", "text/xml");
    me.filelistXHR.send(null);
  };
  
  
  
  this.handleRefreshFileXMLReply = function handleRefreshFileXMLReply() 
  {
    if (me.filelistXHR.readyState == 4) 
    {
      if (me.filelistXHR.status == 200) 
      {
        var xmlDoc = me.filelistXHR.responseXML;

        me.doClearCanvas();

        var svgDoc = me.SVGDocument.getElementById("svgDoc");
        var nodes = xmlDoc.getElementsByTagName("node");
        var g;
        var circle;
        
        for (var n = 0; n < nodes.length; n++) // nodes
        {    
          g = me.SVGDocument.createElementNS(me.SVGNS, "g");
          svgDoc.appendChild(g);
          g.setAttributeNS(null, "id", "NodeGroup");
          circle = me.SVGDocument.createElementNS(me.SVGNS, "circle");
          g.appendChild(circle);
          circle.setAttributeNS(null, "id", nodes[n].getAttributeNS(null, "id"));
          circle.setAttributeNS(null, "type", nodes[n].getAttributeNS(null, "type"));
          circle.setAttributeNS(null, "cx", nodes[n].getAttributeNS(null, "cx"));
          circle.setAttributeNS(null, "cy", nodes[n].getAttributeNS(null, "cy"));
          circle.setAttributeNS(null, "grabX", "");
          circle.setAttributeNS(null, "grabY", "");
          circle.setAttributeNS(null, "r", me.NodeRadius);
          circle.setAttributeNS(null, "fill", "blue");
          circle.setAttributeNS(null, "stroke", "black");
          circle.addEventListener("mouseover", me.hover, false);

          // refresh edge start and end nodes
          var selectBox = top.document.forms.edgeInputForm.startNodeIDName;
          selectBox.options[selectBox.options.length] = new Option(nodes[n].getAttributeNS(null, "id"));
          selectBox = top.document.forms.edgeInputForm.endNodeIDName;
          selectBox.options[selectBox.options.length] = new Option(nodes[n].getAttributeNS(null, "id"));
          top.doStartNodeIDNameDropdownSelect(selectBox);

          // restore the node attributes
          var attributes = nodes[n].getElementsByTagName("attribute");
          for (var a = 0; a < attributes.length; a++) {   // attributes
              circle.setAttributeNS(me.SVGNS, attributes[a].getAttributeNS(null, "name"), attributes[a].getAttributeNS(null, "value"));
          }

          var iface = nodes[n].getElementsByTagName("interface");
          for (var i = 0; i < iface.length; i++) // interfaces
          {
            circle = me.SVGDocument.createElementNS(me.SVGNS, "circle");
            g.appendChild(circle);
            circle.setAttributeNS(null, "id", iface[i].getAttributeNS(null, "id"));
            circle.setAttributeNS(null, "type", iface[i].getAttributeNS(null, "type"));
            circle.setAttributeNS(null, "mac", iface[i].getAttributeNS(null, "mac"));
            circle.setAttributeNS(null, "model", iface[i].getAttributeNS(null, "port"));
            circle.setAttributeNS(null, "switch", iface[i].getAttributeNS(null, "switch"));
            circle.setAttributeNS(null, "ip", iface[i].getAttributeNS(null, "ip"));
            circle.setAttributeNS(null, "subnet", iface[i].getAttributeNS(null, "subnet"));
            circle.setAttributeNS(null, "vlan", iface[i].getAttributeNS(null, "vlan"));
            circle.setAttributeNS(null, "cx", iface[i].getAttributeNS(null, "cx"));
            circle.setAttributeNS(null, "cy", iface[i].getAttributeNS(null, "cy"));
            circle.setAttributeNS(null, "r", me.InterfaceRadius);
            circle.setAttributeNS(null, "fill", "red");
            circle.setAttributeNS(null, "stroke", "black");
            circle.setAttributeNS(null, "grabX", "");
            circle.setAttributeNS(null, "grabY", "");
            circle.setAttributeNS(null, "edgeId", iface[i].getAttributeNS(null, "edgeId"));
            circle.setAttributeNS(null, "mac", iface[i].getAttributeNS(null, "mac"));
            circle.setAttributeNS(null, "model", iface[i].getAttributeNS(null, "model"));
            circle.setAttributeNS(null, "port", iface[i].getAttributeNS(null, "port"));
            circle.setAttributeNS(null, "switch", iface[i].getAttributeNS(null, "switch"));
            circle.setAttributeNS(null, "ip", iface[i].getAttributeNS(null, "ip"));
            circle.addEventListener("mouseover", me.hover, false);
          }
        }

        // restore the edges
        var edges = xmlDoc.getElementsByTagName("edge");
        var line;
        for (var i = 0; i < edges.length; i++) // edges
        {
          line = me.SVGDocument.createElementNS(me.SVGNS, "line");
          svgDoc.appendChild(line);
          line.setAttributeNS(null, "id", edges[i].getAttributeNS(null, "id"));
          line.setAttributeNS(null, "x1", edges[i].getAttributeNS(null, "x1"));
          line.setAttributeNS(null, "y1", edges[i].getAttributeNS(null, "y1"));
          line.setAttributeNS(null, "x2", edges[i].getAttributeNS(null, "x2"));
          line.setAttributeNS(null, "y2", edges[i].getAttributeNS(null, "y2"));
          line.setAttributeNS(null, "edgeStart", edges[i].getAttributeNS(null, "edgeStart"));
          line.setAttributeNS(null, "edgeEnd", edges[i].getAttributeNS(null, "edgeEnd"));
          line.setAttributeNS(null, "type", "edge");
          line.setAttributeNS(null, "stroke", "green");
          line.setAttributeNS(null, "stroke-width", "2");
          line.setAttributeNS(null, "vlan", edges[i].getAttributeNS(null, "vlan"));
          line.addEventListener("mouseover", me.hover, false);
        }

        // update the node list
        var circle = svgDoc.getElementsByTagName("circle");
        var selectBox = top.document.forms.nodeNameDropdownFormName.nodeNameDropdownSelectName;

        me.clearAndReloadDropBox(selectBox);

        for (var j = 0; j < selectBox.options.length; j++) 
        {
          for (var i = 0; i < circle.length; i++) 
          {
            if (circle[i].getAttributeNS(null, "type") == "computer") 
            {
              if (circle[i].id == selectBox.options[j].value) 
              {
                selectBox.options[j] = null;
              }
            }
          }
        }
        
        // reload the menu properties
        if (selectBox.options.length == 0) 
        {
          var element = top.document.getElementById("nodeInfoTableId");
          element.style.visibility = "hidden";
        } 
        else 
        {
          me.doRequest(selectBox.options[0].value);
        }

        // refresh experiment details
        var topology = xmlDoc.getElementsByTagName("topology")[0];
        var experimentid = topology.getAttribute("experimentid");
        top.document.forms.experimentIdInputFormName.experimentIdName.value = experimentid;

        // refresh start and end date
        var startDate = topology.getAttribute("startdate");
        var endDate = topology.getAttribute("enddate");
        top.document.forms.experimentIdInputFormName.startDateInputFormName.value = startDate;
        top.document.forms.experimentIdInputFormName.endDateInputFormName.value = endDate;

        // refresh username, password and email details
        var usermanagement = xmlDoc.getElementsByTagName("usermanagement")[0];
        var username = usermanagement.getAttribute("username");
        top.document.forms.userDetailsInputFormName.usernameInputFormName.value = username;

        var password = usermanagement.getAttribute("password");
        top.document.forms.userDetailsInputFormName.passwordInputFormName.value = password;

        var email = usermanagement.getAttribute("email");
        top.document.forms.userDetailsInputFormName.emailInputFormName.value = email;

        // refresh description
        var descTag = xmlDoc.getElementsByTagName("description")[0];
        var description = descTag.lastChild.nodeValue;
        top.document.forms.experimentIdInputFormName.experimentDescription.value = description;

        // hide left panel if no more nodes
        var svgDoc = me.SVGDocument.getElementById("svgDoc");
        var g = svgDoc.getElementsByTagName("g");
        if (g.length == me.nodeOptions.length) 
        {
          top.document.getElementById("nodeInfoDivId").style.visibility = "hidden";
        }

      }
    }
  };



  // clear the SVG canvas
  this.doClearCanvas = function doClearCanvas() 
  {
    // remove canvas shape objects. (there is no way to
    // avoid removing the <script/> tags as well because
    // removeChild() complaints. anyway, this works.)
    var svgDoc = me.SVGDocument.getElementById("svgDoc");
    while (svgDoc.hasChildNodes()) 
    {
      svgDoc.removeChild(svgDoc.lastChild);
    }

    var selectBox = top.document.forms.nodeNameDropdownFormName.nodeNameDropdownSelectName;

    for (var i = 0; i < me.nodeOptions.length; i++) 
    {
      selectBox.options[i] = new Option(me.nodeOptions[i], me.nodeOptions[i]);
      // refresh the drop-box properties
      me.doRequest(selectBox.options[0].value);
    }
  };
  
  
  
  this.clearAndReloadDropBox = function clearAndReloadDropBox(target) 
  {
    // first clear the drop-down list
    target.options.length = 0;

    // reload with available nodes
    for (var i = 0; i < me.nodeOptions.length; i++) 
    {
      target.options[i] = new Option(me.nodeOptions[i], me.nodeOptions[i]);
    }
  };


  this.doWriteConfig = function doWriteConfig() 
  {
    if (me.validateConfigEntries() == false) return;

    var xmlString = me.marshalXMLString();

    me.writeConfigXHR = new XMLHttpRequest();
    me.writeConfigXHR.open("POST", "/cgi-bin/gui/components/experiment/writeconfigcgi.py", true);
    me.writeConfigXHR.onreadystatechange = me.handleWriteConfig;
    me.writeConfigXHR.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    me.writeConfigXHR.send(xmlString);
  };



  this.handleWriteConfig = function handleWriteConfig() 
  {
    if (me.writeConfigXHR.readyState == 4) 
    {
      if (me.writeConfigXHR.status == 200) 
      {	
        top.doRefreshConfigFileList();
      }
    }
  };



  this.validateConfigEntries = function validateConfigEntries() 
  {
    var startdate = top.document.getElementById("startDateInputFormId").value;
    var enddate = top.document.getElementById("endDateInputFormId").value;

    //var pattern = new RegExp("[0-9][0-9]\/[0-9][0-9]\/[0-9][0-9][0-9][0-9]", "gi");
    var pattern = new RegExp("^\d{2}(\/)\d{2}(\/)\d{4}$", "g");
    //var pattern = new RegExp("(\d\d)(\/)(\d\d)(\/)(\d{4})", "g");

    if(isNaN(startdate.substring(0, 2)) ||
       isNaN(startdate.substring(3, 5)) ||
       isNaN(startdate.substring(6, 10)) ||
       startdate.charAt(2) != "/" ||
       startdate.charAt(5) != "/") 
    {
      alert(startdate + " is not a valid date.");
      return false;
    }

    if(isNaN(enddate.substring(0, 2)) ||
       isNaN(enddate.substring(3, 5)) ||
       isNaN(enddate.substring(6, 10)) ||
       enddate.charAt(2) != "/" ||
       enddate.charAt(5) != "/") 
    {
      alert(enddate + " is not a valid date.");
      return false;
    }

    return true;
  };
  
  
  this.addExperimentTopologyTag = function addExperimentTopologyTag(experimentid, startDate, endDate) 
  {
    var str = "";
    //str += "<?xml version=\"1.0\" ?>\n";
    str += "<topology type==\"experiment\" experimentid=\"" + experimentid + 
        "\" startdate=\"" + startDate +
        "\" enddate=\"" + endDate + "\">\n";
    return str;
  };
  
  
  this.addExperimentDescriptionTag = function addExperimentDescriptionTag(description) 
  {
    var str = "";
    str += "\t<description>";
    str += description;
    str += "</description>\n";
    return str;
  };
  
  
  this.addExperimentUsermanagementTag = function addExperimentUsermanagementTag(username, password, email) 
  {
    var str = "";
    str += "\t<usermanagement username=\"" + username +
        "\" password=\"" + password +
        "\" email=\"" + email + "\"/>\n";
    return str;
  };
  
  
  this.addExperimentNetbootInfoTag = function addExperimentNetbootInfoTag(loader, filesystem, kernel) 
  {
    var str = "";
    str += "\t\t<netbootinfo loader=\"" + loader +
        "\" filesystem=\"" + filesystem +
        "\" kernel=\"" + kernel + "\"/>\n";
    return str;
  };



  this.addExperimentNodeTag = function addExperimentNodeTag(id, className, cx, cy) 
  {
    if (id == null) id = "";
    if (className == null) className = "";
    if (cx == null) cx = "";
    if (cy == null) cy = "";

    var str = "";
    str += "\t<node id=\"" + id + "\" type=\"" + className + "\" cx=\"" + cx + "\" cy=\"" + cy + "\">\n";
    return str;
  };


  this.addExperimentInterfaceTag = function addExperimentInterfaceTag(id, className, mac, model, port, sw, ip, subnet, vlan, cx, cy, edgeId) 
  {
    if (id == null) id = "";
    if (className == null) className = "";
    if (mac == null) mac = "";
    if (model == null) model = "";
    if (port == null) port = "";
    if (sw == null) sw = "";
    if (ip == null) ip = "";
    if (subnet == null) subnet = "";
    if (vlan == null) vlan = "";
    if (cx == null) cx = "";
    if (cy == null) cy = "";
    if (edgeId == null) edgeId = "";

    var str = "";
    str += "\t\t<interface id=\"" + id + "\" type=\"" + className + "\" mac=\"" + mac +
        "\" model=\"" + model + "\" port=\"" + port + "\" switch=\"" + sw + "\" ip=\"" + ip + "\" subnet=\"" + subnet +
        "\" vlan=\"" + vlan + "\" cx=\"" + cx + "\" cy=\"" + cy + "\" edgeId=\"" + edgeId + "\"/>\n";
    return str;
  };


  this.addExperimentAttributeTag = function addExperimentAttributeTag(name, value) 
  {
    if (name == null) name = "";
    if (value == null) value = "";

    var str = "";
    str += "\t\t<attribute name=\"" + name + "\" value=\"" + value + "\" />\n";
    return str;
  };
  
  
  
  this.addExperimentEdgeTag = function addExperimentEdgeTag(id, className, x1, y1, x2, y2, edgeStart, edgeEnd, vlan) 
  {
    if (id == null) id = "";
    if (className == null) className = "";
    if (x1 == null) x1 = "";
    if (y1 == null) y1 = "";
    if (x2 == null) x2 = "";
    if (y2 == null) y2 = "";
    if (edgeStart == null) edgeStart = "";
    if (edgeEnd == null) edgeEnd = "";
    if (vlan == null) vlan = "";

    var str = "";
    str += "\t<edge id=\"" + id + "\" type=\"" + className + "\" x1=\"" + x1 +
        "\" x2=\"" + x2 + "\" y1=\"" + y1 + "\" y2=\"" + y2 + "\" edgeStart=\"" +
        edgeStart + "\" edgeEnd=\"" + edgeEnd + "\" vlan=\"" + vlan + "\"/>\n";
    return str;
  };
  
  
  this.createTableEntry = function createTableEntry(cell1, cell2, classname, value) 
  {
    var tr = document.createElementNS(me.formHelper.XHTMLNS, "tr");

    var td = document.createElementNS(me.formHelper.XHTMLNS, "td");
    tr.appendChild(td);
    td.setAttribute("style", me.formHelper.cell1Style);
    td.appendChild(document.createTextNode(cell1));

    td = document.createElementNS(me.formHelper.XHTMLNS, "td");
    tr.appendChild(td);
    td.setAttribute("id", cell2 + "Id");
    td.setAttribute("class", classname);
    td.setAttribute("style", me.formHelper.cell2Style);

    if (value != null)
      td.appendChild(document.createTextNode(value));
    else
      td.appendChild(document.createTextNode("---"));

    return tr;
  };



  this.interfaceTableEntry = function interfaceTableEntry(count, name, value) 
  {
    var tbody = top.document.getElementById("nodeInfoTableTbody");

    var tr = document.createElementNS(me.formHelper.XHTMLNS, "tr");
    tbody.appendChild(tr);
    tr.setAttribute("class", "interfaceClass");

    var headerText = top.document.getElementById("Interface" + count);
    if (headerText == null) 
    {
      var th = document.createElementNS(me.formHelper.XHTMLNS, "th");
      tr.appendChild(th);
      th.setAttribute("id", "Interface" + count);
      th.setAttribute("class", "interfaceHeaderClass");
      th.setAttribute("colspan", "2");
      th.setAttribute("style", me.formHelper.cell1Style);
      th.appendChild(document.createTextNode("Interface" + count));
    }

    tr = document.createElementNS(me.formHelper.XHTMLNS, "tr");
    tbody.appendChild(tr);
    tr.setAttribute("id", "Interface" + count + name);
    tr.setAttribute("class", "interfaceClass");

    var td = document.createElementNS(me.formHelper.XHTMLNS, "td");
    tr.appendChild(td);
    td.setAttribute("style", me.formHelper.cell1Style);
    td.appendChild(document.createTextNode(name));

    td = document.createElementNS(me.formHelper.XHTMLNS, "td");
    tr.appendChild(td);

    if (name == "ip") 
    {
      var form = document.createElementNS(me.formHelper.XHTMLNS, "form");
      td.appendChild(form);
      form.setAttribute("name", name + "FormName");

      var input = document.createElementNS(me.formHelper.XHTMLNS, "input");
      form.appendChild(input);
      input.setAttribute("type", "text");
      input.setAttribute("id", "interface" + count + name + "InputFormId");
      input.setAttribute("name", "interface" + count + name + "InputFormName");
      input.setAttribute("value", "");
      input.setAttribute("maxlength", "80");
      input.setAttribute("class", "experiment-simpletextinputform");
    } 
    else 
    {
      td.setAttribute("style", me.formHelper.cell2Style);
      td.appendChild(document.createTextNode(value));
    }

    return tbody;
  };
  
} // end class SVGCanvas


// The following four functions need to be global since they're specified
// as event handlers in canvas.svg. I haven't figured out a way to 
// programatically specify these while still retaining the SVG evt object 
// (programmatically I could assign these handlers even if they belonged to 
// classes)
function experimentTabInitCanvas(evt) 
{
  top.experimentTabSVGCanvas.SVGDocument = evt.target.ownerDocument;
  SVGRoot = top.experimentTabSVGCanvas.SVGDocument.documentElement;

  top.experimentTabSVGCanvas.svgDocument = top.experimentTabSVGCanvas.SVGDocument;
  top.experimentTabSVGCanvas.svgRoot = SVGRoot;
  
  // this will serve as the canvas over which items are dragged.
  //    having the drag events occur on the mousemove over a backdrop
  //    (instead of the dragged element) prevents the dragged element
  //    from being inadvertantly dropped when the mouse is moved rapidly
  top.experimentTabSVGCanvas.BackDrop = top.experimentTabSVGCanvas.SVGDocument.getElementById('experiment-topologyTabDivId');

  if (top.experimentTabSVGCanvas.xhr == null) 
  {
    top.experimentTabSVGCanvas.xhr = new XMLHttpRequest();
    top.experimentTabSVGCanvas.xhr.onreadystatechange = top.experimentTabSVGCanvas.handleNodePropertiesReply;
  }

  //top.experimentTabSVGCanvas.doRequest("computer1");
}

function experimentTabGrab(evt) 
{
  top.experimentTabSVGCanvas.CursorX = Number(evt.clientX);
  top.experimentTabSVGCanvas.CursorY = Number(evt.clientY);
  var targetElement = evt.target;

  // Only allow dragging if it's not the back drop
  if (targetElement != top.experimentTabSVGCanvas.BackDrop) 
  {  
    top.experimentTabSVGCanvas.DragTarget = targetElement;

    top.experimentTabSVGCanvas.SVGDocument.getElementById("svgDoc").setAttributeNS(null, "cursor", "move");
  
    if (top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "type") == "computer") 
    {
      top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, 'pointer-events', 'none');
      top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, 'fill-opacity', '0.5');

      top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, "grabX", top.experimentTabSVGCanvas.CursorX - top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "cx"));
      top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, "grabY", top.experimentTabSVGCanvas.CursorY - top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "cy"));

      var interfaces = top.experimentTabSVGCanvas.DragTarget.parentNode.childNodes;
      for (var i = 0; i < interfaces.length; i++) 
      {
        if (interfaces[i].getAttribute("type") == "experimental") 
        {
          interfaces[i].setAttributeNS(null, "grabX", top.experimentTabSVGCanvas.CursorX - interfaces[i].getAttributeNS(null, "cx"));
          interfaces[i].setAttributeNS(null, "grabY", top.experimentTabSVGCanvas.CursorY - interfaces[i].getAttributeNS(null, "cy"));
          interfaces[i].setAttributeNS(null, 'pointer-events', 'none');
          interfaces[i].setAttributeNS(null, 'fill-opacity', '0.5');
        }
      }
    } 
    else if (top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "type") == "experimental") 
    {
      top.experimentTabSVGCanvas.SnapBackToPointX = parseInt(top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "cx"));
      top.experimentTabSVGCanvas.SnapBackToPointY = parseInt(top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "cy"));

      top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, "grabX", top.experimentTabSVGCanvas.CursorX - parseInt(top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "cx")));
      top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, "grabY", top.experimentTabSVGCanvas.CursorY - parseInt(top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "cy")));

      top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, 'fill-opacity', '0.5');

      var nodes = top.experimentTabSVGCanvas.DragTarget.parentNode.childNodes;
      for (var i = 0; i < nodes.length; i++) 
      {
        nodes[i].setAttributeNS(null, 'pointer-events', 'none');
      }
    }
  }
}

function experimentTabDrag(evt) 
{
  top.experimentTabSVGCanvas.CursorX = Number(evt.clientX);
  top.experimentTabSVGCanvas.CursorY = Number(evt.clientY);

  var targetElement = evt.target;
  if (targetElement != top.experimentTabSVGCanvas.BackDrop) 
  {
    if (top.experimentTabSVGCanvas.DragTarget != null) 
    {
      // User is dragging the circle representing the node, drag the whole group along
      // and bring the interface nodes to the front
      if (top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "type") == "computer") 
      {
        // Move the node circle
        top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, 'cx', top.experimentTabSVGCanvas.CursorX - top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "grabX"));
        top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, 'cy', top.experimentTabSVGCanvas.CursorY - top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "grabY"));

        var interfaces = top.experimentTabSVGCanvas.DragTarget.parentNode.childNodes;
        for (var i = 0; i < interfaces.length; i++) 
        {
          if (interfaces[i].getAttribute("type") == "experimental") 
          {
            interfaces[i].setAttributeNS(null, 'cx', top.experimentTabSVGCanvas.CursorX - interfaces[i].getAttributeNS(null, "grabX"));
            interfaces[i].setAttributeNS(null, 'cy', top.experimentTabSVGCanvas.CursorY - interfaces[i].getAttributeNS(null, "grabY"));
	    top.experimentTabSVGCanvas.updateSingleEdge(interfaces[i]);
          }
        }
      } 
      else if (top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "type") == "experimental") 
      {
        // Before moving it, make sure that the circle is within bounds
        // The first condition is so that isWithinBounds is only calculated per click, 
        // not per move
        if ((!top.experimentTabSVGCanvas.OutOfBounds) && top.experimentTabSVGCanvas.isWithinBounds()) 
        {
          // Save the current point in case the next move causes the interface to 
          // go out of bounds.
          top.experimentTabSVGCanvas.SnapBackToPointX = parseInt(top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "cx"));
          top.experimentTabSVGCanvas.SnapBackToPointY = parseInt(top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "cy"));
          
          top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, 'cx', top.experimentTabSVGCanvas.CursorX - parseInt(top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "grabX")));
          top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, 'cy', top.experimentTabSVGCanvas.CursorY - parseInt(top.experimentTabSVGCanvas.DragTarget.getAttributeNS(null, "grabY")));                   
	  top.experimentTabSVGCanvas.updateSingleEdge(top.experimentTabSVGCanvas.DragTarget);
        } 
        else 
        {
          // Don't move, set flag and save interface's position so that we can snap back to
          // it on drop
          top.experimentTabSVGCanvas.OutOfBounds = true;
        }
      }
    }
  }
}

function experimentTabDrop(evt) 
{
  if (top.experimentTabSVGCanvas.DragTarget) 
  {
    top.experimentTabSVGCanvas.SVGDocument.getElementById("svgDoc").setAttributeNS(null, "cursor", "default");

    if (top.experimentTabSVGCanvas.DragTarget.getAttribute("type") == "computer") 
    {
    } 
    else if (top.experimentTabSVGCanvas.DragTarget.getAttribute("type") == "experimental") 
    {
      // Interface element was dragged out of bounds, snap it back and update
      // its position
      if (top.experimentTabSVGCanvas.OutOfBounds) 
      {
        top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, 'cx', top.experimentTabSVGCanvas.SnapBackToPointX);
        top.experimentTabSVGCanvas.DragTarget.setAttributeNS(null, 'cy', top.experimentTabSVGCanvas.SnapBackToPointY);
        top.experimentTabSVGCanvas.OutOfBounds = false;
      }
    }

    var interfaces = top.experimentTabSVGCanvas.DragTarget.parentNode.childNodes;
    for (var i = 0; i < interfaces.length; i++) 
    {
      interfaces[i].setAttributeNS(null, 'pointer-events', 'all');
      interfaces[i].setAttributeNS(null, 'fill-opacity', '1.0');
    }

    top.experimentTabSVGCanvas.DragTarget = null;
  }
}

