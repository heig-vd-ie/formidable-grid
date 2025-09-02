
var width = 960,
    height = 760;

var myTitle, svg, container, force, drag, node, link, zoom;

// zooming
var min_zoom = .1;
var max_zoom = 5;

zoom = d3.behavior.zoom()
  .scaleExtent([min_zoom,max_zoom])
  .on("zoom",zoomed);

function zoomed() {
  container.attr("transform", "translate(" + d3.event.translate + ")scale("
  + d3.event.scale + ")");
}

// Function to load and visualize data
function loadNetworkVisualization() {
    // Clear existing visualization first
    d3.select("#main").selectAll("*").remove();
    
    // Recreate the basic structure
    myTitle = d3.select("#main").append("h1");
    
    svg = d3.select("#main")
      .append("div")
        .attr("class", "col")
      .append("svg")
        .attr("width", width)
        .attr("height", height);

    container = svg.append("g");
    
    // Reapply zoom behavior
    svg.call(zoom).on("dblclick.zoom", null);
    
    // initialize force
    force = d3.layout.force()
        .charge(-120)
        .linkDistance(30)
        .gravity(0.05)
        .size([width, height]);
    
    drag = force.drag().on("dragstart", dragstart);
    
    node = container.selectAll(".node");
    link = container.selectAll(".link");

    // load data
    d3.json("/data", function(error, mydata) {
      if (error) {
          console.error("Error loading data:", error);
          return;
      }

      // extract data from the json input
      var fileNm = mydata.file;
      var graph = mydata.graph;
      var fixedNodes = mydata.fixedNodes;

      myTitle.html(fileNm);

      link = link.data(graph.links)
          .enter().append("g")
          .attr("class", "link")
       // there is no value property. But varying line-width could be useful in the
       // future - keep
       //   .style("stroke-width", function(d) { return Math.sqrt(d.value); });
      // Note: I created the following line object in a 'g' container even though
      // it wasn't necessary in case I want to add something to the container later,
      // like an image - or text
      var line = link.append("line")

      // color the lines according to their type as defined by linkType property in
      // the JSON
      link.each(function(d){
    	if (d.linkType) {
    		d3.select(this).classed(d.linkType, true)
        }
      });

      // node 'g' container will contain the node circle and label
      node = node.data(graph.nodes)
          .enter().append("g")
          .attr("class", "node")
    	  .call(drag) // this command enables the dragging feature
	  .on("dblclick", dblclick);
    //.on("click",clickAction); // this was removed but can be used to display
    // a hidden chart

      node.each(function(d){
        if (d.classNm) {
    	  d3.select(this).classed(d.classNm, true)
    	}
      });
      node.each(function(d){
        if (d.child) {
    	  d3.select(this).classed(d.child, true)
    	}
      });

      var circle = node.append("circle")
    	.attr("r", 10)
    	.attr("class", function(d) { return d.classNm; });
    	//.style("fill", function(d) { return color(d.group); });
      var label = node.append("text")
        .text(function(d) { return d.name })
    	.attr("class", "nodeNm");

      // add labels at end so they are on top
      var lineLabel = link.append("g").append("text")
        .text(function(d) { return d.linkType });
      var nodeg = node.append("g")
        .append("text")
        .style("font-size",16)
        .text(function(d) {
          if (d.child){
            return d.classNm+":"+d.child;
          }
          else {
            return d.classNm;
          }
        })

      node.each(function(d){
        idNode = fixedNodes.names.indexOf(d.name)
        if (idNode>-1) {
        d3.select(this).classed("fixed", d.fixed = true);
        d.x=fixedNodes.x[idNode];
        d.y=fixedNodes.y[idNode];
      }
      });

      force
          .nodes(graph.nodes)
          .links(graph.links)
          .start();

      // update positions at every iteration ('tick') of the force algorithm
      force.on("tick",function(){
        line.attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });
        lineLabel.attr("x", function(d) { return (d.source.x+d.target.x)/2+8; })
          .attr("y", function(d) { return (d.source.y+d.target.y)/2+20; });
        circle.attr("cx", function(d) { return d.x; })
          .attr("cy", function(d) { return d.y; });
        label.attr("x", function(d) { return d.x + 8; })
          .attr("y", function(d) { return d.y; });
        nodeg.attr("x", function(d) { return d.x + 8; })
          .attr("y", function(d) { return d.y+20; });
      })
    });
}

// after a node has been moved manually it is now fixed
function dragstart(d) {
  d3.event.sourceEvent.stopPropagation();
  d3.select(this).classed("fixed", d.fixed = true);
}

// when you double click a fixed node, it is released
function dblclick(d) {
  d3.select(this).classed("fixed", d.fixed = false);
}

function saveXY(){
	var myStr = "data:text/csv;charset=utf-8,name,x,y\n";
	var nodeData = [];

	// Collect all node data with coordinates
	d3.selectAll("g.node").each(function(d) {
		// Get the circle element's position
		var circle = d3.select(this).select("circle");
		var cx = circle.attr("cx");
		var cy = circle.attr("cy");
		
		// If circle doesn't have cx/cy attributes, use the node's x/y data
		if (!cx || !cy) {
			cx = d.x;
			cy = d.y;
		}
		
		nodeData.push({
			name: d.name,
			x: cx,
			y: cy
		});
	});

	// Build CSV content
	for (var i = 0; i < nodeData.length; i++) {
		myStr = myStr + nodeData[i].name + "," + nodeData[i].x + "," + nodeData[i].y + "\n";
	}

	var encodedUri = encodeURI(myStr);
	var dummy = document.createElement("a");
	dummy.setAttribute("href", encodedUri);
	dummy.setAttribute("download", "xycoords.csv");
	document.body.appendChild(dummy);
	dummy.click(); // This will download the data file
}

function saveXYfixed(){
	var myStr = "data:text/csv;charset=utf-8,name,x,y\n";
	var nodeData = [];

	// Collect only fixed nodes data with coordinates
	d3.selectAll("g.node").each(function(d) {
		if (d.fixed) {
			// Get the circle element's position
			var circle = d3.select(this).select("circle");
			var cx = circle.attr("cx");
			var cy = circle.attr("cy");
			
			// If circle doesn't have cx/cy attributes, use the node's x/y data
			if (!cx || !cy) {
				cx = d.x;
				cy = d.y;
			}
			
			nodeData.push({
				name: d.name,
				x: cx,
				y: cy
			});
		}
	});

	// Build CSV content
	for (var i = 0; i < nodeData.length; i++) {
		myStr = myStr + nodeData[i].name + "," + nodeData[i].x + "," + nodeData[i].y + "\n";
	}

	var encodedUri = encodeURI(myStr);
	var dummy = document.createElement("a");
	dummy.setAttribute("href", encodedUri);
	dummy.setAttribute("download", "xycoords.csv");
	document.body.appendChild(dummy);
	dummy.click(); // This will download the data file
}


function nodeSearcher(){
		var targetNodeNm = document.getElementById('nodeSearchNm').value;
		d3.selectAll("g.node").each(
		function(d){
			a=1;
			if (d.name.indexOf(targetNodeNm)>-1){
				d3.select(this).classed("highlight", d.highlight = true);
			}
			else {
				d3.select(this).classed("highlight", d.highlight = false);
			}
		});
}

function changeLinkDistance(){
	// Not supported in current interface - keeping for legacy compatibility
	if (document.getElementById('linkLengthVal')) {
		force.linkDistance(Number(document.getElementById('linkLengthVal').value));
		force.start();
	}
}

function changeGravity(){
	force.gravity(Number(document.getElementById('gravityVal').value));
	force.start();
}

function changeCharge(){
	// Not supported in current interface - keeping for legacy compatibility
	if (document.getElementById('chargeVal')) {
		force.charge(Number(document.getElementById('chargeVal').value));
		force.start();
	}
}

// Make functions globally available for the new interface
window.loadNetworkVisualization = loadNetworkVisualization;
window.saveXY = saveXY;
window.saveXYfixed = saveXYfixed;
window.nodeSearcher = nodeSearcher;
window.changeGravity = changeGravity;
window.changeLinkDistance = changeLinkDistance;
window.changeCharge = changeCharge;
