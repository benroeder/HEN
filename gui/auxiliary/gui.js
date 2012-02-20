//**********************************************************************************
//**********************************************************************************
// Implements the auxiliary.gui namespace
//
// CLASSES
// --------------------------------------------
// GUI    Initializes the GUI, taking care of the login process
//
//**********************************************************************************
//**********************************************************************************
Namespace ("auxiliary.gui");
Import ("auxiliary.tabs", ".", "/");
Import ("auxiliary.login", ".", "/");
Import ("auxiliary.draw", ".", "/");

Import ("components.about.about", ".", "/"); 
Import ("components.physicallocation.physicallocation", ".", "/"); 
Import ("components.status.status", ".", "/"); 
Import ("components.experiment.experiment", ".", "/"); 
Import ("components.inventory.inventory", ".", "/"); 
Import ("components.power.power", ".", "/"); 
Import ("components.config.config", ".", "/"); 
Import ("components.network.network", ".", "/"); 

// ***************************************************
// ***** CLASS: GUI **********************************
// ***************************************************
auxiliary.gui.GUI = function()
{
  // Necessary to keep reference to 'this' for event handlers 
  var me = this;

  this.documentHead = head = document.getElementsByTagName('head').item(0);
  this.tabManager = null;
  this.loginBox = null;
  this.loginBoxId = "loginPageId";
  this.scriptsArray = new Array("auxiliary/tabs.js",
				"auxiliary/login.js",
				"auxiliary/hen.js",
				"auxiliary/draw.js",
				"components/about/about.js", 
				"components/physicallocation/physicallocation.js",
				"components/status/status.js",
				"components/inventory/inventory.js",
				"components/config/config.js",
				"components/power/power.js",
				"components/network/network.js",
				"components/experiment/experiment.js");
  this.cssLinksArray = new Array("auxiliary/hen.css",
				 "auxiliary/tabs.css",
				 "auxiliary/draw.css",
				 "auxiliary/login.css",
				 "components/about/about.css",
				 "components/experiment/experiment.css",
				 "components/inventory/inventory.css",
				 "components/physicallocation/physicallocation.css",
				 "components/config/config.css",
				 "components/power/power.css",
				 "components/network/network.css",
				 "components/status/status.css");
  


  this.runGUI = function runGUI()
  {
    if (this.browserCheck())
    {
      this.loadScripts(this.scriptsArray);
      this.loadCSSLinks(this.cssLinksArray);

      theTabs = new Array(); 
      theTabs.push(new components.about.about.AboutTab()); 
      theTabs.push(new components.physicallocation.physicallocation.PhysicalLocationTab()); 
      theTabs.push(new components.status.status.StatusTab()); 
      theTabs.push(new components.experiment.experiment.ExperimentTab()); 
      theTabs.push(new components.inventory.inventory.InventoryTab()); 
      theTabs.push(new components.power.power.PowerTab()); 
      theTabs.push(new components.network.network.NetworkTab()); 
      theTabs.push(new components.config.config.ConfigTab()); 
      this.tabManager = new auxiliary.tabs.TabManager(theTabs);

      this.loginBox = new auxiliary.login.LoginBox(me.loggedIn);
      this.loginBox.displayBox(document.body, me.loginBoxId);
    }
  };



  this.loadScripts = function loadScripts(scriptsArray)
  {
    for (var i = 0; i < scriptsArray.length; i++)
    {
      var script = document.createElement("script");
      script.src = scriptsArray[i];
      script.type = "text/javascript";
      this.documentHead.appendChild(script);      
    }
  };


  
  this.loadCSSLinks = function loadCSSLinks(cssLinksArray)
  {
    for (var i = 0; i < cssLinksArray.length; i++)
    {
      var link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = cssLinksArray[i];
      link.type = "text/css";
      this.documentHead.appendChild(link);      
    }
  };




  this.loggedIn = function loggedIn()
  {
    // delete the login page div
    var loginElement = document.getElementById(me.loginBoxId);
    loginElement.parentNode.removeChild(loginElement);

    // Populate user's information
    me.tabManager.user = me.loginBox.user;

    // Create the actual tabs
    me.tabManager.createTabs();

    // Start the tab manager
    me.tabManager.runManager();
  };


  this.browserCheck = function browserCheck()
  {
    var userAgent = navigator.userAgent;
    var browserName = navigator.appName;
    var versionOK = false;

    if (browserName == "Netscape")
    {
      var tmp = userAgent.split(" ");
      var browserDescription = tmp[tmp.length - 2];
      var browserVersion = browserDescription.substring(browserDescription.indexOf("/") + 1, 
							browserDescription.indexOf(".")) +
                           browserDescription.substring(browserDescription.indexOf(".") + 1, browserDescription.length);

      if (parseInt(browserVersion) < 15)
      {
	alert("You need at least Firefox 1.5.");
	return false;
      }
    }
    else
    {
      alert("We don't support IE at the moment.");
      return false;
    }
    return true;
  };

} // end class GUI



// Called on body.onload, creates and runs the GUI
function initialize()
{
  var theGUI = new auxiliary.gui.GUI();
  theGUI.runGUI();
}

function logout()
{
  location.reload(true);
}
