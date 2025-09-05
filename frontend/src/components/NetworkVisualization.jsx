import React, { useEffect, useRef, useCallback, useState } from 'react'
import * as d3 from 'd3'
import './NetworkVisualization.css'

const NetworkVisualization = ({ 
  visualizationData, 
  onNodeDetails, 
  onLinkDetails, 
  width = 800, 
  height = 600 
}) => {
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [gravity, setGravity] = useState(0.05)
  const [error, setError] = useState(null)
  
  // D3 variables - using refs to maintain state across renders
  const forceRef = useRef(null)
  const zoomRef = useRef(null)
  const nodesRef = useRef(null)
  const linksRef = useRef(null)

  // Get dynamic dimensions from the container
  const getDimensions = useCallback(() => {
    if (!containerRef.current) {
      console.log('No container ref available')
      return { width: 800, height: 600 }
    }
    const containerRect = containerRef.current.getBoundingClientRect()
    const dims = {
      width: Math.max(containerRect.width - 20, 400),
      height: Math.max(containerRect.height - 20, 300)
    }
    console.log('Container dimensions:', dims, 'from rect:', containerRect)
    return dims
  }, [])

  // Zoom function
  const zoomed = useCallback((event) => {
    const container = d3.select(svgRef.current).select('.zoom-container')
    container.attr('transform', `translate(${event.transform.x},${event.transform.y})scale(${event.transform.k})`)
  }, [])

  // Drag start function
  const dragstart = useCallback((event, d) => {
    if (!event.active) forceRef.current.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
    d3.select(event.sourceEvent.currentTarget).classed('fixed', d.fixed = true)
  }, [])

  // Node search function
  const nodeSearcher = useCallback(() => {
    if (!nodesRef.current || !searchTerm) return
    
    nodesRef.current.each(function(d) {
      const element = d3.select(this)
      if (d.name.indexOf(searchTerm) > -1) {
        element.classed('highlight', d.highlight = true)
      } else {
        element.classed('highlight', d.highlight = false)
      }
    })
  }, [searchTerm])

  // Change gravity function
  const changeGravity = useCallback((newGravity) => {
    if (forceRef.current) {
      // In D3 v6+, gravity is replaced with center force strength
      forceRef.current.force('center').strength(newGravity)
      forceRef.current.alpha(0.3).restart()
    }
  }, [])

  // Save coordinates functions
  const saveXY = useCallback(() => {
    if (!nodesRef.current) return
    
    let csvContent = "data:text/csv;charset=utf-8,name,x,y\n"
    const nodeData = []

    nodesRef.current.each(function(d) {
      const circle = d3.select(this).select('circle')
      const cx = circle.attr('cx') || d.x
      const cy = circle.attr('cy') || d.y
      
      nodeData.push({
        name: d.name,
        x: cx,
        y: cy
      })
    })

    nodeData.forEach(node => {
      csvContent += `${node.name},${node.x},${node.y}\n`
    })

    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', 'xycoords.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }, [])

  const saveXYfixed = useCallback(() => {
    if (!nodesRef.current) return
    
    let csvContent = "data:text/csv;charset=utf-8,name,x,y\n"
    const nodeData = []

    nodesRef.current.each(function(d) {
      if (d.fixed) {
        const circle = d3.select(this).select('circle')
        const cx = circle.attr('cx') || d.x
        const cy = circle.attr('cy') || d.y
        
        nodeData.push({
          name: d.name,
          x: cx,
          y: cy
        })
      }
    })

    nodeData.forEach(node => {
      csvContent += `${node.name},${node.x},${node.y}\n`
    })

    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', 'xycoords_fixed.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }, [])

  // Main visualization loading function
  const loadNetworkVisualization = useCallback(() => {
    console.log('loadNetworkVisualization called', { visualizationData, svgRef: svgRef.current })
    
    setError(null) // Clear any previous errors
    
    if (!visualizationData || !svgRef.current) {
      console.log('Early return - missing data or ref')
      return
    }

    console.log('Visualization data:', visualizationData)

    try {
      // Clear existing visualization
      d3.select(svgRef.current).selectAll('*').remove()

      const dims = getDimensions()
      const vizWidth = dims.width
      const vizHeight = dims.height

      // Create SVG structure
      const svg = d3.select(svgRef.current)
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${vizWidth} ${vizHeight}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .style('background-color', 'transparent')

      console.log('Created SVG with dimensions:', vizWidth, 'x', vizHeight)
      console.log('SVG element:', svg.node())

      const container = svg.append('g').attr('class', 'zoom-container')
      console.log('Created container:', container.node())

      // Setup zoom behavior
      const zoom = d3.zoom()
        .scaleExtent([0.1, 5])
        .on('zoom', zoomed)

      svg.call(zoom).on('dblclick.zoom', null)
      zoomRef.current = zoom

      // Initialize force layout (using D3 v6+ syntax)
      const force = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.name).distance(30))
        .force('charge', d3.forceManyBody().strength(-120))
        .force('center', d3.forceCenter(vizWidth / 2, vizHeight / 2))
        .force('collision', d3.forceCollide().radius(15))

      forceRef.current = force

      // Create drag behavior
      const drag = d3.drag()
        .on('start', dragstart)
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) force.alphaTarget(0)
          d.fx = null
          d.fy = null
        })

      // Extract data
      const graph = visualizationData.graph
      const fixedNodes = visualizationData.fixedNodes || { names: [], x: [], y: [] }

      console.log('Graph data:', graph)
      console.log('Nodes:', graph.nodes)
      console.log('Links:', graph.links)

      // Validate data structure
      if (!graph || !graph.nodes || !graph.links) {
        console.error('Invalid graph data structure:', graph)
        setError('Invalid graph data structure')
        return
      }

      if (graph.nodes.length === 0) {
        console.warn('No nodes in graph data')
        setError('No nodes found in graph data')
        return
      }

      console.log(`Found ${graph.nodes.length} nodes and ${graph.links.length} links`)    // Create links
    const linkSelection = container.selectAll('.link')
      .data(graph.links)
      .enter().append('g')
      .attr('class', 'link')
      .on('dblclick', (event, d) => {
        event.stopPropagation()
        if (onLinkDetails) {
          onLinkDetails({
            source: d.source.name || d.source,
            target: d.target.name || d.target,
            linkType: d.linkType,
            type: 'link'
          })
        }
      })
      .on('mouseover', function(event, d) {
        d3.select(this).style('cursor', 'pointer')
        d3.select(this).select('line').style('stroke-width', '3px')
      })
      .on('mouseout', function(event, d) {
        d3.select(this).style('cursor', 'default')
        d3.select(this).select('line').style('stroke-width', '2px')
      })

    // Add lines to links
    const lines = linkSelection.append('line')

    // Apply link types as CSS classes
    linkSelection.each(function(d) {
      if (d.linkType) {
        d3.select(this).classed(d.linkType, true)
      }
    })

    // Create nodes
    const nodeSelection = container.selectAll('.node')
      .data(graph.nodes)
      .enter().append('g')
      .attr('class', 'node')
      .call(drag)
      .on('dblclick', (event, d) => {
        event.stopPropagation()
        if (onNodeDetails) {
          onNodeDetails({
            name: d.name,
            classNm: d.classNm,
            child: d.child,
            position: { x: d.x, y: d.y }
          })
        }
      })
      .on('mouseover', function(event, d) {
        d3.select(this).classed('clickable', true)
      })
      .on('mouseout', function(event, d) {
        d3.select(this).classed('clickable', false)
      })

    // Apply node classes
    nodeSelection.each(function(d) {
      if (d.classNm) {
        d3.select(this).classed(d.classNm, true)
      }
      if (d.child) {
        d3.select(this).classed(d.child, true)
      }
    })

    // Add circles to nodes
    const circles = nodeSelection.append('circle')
      .attr('r', 10)
      .attr('class', d => d.classNm)

    // Add node labels
    const labels = nodeSelection.append('text')
      .text(d => d.name)
      .attr('class', 'nodeNm')

    // Add link labels
    const linkLabels = linkSelection.append('g').append('text')
      .text(d => d.linkType)

    // Add node type labels
    const nodeTypeLabels = nodeSelection.append('g')
      .append('text')
      .style('font-size', 16)
      .text(d => {
        if (d.child) {
          return `${d.classNm}:${d.child}`
        } else {
          return d.classNm
        }
      })

    // Set fixed nodes
    nodeSelection.each(function(d) {
      const idNode = fixedNodes.names.indexOf(d.name)
      if (idNode > -1) {
        d3.select(this).classed('fixed', d.fixed = true)
        d.fx = fixedNodes.x[idNode]
        d.fy = fixedNodes.y[idNode]
      }
    })

    // Start force simulation
    force
      .nodes(graph.nodes)
      .force('link').links(graph.links)

    force.on('tick', () => {
      lines
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)

      linkLabels
        .attr('x', d => (d.source.x + d.target.x) / 2 + 8)
        .attr('y', d => (d.source.y + d.target.y) / 2 + 20)

      circles
        .attr('cx', d => d.x)
        .attr('cy', d => d.y)

      labels
        .attr('x', d => d.x + 8)
        .attr('y', d => d.y)

      nodeTypeLabels
        .attr('x', d => d.x + 8)
        .attr('y', d => d.y + 20)
    })

    // Store references for other functions
    nodesRef.current = nodeSelection
    linksRef.current = linkSelection

    } catch (error) {
      console.error('Error rendering network visualization:', error)
      setError(error.message)
    }

  }, [visualizationData, getDimensions, zoomed, dragstart, gravity, onNodeDetails, onLinkDetails])

  // Load visualization when data changes
  useEffect(() => {
    console.log('NetworkVisualization useEffect triggered', { visualizationData })
    loadNetworkVisualization()
  }, [loadNetworkVisualization])

  // Debug: log when component mounts
  useEffect(() => {
    console.log('NetworkVisualization component mounted')
  }, [])

  // Update gravity when it changes
  useEffect(() => {
    changeGravity(gravity)
  }, [gravity, changeGravity])

  // Run search when search term changes
  useEffect(() => {
    nodeSearcher()
  }, [searchTerm, nodeSearcher])

  if (!visualizationData) {
    return (
      <div className="network-visualization-placeholder">
        <div className="placeholder-content">
          <svg className="visualization-placeholder-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
          </svg>
          <h3 className="placeholder-title">Network Visualization</h3>
          <p className="placeholder-text">
            Upload a GLM file, run simulation, and load results to see the network visualization
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="network-visualization-error">
        <div className="error-content">
          <h3>Visualization Error</h3>
          <p>Failed to render network visualization: {error}</p>
          <button onClick={() => setError(null)}>Try Again</button>
        </div>
      </div>
    )
  }

  return (
    <div className="network-visualization">
      {/* Controls */}
      <div className="visualization-controls">
        <div className="control-group">
          <label htmlFor="nodeSearch">Search Nodes:</label>
          <input
            id="nodeSearch"
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Enter node name..."
          />
        </div>
        
        <div className="control-group">
          <label htmlFor="gravityControl">Gravity:</label>
          <input
            id="gravityControl"
            type="range"
            min="0"
            max="0.2"
            step="0.01"
            value={gravity}
            onChange={(e) => setGravity(parseFloat(e.target.value))}
          />
          <span>{gravity.toFixed(2)}</span>
        </div>

        <div className="control-buttons">
          <button onClick={saveXY} title="Save all node coordinates">
            Save All Coordinates
          </button>
          <button onClick={saveXYfixed} title="Save fixed node coordinates">
            Save Fixed Coordinates
          </button>
        </div>
      </div>

      {/* Title */}
      <h2 className="visualization-title">
        {visualizationData.file || 'Network Visualization'}
      </h2>

      {/* Debug info */}
      <div style={{ padding: '1rem', backgroundColor: '#f0f0f0', fontSize: '12px' }}>
        <strong>Debug Info:</strong>
        <div>Nodes: {visualizationData.graph?.nodes?.length || 0}</div>
        <div>Links: {visualizationData.graph?.links?.length || 0}</div>
        <div>Fixed Nodes: {visualizationData.fixedNodes?.names?.length || 0}</div>
        {error && <div style={{ color: 'red' }}>Error: {error}</div>}
      </div>

      {/* Main visualization container */}
      <div className="visualization-container" ref={containerRef}>
        <svg ref={svgRef} className="network-svg"></svg>
      </div>

      {/* Legend */}
      <div className="visualization-legend">
        <div className="legend-section">
          <h4>Node Types</h4>
          <div className="legend-items">
            <div className="legend-item">
              <div className="legend-color circle legend-load"></div>
              <span>Load</span>
            </div>
            <div className="legend-item">
              <div className="legend-color circle legend-capacitor"></div>
              <span>Capacitor</span>
            </div>
            <div className="legend-item">
              <div className="legend-color circle legend-meter"></div>
              <span>Meter</span>
            </div>
            <div className="legend-item">
              <div className="legend-color circle legend-diesel"></div>
              <span>Diesel Generator</span>
            </div>
            <div className="legend-item">
              <div className="legend-color circle legend-node"></div>
              <span>Node</span>
            </div>
          </div>
        </div>
        
        <div className="legend-section">
          <h4>Link Types</h4>
          <div className="legend-items">
            <div className="legend-item">
              <div className="legend-color legend-overhead"></div>
              <span>Overhead Line</span>
            </div>
            <div className="legend-item">
              <div className="legend-color legend-underground dashed"></div>
              <span>Underground Line</span>
            </div>
            <div className="legend-item">
              <div className="legend-color legend-switch dashed"></div>
              <span>Switch</span>
            </div>
            <div className="legend-item">
              <div className="legend-color legend-regulator"></div>
              <span>Regulator</span>
            </div>
            <div className="legend-item">
              <div className="legend-color legend-transformer"></div>
              <span>Transformer</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NetworkVisualization
