import { useState } from 'react'
import NetworkVisualization from './NetworkVisualization'

export { VisualizationPanel }

// Visualization Panel Component
function VisualizationPanel({ editorCollapsed, onToggleEditor, visualizationLoaded, visualizationData }) {
  const [selectedNodeDetails, setSelectedNodeDetails] = useState(null)
  const [selectedLinkDetails, setSelectedLinkDetails] = useState(null)
  const [showDetailsModal, setShowDetailsModal] = useState(false)

  console.log('VisualizationPanel render:', { 
    visualizationLoaded, 
    visualizationData: visualizationData ? 'data present' : 'no data',
    dataKeys: visualizationData ? Object.keys(visualizationData) : null,
    fullData: visualizationData
  })

  const handleNodeDetails = (nodeData) => {
    setSelectedNodeDetails(nodeData)
    setSelectedLinkDetails(null)
    setShowDetailsModal(true)
  }

  const handleLinkDetails = (linkData) => {
    setSelectedLinkDetails(linkData)
    setSelectedNodeDetails(null)
    setShowDetailsModal(true)
  }

  const closeDetailsModal = () => {
    setShowDetailsModal(false)
    setSelectedNodeDetails(null)
    setSelectedLinkDetails(null)
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
      
      <div className="visualization-content">
        {visualizationLoaded && visualizationData ? (
          <div>
            <NetworkVisualization
              visualizationData={visualizationData}
              onNodeDetails={handleNodeDetails}
              onLinkDetails={handleLinkDetails}
            />
          </div>
        ) : (
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

      {/* Details Modal */}
      {showDetailsModal && (
        <div className="details-modal-overlay" onClick={closeDetailsModal}>
          <div className="details-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedNodeDetails ? 'Node Details' : 'Link Details'}</h3>
              <button onClick={closeDetailsModal} className="close-button">×</button>
            </div>
            <div className="modal-content">
              {selectedNodeDetails && (
                <div className="node-details">
                  <div className="detail-row">
                    <span className="detail-label">Name:</span>
                    <span className="detail-value">{selectedNodeDetails.name}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Class:</span>
                    <span className="detail-value">{selectedNodeDetails.classNm}</span>
                  </div>
                  {selectedNodeDetails.child && (
                    <div className="detail-row">
                      <span className="detail-label">Child:</span>
                      <span className="detail-value">{selectedNodeDetails.child}</span>
                    </div>
                  )}
                  {selectedNodeDetails.position && (
                    <div className="detail-row">
                      <span className="detail-label">Position:</span>
                      <span className="detail-value">
                        x: {Math.round(selectedNodeDetails.position.x)}, 
                        y: {Math.round(selectedNodeDetails.position.y)}
                      </span>
                    </div>
                  )}
                </div>
              )}
              {selectedLinkDetails && (
                <div className="link-details">
                  <div className="detail-row">
                    <span className="detail-label">Source:</span>
                    <span className="detail-value">{selectedLinkDetails.source}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Target:</span>
                    <span className="detail-value">{selectedLinkDetails.target}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Type:</span>
                    <span className="detail-value">{selectedLinkDetails.linkType}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
