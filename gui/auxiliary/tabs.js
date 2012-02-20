//**********************************************************************************
//**********************************************************************************
// Implements the auxiliary.tabs namespace
//
// CLASSES
// --------------------------------------------
// TabManager   Creates the tabs for the GUI and controls their visibility.
//
//**********************************************************************************
//**********************************************************************************
Namespace("auxiliary.tabs");
Import ("auxiliary.login", ".", "/");

// ***************************************************
// ***** CLASS: TabManager ***************************
// ***************************************************
auxiliary.tabs.TabManager = function(theTabs)
{
  // Necessary to keep reference to 'this' for event handlers 
  var me = this;
  // one of the above tab views at any one time 
  this.currentActiveTab = null;
  // the div container for all tabs 
  this.tabAreaDiv = null;
  // Keeps track of a user's information
  this.user = null;
  // An array of the tab objects, all inheriting from auxiliary.hen.Tab
  this.theTabs = theTabs;

  this.runManager = function runManager() 
  {
    // Sets the user property of each tab to the logged in user
    for (var i = 0; i < me.theTabs.length; i++)
      me.theTabs[i].setUser(me.user);

    // Show the first tab, if one exists
    if (me.theTabs.length > 0)
    {
      me.theTabs[0].setVisibility("visible");
      var firstTab = document.getElementById(me.theTabs[0].getTabLabel());
      firstTab.setAttribute("class", "tab activeTab");
      me.currentActiveTab = me.theTabs[0].getTabLabel();
    }
    else
    {
      alert("Either no tabs exist or you're not allowed access to any of them!!");
    }
  };

  this.createTabs = function createTabs() 
  {
    // The div that will contain all the tabs
    tabAreaDiv = document.createElement("div");
    tabAreaDiv.setAttribute("id", "tabAreaDiv");
    tabAreaDiv.setAttribute("class", "tabArea");
    document.body.appendChild(tabAreaDiv);


    // Remove tabs that the user is not allowed to access
    var filteredTabs = new Array();
    for (var i = 0; i < me.theTabs.length; i++)
      if (isUserAllowed(me.theTabs[i].getAllowedGroups()))
	filteredTabs.push(me.theTabs[i]);
    me.theTabs = filteredTabs;

    var div;
    var subDiv;
    for (var i = 0; i < me.theTabs.length; i++)
    {
      // Each of these holds the tab's label as well as all its elements
      div = document.createElement("div");
      div.setAttribute("id", me.theTabs[i].getTabLabel());
      div.appendChild(document.createTextNode(me.theTabs[i].getTabLabel()));
      div.onclick = me.toggleTabs;
      
      // Set the tab to look inactive
      div.setAttribute("class", "tab");
      
      // Have each tab subclass create the div that will hold all of the tab's elements
      subDiv = me.theTabs[i].createTab();
      div.appendChild(subDiv);
      tabAreaDiv.appendChild(div);
    }

    // Finally, add the tab that displays the currently logged user and the log out link
    div = document.createElement("div");
    div.setAttribute("id", "Login");
    
    subdiv = document.createElement("div");
    subdiv.setAttribute("class", "tabs-loggedinuserdiv");
    subdiv.appendChild(document.createTextNode("logged in as " + me.user.username));
    div.appendChild(subdiv);

    subdiv = document.createElement("div");
    subdiv.setAttribute("class", "tabs-loggedinuserdiv");
    var link = document.createElement("a");
    link.innerHTML = "Logout";
    link.href = "javascript:logout()";
    subdiv.appendChild(link);
    div.appendChild(subdiv);

    tabAreaDiv.appendChild(div);
  };



  this.toggleTabs = function toggleTabs(tab) 
  {
    tab = tab.target;
    if (tab.getAttribute("class") == "tab") 
    {
      var oldActiveTab = document.getElementById(me.currentActiveTab);
      oldActiveTab.setAttribute("class", "tab");
      tab.setAttribute("class", "tab activeTab");
      me.currentActiveTab = tab.getAttribute("id");

      children = tab.lastChild.childNodes;

      for (var i = 0; i < me.theTabs.length; i++)
      {
	if (me.theTabs[i].getTabLabel() == me.currentActiveTab)
	{
	  me.theTabs[i].setVisibility("visible");
	}
	else
	  me.theTabs[i].setVisibility("hidden");
      }
    }
  };


  var isUserAllowed = function isUserAllowed(tabGroups)
  {
    for (var i = 0; i < tabGroups.length; i++)
      for (var j = 0; j < me.user.groups.length; j++)
	if (tabGroups[i] == me.user.groups[j])
	  return true;
    return false;
  };


  this.theTabs[0].toggleTabs = me.toggleTabs;
} // end class TabManager
