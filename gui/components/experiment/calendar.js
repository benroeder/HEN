/**
 * @fileoverview  Implements a table-based calendar
 * @version 0.1
 */
Namespace("components.experiment.calendar");
Import("auxiliary.hen", ".", "/");
Import("auxiliary.draw", ".", "/");

/**
 * Initializes a new calendar object
 * @class Calendar
 * @constructor
 * @param {int} numberColumns The number of columns for the calendar, including the column for labels
 * @param {int} columnWidth The width in pixels for each column
 * @param {int} rowHeight The height is pixels for each row
 * @param {array of auxiliary.hen.Experiment} experiemnts An array with the experiment information to display
 * @param {function} labelOnclickHandler The callback for labels
 * @param {function} dateOnclickHandler The callback for date cells
 * @param {String} calendarElementIDPrefix The prefix to use when assigning IDs to elements in the calendar
 * @param {String} cellIndexAttribute The attribute to set on a cell so that it can later be retrieved
 * @param {String} labelIDAttribute The attribute to set on a label so that it can later be retrieved
 * @param {String} username The id of the currently logged in user
 * @return A new Calendar object
 */
components.experiment.calendar.Calendar = function Calendar(numberColumns, columnWidth, rowHeight, experiments, labelOnclickHandler, dateOnclickHandler, calendarElementIDPrefix, cellIndexAttribute, labelIDAttribute, username)
{
  // Necessary to keep reference to 'this' for event handlers
  var me = this;
  // The number of columns in the calendar, including the column for labels
  var numberColumns = numberColumns;
  // The width of each column
  var columnWidth = columnWidth;
  // The height for each row
  var rowHeight = rowHeight;
  // An array of auxiliary.hen.Experiment objects
  var experiments = experiments;
  // The onclick handler for a date square
  var dateOnclickHandler = dateOnclickHandler;
  // The onclick handler for a label box
  var labelOnclickHandler = labelOnclickHandler;
  // The prefix to use when setting ids
  var calendarElementIDPrefix = calendarElementIDPrefix;
  // This attribute gets set in a cell so that it can be later retrieved
  var cellIndexAttribute = cellIndexAttribute;
  // Same as previous but for labels
  var labelIDAttribute = labelIDAttribute;
  // The id of the currently logged in user
  var username = username;
  // Used to create html elements with
  var drawHelper = new auxiliary.draw.DrawHelper();
  // Used to create form elements with
  var formHelper = new auxiliary.draw.FormHelper();
  // Used to convert numeric months to month names
  var months = new Array("January", "February", "March", "April", "May", "June", "July", "August",
                         "September", "October", "November", "December");
  // Used to keep track of the first date currently displayed on the calendar
  var currentlyDisplayedDate = null;
  // The colors of the squares representing allocations
  var allocatedColors = new Array();
  allocatedColors["unallocated"] = "#ccc";
  allocatedColors["user"] = "blue";
  allocatedColors["shared"] = "green";
  allocatedColors["other"] = "yellow";
  // Used to keep track of all the ids of nodes in the calendar
  var allNodeIDs = new Array();

  this.setAllocatedColor = function setAllocatedColor(allocationType, color)
  {
    if (allocationType == "unallocated" || allocationType == "user" ||
        allocationType == "shared" || allocationType == "other")
      allocatedColors[allocationType] = color;
  };

  var isInArray = function isInArray(item, theArray)
  {
    for (var i = 0; i < theArray.length; i++)
      if (theArray[i] == item)
	return true;
    return false;
  };

  /**
   * Creates an actual calendar with no allocations. Call {@link auxiliary.hen.Calendar#populateAllocations}
   * to color the allocations.
   * @return {HTMLTableElement} An HTML table containing the calendar
   */
  this.createCalendar = function createCalendar()
  {
    var calendarTable = drawHelper.createLayoutTable();
    currentlyDisplayedDate = new Date();

    // Create list with all the node ids
    for (var i = 0; i < experiments.length; i++)
    {
      var nodeIDs = experiments[i].getNodeIDs();
      for (var j = 0; j < nodeIDs.length; j++)
	if (!isInArray(allNodeIDs, nodeIDs[j]))
	  allNodeIDs.push(nodeIDs[j]);
    }

    // Need better sort method than this since this will place computer10 before computer8
    allNodeIDs.sort();

    // Legend row
    var row = drawHelper.createLayoutRow();
    calendarTable.appendChild(row);
    var cell = drawHelper.createLayoutCell();
    cell.setAttribute("colspan", numberColumns);
    cell.style.backgroundColor = "#ccc";
    cell.style.border = "1px solid";
    cell.setAttribute("valign", "middle");
    cell.setAttribute("align", "center");
    row.appendChild(cell);
    var legendTable = drawHelper.createLayoutTable();
    cell.appendChild(legendTable);
    var row = drawHelper.createLayoutRow();
    legendTable.appendChild(row);
    for (var key in allocatedColors)
    {
      var cell = drawHelper.createLayoutCell();
      row.appendChild(cell);
      var label = document.createElement("label");
      cell.appendChild(label);
      label.setAttribute("class", "largerboldlabel");
      label.appendChild(document.createTextNode(key));
      var cell = drawHelper.createLayoutCell();
      row.appendChild(cell);
      var div = document.createElement("div");
      div.setAttribute("class", "experiment-legenddiv");
      div.style.backgroundColor = allocatedColors[key];
      cell.appendChild(div);
      var cell = drawHelper.createLayoutCell();
      row.appendChild(cell);
      var img = document.createElement("img");
      img.src = "images/transparent.gif";
      img.setAttribute("width", "10");
      cell.appendChild(img);
    }

    // Add row that will contain the year labels
    var date = new Date();
    var row = drawHelper.createLayoutRow();
    calendarTable.appendChild(row);
    for (var j = 0; j < numberColumns; j++)
    {
      if (j == 0)
      {
	var cell = drawHelper.createLayoutCell();
	cell.setAttribute("align", "right");
	row.appendChild(cell);
	var label = document.createElement("label");
	cell.appendChild(label);
	label.setAttribute("class", "largerboldlabel");
	label.appendChild(document.createTextNode("year:"));
      }
      else
      {
	var cell = drawHelper.createLayoutCell();
	cell.setAttribute("align", "center");
	row.appendChild(cell);
	if ( (date.getDate() == 1 && date.getMonth() == 0) || (j == 1) )
	{
	  var label = document.createElement("label");
	  cell.appendChild(label);
	  label.setAttribute("id", calendarElementIDPrefix + "YearLabel" + j);
	  label.setAttribute("class", "largerboldlabel");
	  var theFullYear = new String(date.getFullYear());
	  label.appendChild(document.createTextNode(theFullYear.substring(2)));
	}
	// create placeholder labels
	else
	{
	  var label = document.createElement("label");
	  cell.appendChild(label);
	  label.setAttribute("id", calendarElementIDPrefix + "YearLabel" + j);
	  label.setAttribute("class", "largerboldlabel");
	}
	date.setDate(date.getDate() + 1);
      }
    }

    // Add row that will contain the month names and the step select box
    var date = new Date();
    var row = drawHelper.createLayoutRow();
    calendarTable.appendChild(row);
    for (var j = 0; j < numberColumns; j++)
    {
      if (j == 0)
      {
	var cell = drawHelper.createLayoutCell();
	cell.setAttribute("align", "center");
	row.appendChild(cell);
	var optionLabels = new Array("step:day", "step:week", "step:month");
	var optionValues = new Array(1, 7, 30);
	var selectBox = formHelper.createSelectBox(calendarElementIDPrefix + "StepSelectBoxId", 
                                                   "simpleveryshortdropdowninputform",
						   optionLabels, null, optionValues);
	cell.appendChild(selectBox);
      }
      else
      {
	var cell = drawHelper.createLayoutCell();
	cell.setAttribute("align", "center");
	row.appendChild(cell);
	if (date.getDate() == 1 || j == 1)
	{
	  var label = document.createElement("label");
	  cell.appendChild(label);
	  label.setAttribute("id", calendarElementIDPrefix + "MonthNameLabel" + j);
	  label.setAttribute("class", "boldlabel");
	  label.appendChild(document.createTextNode(months[date.getMonth()].substring(0, 3)));
	}
	// create place holder labels
	else
	{
	  var label = document.createElement("label");
	  cell.appendChild(label);
	  label.setAttribute("id", calendarElementIDPrefix + "MonthNameLabel" + j);
	  label.setAttribute("class", "boldlabel");
	}
	date.setDate(date.getDate() + 1);	
      }
    }

    // Add row that will contain the days of the month numbers and the back/forward arrows
    var date = new Date();
    var row = drawHelper.createLayoutRow();
    calendarTable.appendChild(row);
    for (var j = 0; j < numberColumns; j++)
    {
      if (j == 0)
      {
	var cell = drawHelper.createLayoutCell();
	cell.setAttribute("align", "center");
	row.appendChild(cell);
	var img = document.createElement("img");
	img.setAttribute("shiftCalendarButton", "back");
	img.src = "images/button_back.gif";
	img.onclick = me.shiftCalendar;
	cell.appendChild(img);
	var img = document.createElement("img");
	img.src = "images/transparent.gif";
	img.setAttribute("width", "5");
	cell.appendChild(img);
	var img = document.createElement("img");
	img.setAttribute("shiftCalendarButton", "next");
	img.src = "images/button_next.gif";
	img.onclick = me.shiftCalendar;
	cell.appendChild(img);
      }
      else
      {
	var cell = drawHelper.createLayoutCell();
	cell.setAttribute("align", "center");
	row.appendChild(cell);
	var label = document.createElement("label");
	cell.appendChild(label);
	label.setAttribute("class", "boldlabel");
	label.setAttribute("id", calendarElementIDPrefix + "MonthLabel" + j);
	label.appendChild(document.createTextNode(date.getDate()));
	date.setDate(date.getDate() + 1);
      }
    }

    // Add allocation rows
    for (var i = 0; i < allNodeIDs.length; i++)
    {
      var row = drawHelper.createLayoutRow();
      calendarTable.appendChild(row);
      for (var j = 0; j < numberColumns; j++)
      {
	var cell = drawHelper.createLayoutCell();
	row.appendChild(cell);
	cell.style.backgroundColor = allocatedColors["unallocated"];
	cell.setAttribute("allocated", "no");
	cell.style.border = "1px solid";

	// first column, labels
	if (j == 0)
	{
	  cell.onclick = labelOnclickHandler;
	  var label = document.createElement("label");
	  cell.appendChild(label);
	  cell.setAttribute(labelIDAttribute, allNodeIDs[i]);
	  label.setAttribute("class", "normallabel");
	  label.setAttribute(labelIDAttribute, allNodeIDs[i]);
	  label.appendChild(document.createTextNode(allNodeIDs[i]));
	  var img = document.createElement("img");
	  img.setAttribute(labelIDAttribute, allNodeIDs[i]);
	  img.src = "images/transparent.gif";
          img.setAttribute("width", "5");
	  cell.appendChild(img);
	}
	else
	{
	  cell.onclick = dateOnclickHandler;
	  cell.setAttribute("id", calendarElementIDPrefix + "AllocationCellId" + i + "-" + j);
	  var img = document.createElement("img");
	  img.setAttribute(cellIndexAttribute, i + "-" + j);
	  img.src = "images/transparent.gif";
	  img.setAttribute("height", rowHeight);
          img.setAttribute("width", columnWidth);
	  cell.appendChild(img);
	}

      }
    }

    return calendarTable;
  };
  
  /**
   * Colors the squares that represent a node allocation, as described by the experiment information
   * given to this class' constructor.
   */
  this.populateAllocations = function populateAllocations()
  {
    // First clear all colors from the date squares
    for (var i = 0; i < allNodeIDs.length; i++)
    {
      for (var j = 0; j < numberColumns; j++)
      {
	if (j != 0)
	  me.setCellColorByRowCol(i, j, allocatedColors["unallocated"]);
      }
    }

    for (var i = 0; i < allNodeIDs.length; i++)
    {
      var dateRanges = new Array();
      for (var j = 0; j < experiments.length; j++)
	{
	// If the current node is part of the current experiment
	if (isInArray(allNodeIDs[i], experiments[j].getNodeIDs()))
	{
	  var startDateRange = new Date();
	  startDateRange.setDate(experiments[j].getStartDate().substring(0, 2));
	  startDateRange.setMonth(experiments[j].getStartDate().substring(3, 5) - 1);
	  startDateRange.setFullYear(experiments[j].getStartDate().substring(6));

	  var endDateRange = new Date();
	  endDateRange.setDate(experiments[j].getEndDate().substring(0, 2));
	  endDateRange.setMonth(experiments[j].getEndDate().substring(3, 5) - 1);
	  endDateRange.setFullYear(experiments[j].getEndDate().substring(6));

	  dateRanges.push(new auxiliary.hen.DateRange(startDateRange, endDateRange, experiments[j].getExperimentID()));
	}
      }
      // We now have a list of date ranges for the node we're currently processing
      for (var j = 0; j < dateRanges.length; j++)
      {
	// Get the currently displayed begin and end range
	var currentlyDisplayedStartDate = new Date(currentlyDisplayedDate);	
	var currentlyDisplayedEndDate = new Date(currentlyDisplayedDate);
	currentlyDisplayedEndDate.setDate(currentlyDisplayedEndDate.getDate() + numberColumns - 2);
	var columnNumber = 0;

	while (isDateLessOrEqual(currentlyDisplayedStartDate, currentlyDisplayedEndDate))
	{
	  if (isDateInRange(currentlyDisplayedStartDate, dateRanges[j]))
	  {
	    var experimentID = dateRanges[j].getExperimentID();
	    var theUsername = null;
	    var shared = null;
	    // Get information about the experiment that the range belongs to to determine
	    // which color to paint the cell with
	    for (var k = 0; k < experiments.length; k++)
	      if (experiments[k].getExperimentID() == experimentID)
	      {
		theUsername = experiments[k].getUser().username;
		shared = experiments[k].getShared();
		break;
	      }
	    
	    var theColor = null;
	    if (theUsername == username)
	      theColor = allocatedColors["user"];
	    else if (shared == "yes")
	      theColor = allocatedColors["shared"];
	    else
	      theColor = allocatedColors["other"];

	    me.setCellColorByRowCol(i, columnNumber + 1, theColor);
	  }
	  currentlyDisplayedStartDate.setDate(currentlyDisplayedStartDate.getDate() + 1);
	  ++columnNumber;
	}
      }
    }
  };

  /**
   * Shifts the calendar on a per-day granularity based on the select box and arrow buttons provided.
   * @param {Event} evt Either the back or forward arrow button.
   */
  this.shiftCalendar = function shiftCalendar(evt)
  {
    var direction = evt.target.getAttribute("shiftCalendarButton");
    var step = document.getElementById(calendarElementIDPrefix + "StepSelectBoxId").value;
    if (direction == "back")
      step *= -1;
    // hack to force JavaScript to convert string to int
    else
      step *= 1;

    var newDate = new Date(currentlyDisplayedDate);
    newDate.setDate(newDate.getDate() + step);

    currentlyDisplayedDate = new Date(newDate);

    for (var j = 1; j < numberColumns; j++)
    {
      // Change the year labels
      var yearLabel = document.getElementById(calendarElementIDPrefix + "YearLabel" + j)
      try 
      {
	yearLabel.removeChild(yearLabel.firstChild);
      }
      catch (e) {}
      if ( (newDate.getDate() == 1 && newDate.getMonth() == 0) || (j == 1) )
      {
	var theFullYear = new String(newDate.getFullYear());
	yearLabel.appendChild(document.createTextNode(theFullYear.substring(2)));
      }

      // Change the month names labels
      var monthNameLabel = document.getElementById(calendarElementIDPrefix + "MonthNameLabel" + j);
      try 
      {
	monthNameLabel.removeChild(monthNameLabel.firstChild);
      }
      catch (e) {}

      if (newDate.getDate() == 1 || j == 1)
	monthNameLabel.appendChild(document.createTextNode(months[newDate.getMonth()].substring(0, 3)));
      
      // Change the number of the month labels
      var dayOfMonthLabel = document.getElementById(calendarElementIDPrefix + "MonthLabel" + j);
      dayOfMonthLabel.removeChild(dayOfMonthLabel.firstChild);
      dayOfMonthLabel.appendChild(document.createTextNode(newDate.getDate()));
      newDate.setDate(newDate.getDate() + 1);
    }

    // Color the appropriate cells for allocated nodes
    me.populateAllocations();
  };

  /**
   * Pops up an alert box displaying the user's id, the user's email, and the experiment id of the
   * cell whose id is given
   * @param {String} cellID The cell whose information is to be retrieved.
   */
  this.getCellInfo = function getCellInfo(cellID)
  {
    var row = cellID.substring(0, cellID.indexOf("-"));
    var column = cellID.substring(cellID.indexOf("-") + 1);
    var cell = document.getElementById(calendarElementIDPrefix + "AllocationCellId" + row + "-" + column);

    if (cell.getAttribute("allocated") == "no")
      return;

    // Hack to force JavaScript to force to convert string to int
    column *= 1;
    var cellDate = new Date(currentlyDisplayedDate);
    cellDate.setDate(cellDate.getDate() + column - 1);

    var nodeID = allNodeIDs[row];
    for (var i = 0; i < experiments.length; i++)
    {
      if (isInArray(nodeID, experiments[i].getNodeIDs()))
      {
	var startDateRange = new Date();
	startDateRange.setDate(experiments[i].getStartDate().substring(0, 2));
	startDateRange.setMonth(experiments[i].getStartDate().substring(3, 5) - 1);
	startDateRange.setFullYear(experiments[i].getStartDate().substring(6));

	var endDateRange = new Date();
	endDateRange.setDate(experiments[i].getEndDate().substring(0, 2));
	endDateRange.setMonth(experiments[i].getEndDate().substring(3, 5) - 1);
	endDateRange.setFullYear(experiments[i].getEndDate().substring(6));

	while (isDateLessOrEqual(startDateRange, endDateRange))
	{
	  if (areDatesEqual(startDateRange, cellDate))
	  {
	    var username = experiments[i].getUser().username;
	    var email = experiments[i].getUser().email;
	    alert("in use by " + username + ":" + email + " for experiment " + experiments[i].getExperimentID());
	  }

	  startDateRange.setDate(startDateRange.getDate() + 1);
	}
      }
    }
  };

  /**
   * Colors the calendar cell found at the intersection of the given row and column numbers
   * @param {int} row The row number of the cell to color
   * @param {int} column The column number of the cell to color
   */
  this.setCellColorByRowCol = function setCellColorByRowCol(row, column, color)
  {
    var cell = document.getElementById(calendarElementIDPrefix + "AllocationCellId" + row + "-" + column);
    if (color == allocatedColors["unallocated"])
      cell.setAttribute("allocated", "no");
    else 
      cell.setAttribute("allocated", "yes");
     
    cell.style.backgroundColor = color;
  };

  /**
   * Colors the calendar cell whose id is given.
   * @param cellID The id of the cell to color
   * @param color The color to paint the cell with
   */
  this.setCellColor = function setCellColor(cellID, color)
  {
    document.getElementById(calendarElementIDPrefix + "Cell" + cellID).style.backgroundColor = color;
  };

  /**
   * Returns true if the two dates are equal, false otherwise (times are ignored).
   * This function and the ones below are needed because JavaScript takes time into 
   * account when using the built-in comparison operator of the Date object.
   * @param {Date} date1 The first date to compare
   * @param {Date} date2 The second date to compare
   * @return {boolean} The result of the comparison
   */
  var areDatesEqual = function areDatesEqual(date1, date2)
  {
    if ((date1.getDate() == date2.getDate()) &&
	(date1.getMonth() == date2.getMonth()) &&
	(date1.getFullYear() == date2.getFullYear()))
      return true;
    return false;
  };

  /**
   * Returns true if date1 is less than or equal to date2, false otherwise.
   * @param {Date} date1 The first date to compare
   * @param {Date} date2 The second date to compare
   * @return {boolean} The result of the comparison
   */
  var isDateLessOrEqual = function isDateLessOrEqual(date1, date2)
  {
    if (areDatesEqual(date1, date2))
      return true;

    if (date1.getFullYear() < date2.getFullYear())
      return true;

    if (date1.getMonth() < date2.getMonth())
      return true;

    if (date1.getDate() < date2.getDate())
      return true;

    return false;
  };

  /**
   * Returns true if the given date is within the given range (range end points included), false otherwise
   * @param {Date} theDate The date to compare
   * @param {auxiliary.hen.DateRange} The date range
   * @return {boolean} The result of the comparison
   */
  var isDateInRange = function isDateInRange(theDate, dateRange)
  {
    // Must do the check by hand since the JavaScript Date class includes time in the built-in comparison
    if ( (theDate.getDate() >= dateRange.getStartDate().getDate()) &&
	 (theDate.getMonth() >= dateRange.getStartDate().getMonth()) &&
	 (theDate.getFullYear() >= dateRange.getStartDate().getFullYear()) &&
	 (theDate.getDate() <= dateRange.getEndDate().getDate()) &&
	 (theDate.getMonth() <= dateRange.getEndDate().getMonth()) &&
	 (theDate.getFullYear() <= dateRange.getEndDate().getFullYear()) )
      return true;
    return false;
  };

  /**
   * Returns true if date1 is strictly before date2, false otherwise.
   * @param {Date} date1 The first date to compare
   * @param {Date} date2 The second date to compare
   * @return {boolean} The result of the comparison
   */
  var isDateBeforeDate = function isDateBeforeDate(date1, date2)
  {
    if (areDatesEqual(date1, date2))
      return false;

    if (date1.getFullYear() > date2.getFullYear())
      return false;

    if (date1.getMonth() > date2.getMonth())
      return false;

    if (date1.getDate() > date2.getDate())
      return false;
    
    return true;
  };
  
}; // end class components.experiment.calendar.Calendar
