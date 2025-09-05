import { useEffect, useRef } from 'react'

export { VisualizationPanel }

// Visualization Panel Component
function VisualizationPanel({ editorCollapsed, onToggleEditor, visualizationLoaded, visualizationData }) {
  const visualizationRef = useRef(null)

  useEffect(() => {
    if (visualizationLoaded && visualizationData && visualizationRef.current) {
      // Clear previous visualization
      visualizationRef.current.innerHTML = ''
      
      try {
        // Create a simple visualization of the network data
        renderNetworkVisualization(visualizationData, visualizationRef.current)
      } catch (error) {
        console.error('Failed to render visualization:', error)
        visualizationRef.current.innerHTML = `
          <div class="error-message">
            <p>Failed to render visualization: ${error.message}</p>
          </div>
        `
      }
    }
  }, [visualizationLoaded, visualizationData])

  const renderNetworkVisualization = (data, container) => {
    // Create a simple text-based representation of the network
    // This is a placeholder - you can replace with D3.js or other visualization library
    const infoDiv = document.createElement('div')
    infoDiv.className = 'network-info'
    
    infoDiv.innerHTML = `
      <h3>Network: ${data.file || 'Unknown'}</h3>
      <div class="network-stats">
        <div class="stat">
          <span class="stat-label">Nodes:</span>
          <span class="stat-value">${data.graph?.nodes?.length || 0}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Links:</span>
          <span class="stat-value">${data.graph?.links?.length || 0}</span>
        </div>
      </div>
      <div class="network-data">
        <h4>Network Structure:</h4>
        <pre>${JSON.stringify(data.graph, null, 2)}</pre>
      </div>
    `
    
    container.appendChild(infoDiv)
  }
  return (
    <div className="visualization-panel">
      {editorCollapsed && (
        <button onClick={onToggleEditor} className="open-editor-button">
          <svg className="open-editor-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"></path>
          </svg>
        </button>
      )}
      
      <div id="main" className="visualization-content" ref={visualizationRef}>
        {!visualizationLoaded && (
          <div className="visualization-placeholder">
            <div className="placeholder-content">
              <svg className="visualization-placeholder-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
              <h3 className="placeholder-title">Network Visualization</h3>
              <p className="placeholder-text">
                {editorCollapsed && <span>Click the blue button to open the editor, or </span>}
                Upload a GLM file, run simulation, and load results to see the network visualization
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
