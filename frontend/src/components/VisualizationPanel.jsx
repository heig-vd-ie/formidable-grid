export { VisualizationPanel }

// Visualization Panel Component
function VisualizationPanel({ editorCollapsed, onToggleEditor, visualizationLoaded }) {
  return (
    <div className="visualization-panel">
      {editorCollapsed && (
        <button onClick={onToggleEditor} className="open-editor-button">
          <svg className="open-editor-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"></path>
          </svg>
        </button>
      )}
      
      <div id="main" className="visualization-content">
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
