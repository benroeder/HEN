//**********************************************************************************
//**********************************************************************************
// Implements the components.about.about namespace
//
// CLASSES
// --------------------------------------------
// AboutTab    Displays and manages the "About" tab
//
//**********************************************************************************
//**********************************************************************************
Namespace ("components.about.about");
Import ("auxiliary.tabs", ".", "/");



// ***************************************************
// ***** CLASS: AboutTab *****************************
// ***************************************************
components.about.about.AboutTab = function()
{
  /* Necessary to keep reference to 'this' for event handlers */
  var me = this;
  this.toggleTabs = null;
  this.tabLabel = "About";
  this.allowedGroups.push("henmanager");
  this.allowedGroups.push("henuser");
  this.processManagementXHR = null;
  


  this.initTab = function initTab() 
  {
    var aboutElement = document.createElement("div");
    me.tabMainDiv.appendChild(aboutElement);
    aboutElement.setAttribute("id", "aboutPageId");

    var style = "position: absolute;" +
      "font-family: verdana, sans-serif;" +
      "width: 250px;" +
      "font-size: 10px;" +
      "font-weight: bold;" +
      "top: 40px;" +
      "left: 10px;" +
      "border: none;" +
      "cursor: default;" +
      "background-color: white;" +
      "padding: 5px;";
    aboutElement.setAttribute("style", style);


    // running process information
    var p = document.createElement("p");
    aboutElement.appendChild(p);
    p.appendChild(document.createTextNode("Running daemons"));
    var style = "position: relative;" +
      "width: 50%;" +
      "font-family: verdana, sans-serif;" +
      "font-size: 10px;" +
      "font-weight: bold;" +
      "border: none;" +
      "cursor: default;" +
      "background-color: lightblue;" +
      "padding: 5px;";
    p.setAttribute("style", style);

    var runningProcessDiv = document.createElement("div");
    aboutElement.appendChild(runningProcessDiv);
    runningProcessDiv.setAttribute("id", "runningProcessDivId");

    var style = "position: relative;" +
      "width: 50%;" +
      "font-family: verdana, sans-serif;" +
      "font-size: 10px;" +
      "font-weight: bold;" +
      "border: none;" +
      "cursor: default;" +
      "background-color: white;" +
      "padding: 5px;";
    runningProcessDiv.setAttribute("style", style);


    // stopped process information
    var p = document.createElement("p");
    aboutElement.appendChild(p);
    p.appendChild(document.createTextNode("Stopped daemons"));
    var style = "position: relative;" +
      "width: 50%;" +
      "font-family: verdana, sans-serif;" +
      "font-size: 10px;" +
      "font-weight: bold;" +
      "border: none;" +
      "cursor: default;" +
      "background-color: pink;" +
      "padding: 5px;";
    p.setAttribute("style", style);

    var stoppedProcessDiv = document.createElement("div");
    aboutElement.appendChild(stoppedProcessDiv);
    stoppedProcessDiv.setAttribute("id", "stoppedProcessDivId");

    var style = "position: relative;" +
      "width: 50%;" +
      "font-family: verdana, sans-serif;" +
      "font-size: 10px;" +
      "font-weight: bold;" +
      "border: none;" +
      "cursor: default;" +
      "background-color: white;" +
      "padding: 5px;";
    stoppedProcessDiv.setAttribute("style", style);

    var contentsDiv = document.createElement("div");
    aboutElement.appendChild(contentsDiv);
    contentsDiv.setAttribute("id", "contentsDivId");

    var style = "position: absolute;" +
      "font-family: verdana, sans-serif;" +
      "width: 800px;" +
      "font-size: 10px;" +
      "font-weight: normal;" +
      "top: 10px;" +
      "left: 200px;" +
      "border: none;" +
      "cursor: default;" +
      "background-color: white;" +
      "padding: 5px;";
    contentsDiv.setAttribute("style", style);

    var p = document.createElement("p");
    contentsDiv.appendChild(p);
    p.appendChild(document.createTextNode("Welcome to the HEN visualisation GUI."));

    var p = document.createElement("p");
    contentsDiv.appendChild(p);
    p.appendChild(document.createTextNode("The panels on the left represent running and stopped processes. Stopped processes need to be enabled or the tabs will not be accessible."));

    var p = document.createElement("p");
    contentsDiv.appendChild(p);
    p.appendChild(document.createTextNode("orphandetectd.py: This daemon checks for orphan nodes on the HEN network."));
    p.appendChild(document.createElement("br"));
    p.appendChild(document.createTextNode("temperatured.py: This daemon constantly updates the temperature readings from the sensors."));
    p.appendChild(document.createElement("br"));
    p.appendChild(document.createTextNode("managerd.py:"));
    p.appendChild(document.createElement("br"));
    p.appendChild(document.createTextNode("seriald.py: This daemon returns information of available serial consoles."));
    p.appendChild(document.createElement("br"));
    p.appendChild(document.createTextNode("serviceprocessord.py: This daemon returns information of available service processors."));
    p.appendChild(document.createElement("br"));
    p.appendChild(document.createTextNode("powerswitchd.py: This daemon returns information of available power switches."));
    p.appendChild(document.createElement("br"));
    p.appendChild(document.createTextNode("createconfigd.py: This is the daemon that writes the XML and creates the experiments on HEN, i.e. the boxes will be booted up, their interfaces setup, etc"));
    p.appendChild(document.createElement("br"));
    p.appendChild(document.createTextNode("orphanmanagerd.py: This is daemon searches for orphan machines on the network and keeps records of them."));
    me.processManagementXHRRequest()
    me.intervalID = setInterval(me.processManagementXHRRequest, 20 * 1000);  // 20 seconds timer

  };


  this.processManagementXHRRequest = function processManagementXHRRequest()
  {
    me.processManagementXHR = new XMLHttpRequest();
    me.processManagementXHR.onreadystatechange = me.processManagementXHRCallback;
    me.processManagementXHR.open("GET", "/cgi-bin/gui/components/about/monitorcgi.py", true);
    me.processManagementXHR.send(null);
  }

  this.processManagementXHRCallback = function processManagementXHRCallback()
  {

    if (me.processManagementXHR.readyState == 4) {
        if (me.processManagementXHR.status == 200) {
            var processmanagement = me.processManagementXHR.responseXML;

            var style = "font-family: verdana, sans-serif;" +
              "font-size: 10px;" +
              "font-weight: normal;";

            var running = processmanagement.getElementsByTagName("running")[0];
            var runningProcess = running.getElementsByTagName("process");

            // remove children
            var runningProcessDiv = document.getElementById("runningProcessDivId");
            while (runningProcessDiv.hasChildNodes()) {
                runningProcessDiv.removeChild(runningProcessDiv.lastChild);
            }

            for (var i = 0; i < runningProcess.length; i++) {
                var div = document.createElement("div");
                runningProcessDiv.appendChild(div);
                div.setAttribute("id", runningProcess[i].getAttribute("name"));
                div.setAttribute("class", "runningprocess");
                div.setAttribute("style", style);
                div.appendChild(document.createTextNode(runningProcess[i].getAttribute("name")));
            }

            var stopped = processmanagement.getElementsByTagName("stopped")[0];
            var stoppedProcess = stopped.getElementsByTagName("process");

            // remove children
            var stoppedProcessDiv = document.getElementById("stoppedProcessDivId");
            while (stoppedProcessDiv.hasChildNodes()) {
                stoppedProcessDiv.removeChild(stoppedProcessDiv.lastChild);
            }

            for (var i = 0; i < stoppedProcess.length; i++) {
                var div = document.createElement("div");
                stoppedProcessDiv.appendChild(div);
                div.setAttribute("id", stoppedProcess[i].getAttribute("name"));
                div.setAttribute("class", "stoppedprocess");
                div.setAttribute("style", style);
                div.appendChild(document.createTextNode(stoppedProcess[i].getAttribute("name")));

            }

            me.enableTabClickEvents();

        }
    }
  };


  this.enableTabClickEvents = function enableTabClickEvents()
  {
    /*
      var AboutTab = document.getElementById("About");
      var RacksTab = document.getElementById("Location");
      var TemperatureTab = document.getElementById("Temperature");
      var VlansTab = document.getElementById("Experiment");


      AboutTab.onclick = function() { me.toggleTabs(this); };
      VlansTab.onclick = function() { me.toggleTabs(this); };

      var runningProcessDiv = document.getElementById("runningProcessDivId");
      var runningChildren = runningProcessDiv.childNodes;

      // racks tab
      var allRunning = false;
      for (var i = 0; i < runningChildren.length; i++) {
          if (runningChildren[i].getAttribute("id") == "serialdaemon.py")
            allRunning = true;
          if (runningChildren[i].getAttribute("id") == "serviceprocessordaemon.py")
            allRunning = true;
          if (runningChildren[i].getAttribute("id") == "powerswitchdaemon.py")
            allRunning = true;
          if (runningChildren[i].getAttribute("id") == "OrphanManager.py")
            allRunning = true;
          if (runningChildren[i].getAttribute("id") == "PyTail.py")
            allRunning = true;
      }
      if (allRunning)
        RacksTab.onclick = function() { me.toggleTabs(this); };

      // temperature tab
      allRunning = false;
      for (var i = 0; i < runningChildren.length; i++) {
          if (runningChildren[i].getAttribute("id") == "tempdaemon.py")
            allRunning = true;
      }
      if (allRunning)
        TemperatureTab.onclick = function() { me.toggleTabs(this); };

      // vlan tab
      allRunning = false;
      for (var i = 0; i < runningChildren.length; i++) {
          if (runningChildren[i].getAttribute("id") == "ExperimentManager.py")
            allRunning = true;
          if (runningChildren[i].getAttribute("id") == "confdaemon2.py")
            allRunning = true;
      }
      if (allRunning)
        TemperatureTab.onclick = function() { me.toggleTabs(this); };
    */
  };
} // end class AboutTab

// Set up inheritance
components.about.about.AboutTab.prototype = new auxiliary.hen.Tab();
