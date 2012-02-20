//**********************************************************************************
//**********************************************************************************
// Implements the auxiliary.draw namespace
//
// CLASSES
// --------------------------------------------
// FormHelper    Creates various forms and elements for them
// PopUpInput    Creates a pop up div with an input in it
// DrawHelper    Creates various divs for text and nodes
//
// $Id: draw.js 48 2006-06-07 20:42:40Z munlee $ 
//**********************************************************************************
//**********************************************************************************
Namespace("auxiliary.draw");
Import("auxiliary.hen", ".", "/");

auxiliary.draw.PopUpInput = function PopUpInput(xPos, yPos, title, input, popUpID, onclickHandler, parentNode, resultTargetID, dataToStore)
{
  // Necessary to keep reference to 'this' for event handlers
  var me = this;
  // The x position of the pop up div
  var xPos = xPos;
  // The y position of the pop up div
  var yPos = yPos;
  // The title for the pop up div
  var title = title;
  // An HTML input object
  var input = input;
  // The id to give to the pop up div
  var popUpID = popUpID;
  // The onclick handler for the submit button
  var onclickHandler = onclickHandler;
  // The node to append the pop up to
  var parentNode = parentNode;
  // The id of the target for the input's result
  var resultTargetID = resultTargetID;
  // Any data that the caller of this class might want to retrieve after the pop up input is done
  var dataToStore = dataToStore;
  // Used to keep a reference to the div
  var popUpDiv = null;
  // Used to keep a reference to the label in the div
  var label = null;
  // Used to keep a reference to the cell that contains the input box
  var inputCell = null;
  // Used to keep a reference to the submit button
  var sumbmitButton = null;
  // Used to draw HTML elements
  var drawHelper = new auxiliary.draw.DrawHelper();
  // The width of the pop up div
  var POP_UP_WIDTH = 160;
  // The height of the pop up div
  var POP_UP_HEIGHT = 90;
  // Whether the create function has been ran already or not
  var createdPopUp = false;

  this.setXPosition = function setXPosition(xPosition) { xPos = xPosition; };
  this.setYPosition = function setYPosition(yPosition) { yPos = yPosition; };
  this.setTitle = function setTitle(theTitle) { title = theTitle; };
  this.setInput = function setInput(theInput) { input = theInput; };
  this.setID = function setID(thePopUpID) { popUpID = thePopUpID; };
  this.setOnclickHandler = function setOnclickHandler(theOnclickHandler) { onclickHandler = theOnclickHandler; };
  this.setParentNode = function setParentNode(theParentNode) { parentNode = theParentNode; };
  this.setResultTargetID = function setResultTargetID(theResultTargetID) { resultTargetID = theResultTargetID; };
  this.getResultTargetID = function getResultTargetID() { return resultTargetID; };
  this.getDataToStore = function getDataToStore() { return dataToStore; };

  this.showPopUp = function showPopUp()
  {
    if (!createdPopUp)
    {
      createPopUp();
      createdPopUp = true;
    }

    // Clear existing title (if any) and display the given one
    try
    {
      label.removeChild(label.firstChild);
    }
    catch (e) {}
    label.appendChild(document.createTextNode(title));

    // Clear existing input box (if any) and display the given one
    try
    {
      inputCell.removeChild(inputCell.firstChild);
    }
    catch (e) {}
    inputCell.appendChild(input);
    if (input.type == "text")
    {
      // Clear any previous input
      input.value = "";
      // Give the input box focus
      input.focus();
    }

    // Set the onclick handler for the submit button
    submitButton.onclick = onclickHandler;

    // Show the div
    popUpDiv.style.visibility = "visible";
  };

  this.closePopUp = function hidePopUp()
  {
    popUpDiv.style.visibility = "hidden";    
  };

  var createPopUp = function createPopUp()
  {
    popUpDiv = document.createElement("div");
    popUpDiv.setAttribute("id", popUpID);
    popUpDiv.setAttribute("class", "draw-floatinginput");
    popUpDiv.style.left = xPos;
    popUpDiv.style.top = yPos;
    popUpDiv.style.width = POP_UP_WIDTH;
    popUpDiv.style.height = POP_UP_HEIGHT;

    // Create table for layout
    var table = drawHelper.createLayoutTable();
    table.setAttribute("width", POP_UP_WIDTH);
    popUpDiv.appendChild(table);
    // First row contains close button
    var row = drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.setAttribute("align", "right");
    var img = document.createElement("img");
    img.src = "images/close.gif";
    img.onclick = me.closePopUp;
    cell.appendChild(img);
    // Second row contains just a label
    var row = drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.setAttribute("align", "center");
    label = document.createElement("label");
    label.setAttribute("class", "boldlabel");
    cell.appendChild(label);
    // Third row contains the input box
    var row = drawHelper.createLayoutRow();
    table.appendChild(row);
    inputCell = drawHelper.createLayoutCell();
    row.appendChild(inputCell);
    inputCell.setAttribute("align", "center");
    // Fourth row contains the submit button
    var row = drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = drawHelper.createLayoutCell();
    row.appendChild(cell);
    cell.setAttribute("align", "center");
    submitButton = document.createElement("input");
    cell.appendChild(submitButton);
    submitButton.setAttribute("type", "button");
    submitButton.setAttribute("value", "Enter");
    submitButton.setAttribute("class", "simplebuttoninputform");
    // Fifth row is a spacer row
    var row = drawHelper.createLayoutRow();
    table.appendChild(row);
    var cell = drawHelper.createLayoutCell();
    row.appendChild(cell);
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("height", "10");
    cell.appendChild(img);

    parentNode.appendChild(popUpDiv);
  };
};

// ***************************************************
// ***** CLASS: FormHelper ***************************
// ***************************************************
auxiliary.draw.FormHelper = function FormHelper()
{
  this.XHTMLNS = "http://www.w3.org/1999/xhtml";

  this.cell1Style = "font-family: verdana, sans-serif;" +
                    "font-size: 10px;" +
                    "font-weight: bold;";

  this.cell2Style = "font-family: verdana, sans-serif;" +
                    "font-size: 10px;" +
                    "font-weight: normal;";

  this.createSelectBox = function createSelectBox(selectBoxID, selectBoxClass, selectBoxOptions, onchange, selectBoxOptionsValues)
  {
    var select = document.createElement("select");
    select.setAttribute("id", selectBoxID);
    select.setAttribute("class", selectBoxClass);

    for (var i = 0; i < selectBoxOptions.length; i++)
      if (selectBoxOptionsValues)
	select.options[i] = new Option(selectBoxOptions[i], selectBoxOptionsValues[i]);
      else
	select.options[i] = new Option(selectBoxOptions[i], selectBoxOptions[i]);

    select.onchange = onchange;
    return select;
  };

  this.createTextBox = function createTextBox(textBoxID, textBoxClass, textBoxValue, textBoxMaxLength)
  {
    if (!textBoxMaxLength)
      textBoxMaxLength = "80";

    var input = document.createElement("input");
    input.setAttribute("type", "text");
    input.setAttribute("id", textBoxID);
    input.setAttribute("class", textBoxClass);
    input.setAttribute("value", textBoxValue);
    input.setAttribute("maxlength", textBoxMaxLength);
    return input;
  };

  this.createPasswordBox = function createPasswordBox(passwordBoxID, passwordBoxClass, passwordBoxMaxLength)
  {
    if (!passwordBoxMaxLength)
      passwordBoxMaxLength = "80";

    var input = document.createElement("input");
    input.setAttribute("type", "password");
    input.setAttribute("value", "");
    input.setAttribute("id", passwordBoxID);
    input.setAttribute("class", passwordBoxClass);
    input.setAttribute("maxlength", passwordBoxMaxLength);
    return input;
  };

  this.createButton = function createButton(buttonID, buttonClass, buttonText, onclick)
  {
    input = document.createElement("input");
    input.setAttribute("type", "button");
    input.setAttribute("id", buttonID);
    input.setAttribute("class", buttonClass);
    input.setAttribute("value", buttonText);
    input.onclick = onclick;
    return input;
  };

  this.createTextArea = function createTextArea(textAreaID, textAreaClass, textAreaRows, textAreaColumns)
  {
    var textArea = document.createElement("textarea");
    textArea.setAttribute("id", textAreaID);
    textArea.setAttribute("class", textAreaClass);
    textArea.setAttribute("rows", textAreaRows);
    textArea.setAttribute("cols", textAreaColumns);
    return textArea;
  };

  this.createTableForm = function createTableForm(tablecell, formcell, classname, value) 
  {
    var tr = document.createElementNS(this.XHTMLNS, "tr");

    var td = document.createElementNS(this.XHTMLNS, "td");
    tr.appendChild(td);
    td.setAttribute("style", this.cell1Style);
    td.appendChild(document.createTextNode(tablecell));

    td = document.createElementNS(this.XHTMLNS, "td");
    tr.appendChild(td);
    td.setAttribute("id", formcell + "Id");
    td.setAttribute("style", this.cell2Style);

    var form = document.createElementNS(this.XHTMLNS, "form");
    td.appendChild(form);
    form.setAttribute("name", formcell + "FormName");

    var input = document.createElement("input");
    form.appendChild(input);
    input.setAttribute("type", "text");
    input.setAttribute("id", formcell + "InputFormId");
    input.setAttribute("name", formcell + "InputFormName");
    input.setAttribute("value", value);
    input.setAttribute("size", "15");
    input.setAttribute("maxlength", "80");
    input.setAttribute("class", classname);

    return tr;
  };



  this.createTableEntry = function createTableEntry(cell1, cell2, classname, value) 
  {
    var tr = document.createElementNS(this.XHTMLNS, "tr");

    var td = document.createElementNS(this.XHTMLNS, "td");
    tr.appendChild(td);
    td.setAttribute("style", this.cell1Style);
    td.appendChild(document.createTextNode(cell1));

    td = document.createElementNS(this.XHTMLNS, "td");
    tr.appendChild(td);
    td.setAttribute("id", cell2 + "Id");
    td.setAttribute("class", classname);
    td.setAttribute("style", this.cell2Style);

    if (value != null)
      td.appendChild(document.createTextNode(value));
    else
      td.appendChild(document.createTextNode("---"));

    return tr;
  };

} // end class FormHelper



// ***************************************************
// ***** CLASS: DrawHelper ***************************
// ***************************************************
auxiliary.draw.DrawHelper = function DrawHelper()
{
  
  this.createAbsoluteDiv = function createAbsoluteDiv(id, divclass, xPos, yPos, width, height, zIndex, padding, border) 
  {
    var style = "position:absolute; top:" + yPos +
                "; left:" + xPos +
                "; width:" + width + 
                "; height:" + height + 
                "; z-index:" + zIndex +
                "; padding:" + padding +
                "; border:" + border + ";"
    var newdiv = document.createElement("div");

    newdiv.setAttribute("id", id);
    newdiv.setAttribute("class", divclass);
    newdiv.setAttribute("style", style);
    return newdiv;
  };

  this.createAbsoluteDivByWidth = function createAbsoluteDivByWidth(id, width, zIndex, padding, border) 
  {
    var style = "position:absolute; " +
                "; width:" + width + 
                "; z-index:" + zIndex +
                "; padding:" + padding +
                "; border:" + border + ";"
    var newdiv = document.createElement("div");

    newdiv.setAttribute("id", id);
    newdiv.setAttribute("style", style);
    return newdiv;
  };

  this.createUnsizedAbsoluteDiv = function createAbsoluteDivByWidth(id, zIndex, padding, border) 
  {
    var style = "position:absolute; " +
                "; z-index:" + zIndex +
                "; padding:" + padding +
                "; border:" + border + ";"
    var newdiv = document.createElement("div");

    newdiv.setAttribute("id", id);
    newdiv.setAttribute("style", style);
    return newdiv;
  };


  
  this.createRelativeDiv = function createRelativeDiv(id, divclass, xPos, yPos, width, height, zIndex, padding, border) 
  {
    var style = "position:relative; top:" + yPos + 
                "; left:" + xPos +
                "; width:" + width + 
                "; height:" + height + 
                "; z-index:" + zIndex +
                "; padding:" + padding + 
                "; border:" + border + ";";
    var newdiv = document.createElement("div");

    newdiv.setAttribute("id", id);
    newdiv.setAttribute("class", divclass);
    newdiv.setAttribute("style", style);
    return newdiv;
  };


  this.createLoadingDiv = function createLoadingDiv(xPos, yPos)
  {
    var style = "position:relative; top:" + yPos + 
                "; left:" + xPos +
                "; width:100px" + 
                "; height:50px" + 
                "; z-index:1" 
                "; padding:0px" + 
                "; border:0px;";

    var newdiv = document.createElement("div");
    newdiv.setAttribute("style", style);
     
    var image = document.createElement("img");
    image.src = "images/loading.gif";
    newdiv.appendChild(image);
    
    return newdiv;
  };


  this.addTextDiv = function addTextDiv(id, divclass, text, parent, numberUnits, textHeight) 
  {
    var textYPos =
      (parent.style.height.substring(0, parent.style.height.indexOf("px")) / 2) - textHeight;
    var style = "position:relative;";

    if (numberUnits != 1)
      style += " top:" + textYPos + ";";

    var newdiv = document.createElement("div");
    newdiv.setAttribute("id", id);
    newdiv.setAttribute("class", divclass);
    newdiv.setAttribute("style", style);
    var newText = document.createTextNode(text);
    newdiv.appendChild(newText);
    parent.appendChild(newdiv);
    return newdiv;
  };



  this.toggleVisibleByID = function toggleVisibleByID(id) 
  {
    var newdiv = document.getElementById(id);
    var visibility = newdiv.style.visibility;

    if (visibility == "visible" || visibility == "")
      newdiv.style.visibility = "hidden";
    else
      newdiv.style.visibility = "visible";
  };



  this.toggleVisibleByElement = function toggleVisibleByElement(element) 
  {
    if (!element)
      return;
	
    var visibility = element.style.visibility;

    if (visibility == "visible" || visibility == "")
      element.style.visibility = "hidden"; 
    else
      element.style.visibility = "visible";
  };



  this.drawNode = function drawNode(id, divclass, xPos, yPos, numberUnits, unitHeight,
        rackWidth, maxNodeLabelLength, textHeight, callback, textClass) 
  {

    if (textClass == null)
    {
      textClass = "nodetext";
    }

    var div = this.createAbsoluteDiv(
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
    var textDiv = this.addTextDiv(
            divID,
            textClass,
            auxiliary.hen.trimLabel(id, maxNodeLabelLength),
            div,
            numberUnits,
            textHeight);
    return div;
  };
    


  this.drawVerticalNode = function drawVerticalNode(id, divclass, xPos, yPos, numberUnits,
        unitHeight, rackWidth, numberLineBreaks, callback, textclass) 
  {
    var div = this.createAbsoluteDiv(
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

    var textDiv = this.createRelativeDiv(
        id + "text",
        divclass,
        0,
        0,
        rackWidth,
        (numberUnits * unitHeight) - 3,
        "1",
        "0px",
        "#000000 0px solid");
    textDiv.setAttribute("class", textclass);

    var innerHTML = "";
    for (var i = 0; i < numberLineBreaks; i++) 
    {
      innerHTML += "<br>";
    }

    for (var i = 0; i < id.length; i++) 
    {
      innerHTML += "&nbsp;" + id.charAt(i) + "<br>";
    }
    textDiv.innerHTML = innerHTML;
    div.appendChild(textDiv);
    
    return div;
  };



  this.drawBlankNode = function drawBlankNode(id, divclass, xPos, yPos, rackWidth, unitHeight) 
  {
    return this.createAbsoluteDiv(
        id,
        divclass,
        xPos,
        yPos,
        rackWidth,
        unitHeight - 1,
        "1",
        "0px",
        "#000000 1px solid");
  };



  this.drawVerticalBlankNode = function drawVerticalBlankNode(id, divclass, xPos, yPos, width, numberUnits, unitHeight) 
  {
    return this.createAbsoluteDiv(
        id,
        divclass,
        xPos,
        yPos,
        width,
        numberUnits * unitHeight - 1,
        "1",
        "0px",
        "#000000 1px solid");
  };



  this.drawButton = function drawButton(id, buttonClass, xPos, yPos, width, height, buttonText, callback, textHeight) 
  {
    var button = this.createAbsoluteDiv(
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
    var textDiv = this.addTextDiv(divID, buttonClass, buttonText, button, 2, textHeight);
    return button;
  };



  this.drawRelativeButton = function drawButton(id, buttonClass, xPos, yPos, width, height, buttonText, callback, textHeight) 
  {
    var button = this.createRelativeDiv(
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
    var textDiv = this.addTextDiv(divID, buttonClass, buttonText, button, 2, textHeight);
    return button;
  };


  
  this.drawUnitLabels = function drawUnitLabels(xPos, yPos, id, numberUnits, unitHeight, labelWidth, labelHeight, unitLabelClass) 
  {
    if (unitLabelClass == null)
    {
      unitLabelClass = "unitlabel";
    }
    labelsDiv = document.createElement("div");
    labelsDiv.setAttribute("id", "labelsDiv");

    for (var i = numberUnits; i > 0; i--) 
    {
      labelsDiv.appendChild(
          this.drawLabel(id + String(i) + "label",
            unitLabelClass,
            xPos,
            yPos + (numberUnits - i) * unitHeight,
            String(i),
            labelWidth,
            labelHeight));
    }

    return labelsDiv;
  };



  this.drawLabel = function drawLabel(id, labelClass, xPos, yPos, labelText, labelWidth, labelHeight) 
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

  
  this.createLayoutTable = function createLayoutTable()
  {
    var table = document.createElement("table");
    table.setAttribute("class", "draw-layouttable");
    return table;
  };

  this.createLayoutRow = function createLayoutRow()
  {
    var row = document.createElement("tr");
    row.setAttribute("class", "draw-layoutrow");
    return row;
  };

  this.createLayoutCell = function createLayoutCell()
  {
    var cell = document.createElement("td");
    cell.setAttribute("class", "draw-layoutcell");
    return cell;
  };

  this.createLayoutSpacerRow = function createLayoutSpacerRow(spacerHeight, colspan)
  {
    var row = document.createElement("tr");
    row.setAttribute("class", "draw-layoutrow");
    var cell = document.createElement("td");
    cell.setAttribute("colspan", colspan);
    row.appendChild(cell);
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("height", spacerHeight);
    cell.appendChild(img);
    return row;
  };

  this.createLayoutSpacerCell = function createLayoutSpacerCell(spacerWidth)
  {
    var cell = document.createElement("td");
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("width", spacerWidth);
    cell.appendChild(img);
    return cell;
  };

  this.createHorizontalSpacer = function createHorizontalSpacer(spacerWidth)
  {
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("width", spacerWidth);
    return img;
  };

  this.createVerticalSpacer = function createVerticalSpacer(spacerHeight)
  {
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("height", spacerHeight);
    return img;
  };

  this.createLabel = function createLabel(labelClass, labelText)
  {
    var label = document.createElement("label");
    label.setAttribute("class", labelClass);
    label.appendChild(document.createTextNode(labelText));
    return label;
  };
} // end class DrawHelper

