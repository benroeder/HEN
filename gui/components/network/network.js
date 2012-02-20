Namespace ("components.network.network");
Import ("auxiliary.draw", ".", "/");
Import ("auxiliary.hen", ".", "/");
Import ("components.network.canvas", ".", "/");

components.network.network.NetworkTab = function()
{
  // Used by the SVG canvas to interact with the rest of the tab
  window.experimentTabSVGCanvas = new components.experiment.canvas.SVGCanvas();

  // Necessary to keep reference to 'this' for event handlers 
  var me = this;
  // Only users belonging to the manager group are allowed access to this tab
  this.allowedGroups.push("henmanager");
  this.allowedGroups.push("henuser");
  // The tab's name
  this.tabLabel = "Network";

  // Used to create various div elements
  this.drawHelper = new auxiliary.draw.DrawHelper();
  // Controls power to nodes
  this.layoutURL = "/cgi-bin/gui/components/network/topologycgi.py";
  // The height of the canvas
  this.CANVAS_HEIGHT = 800;
  // The width of the canvas
  this.CANVAS_WIDTH = 900;
  // The x position of the canvas
  this.CANVAS_X_POSITION = 20;
  // The y position of the canvas
  this.CANVAS_Y_POSITION = 40;

  this.user = null;
  this.mainDiv = null;
  this.mainNameDiv = null;

  this.initTab = function initTab() 
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
    //me.canvasTabDivs.push(topologyDiv);
    me.visibilityDivs.push(topologyDiv);

    // Embed SVG object into topology tab
    var embed = document.createElement("embed");
    topologyDiv.appendChild(embed);
    embed.setAttribute("src", this.layoutURL);
    // embed.setAttribute("src", "components/network/canvas.svg");	
    embed.setAttribute("width", me.CANVAS_WIDTH);
    embed.setAttribute("height", me.CANVAS_HEIGHT);
    embed.setAttribute("type", "image/svg+xml");
  };

  function networkTabClick(evt)
  {
	alert(evt)
  };

} // end class NetworkTab

// Set up inheritance
components.network.network.NetworkTab.prototype = new auxiliary.hen.Tab();