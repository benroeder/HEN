//**********************************************************************************
//**********************************************************************************
// Implements the auxiliary.login namespace
//
// CLASSES
// --------------------------------------------
// LoginBox    Displays a login box with the fields username, password
//
//**********************************************************************************
//**********************************************************************************
Namespace ("auxiliary.login");
Import ("auxiliary.hen", ".", "/");
Import("auxiliary.draw", ".", "/");


// ***************************************************
// ***** CLASS: LoginBox *****************************
// ***************************************************
auxiliary.login.LoginBox = function(callback)
{
  // This is necessary so that event handlers in the class won't
  // lose a reference to the class itself
  var me = this;
  // Used to create various divs 
  this.drawHelper = new auxiliary.draw.DrawHelper();

  this.finishLoginPoll = null;
  this.pollTime = 100;
  this.loginCheckDone = false;
  this.loggedin = false;
  this.callback = callback;
  this.user = null;
  this.xmlHttp = null;
  this.ldapURL = "/cgi-bin/gui/auxiliary/ldaplogincheckcgi.py";
  this.username = null;
  this.password = null;

  var loginBoxWidth = 200;
  var loginBoxHeight = 150;
  var loginBoxFontSize = 10;
  var loginBoxPadding = 5;
  var loginBoxFontWeight = "bold";
  var loginBoxFontFamily = "verdana, sans-serif";
  var loginBoxBorder = "#000000 1px solid";
  var loginBoxBackgroundColor = "#ccc";
  var loginButtonWidth = 75;
  var loginButtonHeight = 20;
  var loginButtonFontHeight = 8;
  var loginButtonXPos = 0;
  var loginButtonYPos = 15;

  var mainDivYPos = 40;
  var mainDivXPos = 200;

  this.displayBox = function displayBox(loginBoxContainer, loginBoxId)
  {
    // Capture Enter key press
    document.onkeypress = keyPressHandler;

    this.callback = callback;

    // Div that contains all other elements
    var mainDiv = document.createElement("div");
    mainDiv.setAttribute("class", "login-maindiv");
    mainDiv.setAttribute("id", loginBoxId);
    mainDiv.style.top = mainDivYPos;
    mainDiv.style.left = mainDivXPos;
    mainDiv.style.width = loginBoxWidth;
    loginBoxContainer.appendChild(mainDiv);

    // Table used for layout
    var loginTable = document.createElement("table");
    loginTable.setAttribute("class", "login-table");
    loginTable.width = loginBoxWidth;
    mainDiv.appendChild(loginTable);

    // Welcome to HEN title
    var row = document.createElement("tr");
    loginTable.appendChild(row);
    var cell = document.createElement("td");
    cell.align = "center";
    row.appendChild(cell);
    titleLabel = document.createElement("label");
    titleLabel.setAttribute("class", "login-labeltitle");
    titleLabel.appendChild(document.createTextNode("Welcome to HEN"));
    cell.appendChild(titleLabel);

    // Spacer row
    var spacerRow = document.createElement("tr");
    loginTable.appendChild(spacerRow);
    var spacerCell = document.createElement("td");
    spacerCell.setAttribute("align", "center");
    spacerRow.appendChild(spacerCell);
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("height", "10");
    spacerCell.appendChild(img);

    // Login Box
    var row = document.createElement("tr");
    loginTable.appendChild(row);
    var cell = document.createElement("td");
    cell.align = "center";
    row.appendChild(cell);
    var loginPageDiv = document.createElement("div");
    cell.appendChild(loginPageDiv);
    loginPageDiv.setAttribute("align", "center");

    var style = "position: absolute;" +
      "font-family: " + loginBoxFontFamily + ";" +
      "font-size: " + loginBoxFontSize + "px;" +
      "font-weight: " + loginBoxFontWeight + ";" +
      //"top: " + loginBoxYPos + "px;" +
      //"left: " + loginBoxXPos + "px;" +
      "border: " + loginBoxBorder + ";" +
      "cursor: default;" +
      "background-color: " + loginBoxBackgroundColor + ";" +
      "visibility: visible;" +
      "width: " + loginBoxWidth + "px;" +
      "height: " + loginBoxHeight + "px;" +
      "padding: " + loginBoxPadding + "px;";

      
    loginPageDiv.setAttribute("style", style);

    // username
    var p = document.createElement("p");
    loginPageDiv.appendChild(p);
    
    var label = document.createElement("label");
    p.appendChild(label);

    label.setAttribute("for", "loginPageUsernameFormId");
    label.appendChild(document.createTextNode("Username"));
    
    var form = document.createElement("form");
    p.appendChild(form);
    form.setAttributeNS(null, "id", "loginPageUsernameFormId");
    form.setAttributeNS(null, "name", "loginPageUsernameFormName");
    form.onkeypress = null;

    
    var input = document.createElement("input");
    form.appendChild(input);
    input.setAttributeNS(null, "name", "loginPageUsernameInputBoxName");
    input.setAttributeNS(null, "type", "text");
    input.setAttribute("size", "22");
    input.setAttribute("class", "login-inputform");
    input.onkeypress = preventSubmit;

    // password
    var p = document.createElement("p");
    loginPageDiv.appendChild(p);
    
    var label = document.createElement("label");
    p.appendChild(label);
    label.setAttribute("for", "loginPagePasswordFormId");
    label.appendChild(document.createTextNode("Password"));
    
    var form = document.createElement("form");
    p.appendChild(form);
    form.setAttributeNS(null, "id", "loginPagePasswordFormId");
    form.setAttributeNS(null, "name", "loginPagePasswordFormName");
    form.onkeypress = preventSubmit;
    
    var input = document.createElement("input");
    form.appendChild(input);
    input.setAttributeNS(null, "name", "loginPagePasswordInputBoxName");
    input.setAttributeNS(null, "type", "password");
    input.setAttributeNS(null, "value", "");
    input.setAttribute("maxlength", "80");
    input.setAttribute("class", "login-inputform");
    input.onkeypress = preventSubmit;

    // Login button
    var p = document.createElement("p");
    loginPageDiv.appendChild(p);

    p.appendChild(me.drawHelper.drawRelativeButton("login-submitbutton", 
					   "login-submitbuttontext",
					   loginButtonXPos,
					   loginButtonYPos,
					   loginButtonWidth,
					   loginButtonHeight,
					   "Login",
					   me.doLogin,
					   loginButtonFontHeight));

    // Spacer row
    var spacerRow = document.createElement("tr");
    loginTable.appendChild(spacerRow);
    var spacerCell = document.createElement("td");
    spacerCell.setAttribute("align", "center");
    spacerRow.appendChild(spacerCell);
    var img = document.createElement("img");
    img.src = "images/transparent.gif";
    img.setAttribute("height", "175");
    spacerCell.appendChild(img);

    // Disclaimer
    var row = document.createElement("tr");
    loginTable.appendChild(row);
    var cell = document.createElement("td");
    cell.align = "center";
    row.appendChild(cell);
    titleLabel = document.createElement("label");
    titleLabel.setAttribute("class", "login-labeldisclaimer");
    titleLabel.appendChild(document.createTextNode("Access to and use of this system are restricted to authorised individuals"));
    cell.appendChild(titleLabel);

    // Set the focus (cursor) on the username field
    top.document.forms.loginPageUsernameFormName.loginPageUsernameInputBoxName.focus();
  };



  this.doLogin = function doLogin()
  {
    // save username and password
    var username = top.document.forms.loginPageUsernameFormName.loginPageUsernameInputBoxName.value;
    var password = top.document.forms.loginPagePasswordFormName.loginPagePasswordInputBoxName.value;

    if (username == "" || password == "") 
      {
	alert("You'll need to enter something in those boxes.");
	return;
      }

    me.checkLogin(username, password);

    me.finishLoginPoll = setInterval(me.finishLogin, me.pollTime);
  };


  this.finishLogin = function finishLogin()
  {
    if (me.loginCheckDone)
    {
      clearInterval(me.finishLoginPoll);
      if (me.user)
      {
	document.removeEventListener("onkeypress", keyPressHandler, false);
	me.callback();
      }
      else
      {
	alert("invalid login");
	me.loginCheckDone = false;
      }
    }
  };



  this.checkLogin = function checkLogin(username, password)
  {
    me.xmlHttp = new XMLHttpRequest();
    var requestPage = me.ldapURL ; //+ "?username=" + username + "&password=" + password;
    var queryString = "username=" + username + "&password=" + password;
    me.username = username;
    me.password = password;
    me.xmlHttp.onreadystatechange = me.handleLDAPReply;
    me.xmlHttp.open("POST", requestPage, true);
    me.xmlHttp.send(queryString);
  };


  this.handleLDAPReply = function handleLDAPReply() 
  {
    if (me.xmlHttp.readyState == 4) 
    {
      if (me.xmlHttp.status == 200) 
      {	
	var xmlDoc = me.xmlHttp.responseXML;
	var ldapResponse = xmlDoc.getElementsByTagName("ldapresponse")[0];
	var validLogin = auxiliary.hen.getAttributeValue(ldapResponse, "validlogin");

	if (validLogin == "True")
	{
	  var groups = new Array();
	  var groupTags = ldapResponse.getElementsByTagName("group");
	  for (var i = 0; i < groupTags.length; i++)
	    groups.push(auxiliary.hen.getAttributeValue(groupTags[i], "id"));

	  me.user = new auxiliary.hen.User(me.username, me.password, "", groups);
	}

	// If the login was invalid, simply don't set me.user and me.finishLogin will
	// display an alert. Either way the login check is finished.
	me.loginCheckDone = true;
      }
    }
  };

  
  var keyPressHandler = function keyPressHandler(event)
  {
    var key = (document.layers)?e.which:event.keyCode;

    if (key == 13)
    {
      me.doLogin();
    }
  };

  // This is here so that when the user hits enter while in the form, the form
  // does not try to submit (this event is handled by document.onkeypress)
  var preventSubmit = function preventSubmit(event)
  {
    var key = (document.layers)?e.which:event.keyCode;
    if (key == 13)
    {
      return false;
    }
  };

} // end class LoginBox
