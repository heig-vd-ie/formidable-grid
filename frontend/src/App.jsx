import { useState, useRef, useCallback } from 'react'
import './App.css'

// Resizer Component
function Resizer({ onResize }) {
  const isResizing = useRef(false)
  const startX = useRef(0)
  const startWidth = useRef(0)

  const handleMouseDown = useCallback((e) => {
    isResizing.current = true
    startX.current = e.clientX
    startWidth.current = parseInt(document.defaultView.getComputedStyle(e.target.previousElementSibling).width, 10)
    
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    
    // Prevent text selection during resize
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'col-resize'
  }, [])

  const handleMouseMove = useCallback((e) => {
    if (!isResizing.current) return
    
    const dx = e.clientX - startX.current
    const newWidth = startWidth.current + dx
    const containerWidth = document.querySelector('.main-layout').offsetWidth
    
    // Set minimum and maximum widths
    const minWidth = 300
    const maxWidth = containerWidth - 350 // Leave at least 350px for visualization panel
    
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      onResize(newWidth)
    }
  }, [onResize])

  const handleMouseUp = useCallback(() => {
    isResizing.current = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
    
    // Restore text selection
    document.body.style.userSelect = ''
    document.body.style.cursor = ''
  }, [handleMouseMove])

  return (
    <div 
      className="resizer" 
      onMouseDown={handleMouseDown}
    />
  )
}


// File Upload Component
function FileUpload({ selectedFile, onFileUpload }) {
  return (
    <div className="file-upload-section">
      <label className="file-upload-label"></label>
      <label className={`file-upload-area ${selectedFile ? 'file-selected' : ''}`}>
        <div className="file-upload-content">
          <svg className={`file-upload-icon ${selectedFile ? 'success' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
          </svg>
          <span className={`file-upload-text ${selectedFile ? 'success' : ''}`}>
            {selectedFile ? selectedFile.name : 'Choose file'}
          </span>
        </div>
        <input type="file" className="file-input" accept=".glm" onChange={onFileUpload} />
      </label>
    </div>
  )
}

// Action Buttons Component
function ActionButtons({ 
  selectedFile, 
  onSave, 
  onRun, 
  editorSaving, 
  loading, 
  showSaveSuccess, 
  showSaveError, 
  showRunSuccess, 
  showRunError,
  fileEditorContent 
}) {
  return (
    <div className="action-buttons">
      <button 
        onClick={onSave}
        disabled={!selectedFile || editorSaving || !fileEditorContent}
        className={`action-button save-button ${
          showSaveSuccess ? 'success' : 
          showSaveError ? 'error' : 
          (!selectedFile || editorSaving || !fileEditorContent ? 'disabled' : '')
        }`}
      >
        {editorSaving && <div className="spinner"></div>}
        <span className="button-icon">
          {showSaveSuccess ? '✅' : (showSaveError ? '❌' : '💾')}
        </span>
        <span>
          {editorSaving ? 'Saving...' : (showSaveSuccess ? 'Saved!' : (showSaveError ? 'Failed!' : 'Save'))}
        </span>
      </button>
      
      <button 
        onClick={onRun}
        disabled={!selectedFile || loading}
        className={`action-button run-button ${
          showRunSuccess ? 'success' : 
          showRunError ? 'error' : 
          (!selectedFile || loading ? 'disabled' : '')
        }`}
      >
        {loading && <div className="spinner"></div>}
        <span className="button-icon">
          {showRunSuccess ? '✅' : (showRunError ? '❌' : '🚀')}
        </span>
        <span>
          {loading ? 'Running...' : (showRunSuccess ? 'Success!' : (showRunError ? 'Failed!' : 'Run'))}
        </span>
      </button>
    </div>
  )
}

// Cache Selection Component
function CacheSelection({ selectedCache, onCacheChange, cacheFiles, onLoadVisualization, visualizationLoading }) {
  return (
    <div className="cache-selection">
      <div className="cache-controls">
        <select 
          value={selectedCache} 
          onChange={onCacheChange}
          className="cache-select"
        >
          <option value="">Choose cache file...</option>
          {cacheFiles.map(file => (
            <option key={file.name} value={file.name}>{file.name}</option>
          ))}
        </select>
        <button 
          onClick={onLoadVisualization}
          disabled={!selectedCache || visualizationLoading}
          className={`cache-load-button ${(!selectedCache || visualizationLoading) ? 'disabled' : ''}`}
        >
          {visualizationLoading && <div className="spinner"></div>}
          <span className="button-icon">📊</span>
          <span>{visualizationLoading ? 'Loading...' : 'Load'}</span>
        </button>
      </div>
    </div>
  )
}

// Editor Panel Component
function EditorPanel({ 
  editorCollapsed, 
  onToggleEditor, 
  selectedFile, 
  fileEditorContent, 
  onContentChange,
  onFileUpload,
  onSave,
  onRun,
  editorSaving,
  loading,
  showSaveSuccess,
  showSaveError,
  showRunSuccess,
  showRunError,
  selectedCache,
  onCacheChange,
  cacheFiles,
  onLoadVisualization,
  visualizationLoading,
  width
}) {
  if (editorCollapsed) return null;

  return (
    <div className="editor-panel" style={{ width: `${width}px` }}>
      <div className="editor-header">
        <div>
          {selectedFile && <span className="editor-filename">{selectedFile.name}</span>}
        </div>
        <button onClick={onToggleEditor} className="close-button">
          <svg className="close-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      
      <div className="editor-content">
        {selectedFile ? (
          <textarea 
            value={fileEditorContent}
            onChange={onContentChange}
            className="editor-textarea"
            placeholder="File content will appear here..."
          />
        ) : (
          <div className="editor-placeholder">
            <svg className="placeholder-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
          </div>
        )}
      </div>
      
      <div className="editor-controls">
        <FileUpload selectedFile={selectedFile} onFileUpload={onFileUpload} />
        <ActionButtons 
          selectedFile={selectedFile}
          onSave={onSave}
          onRun={onRun}
          editorSaving={editorSaving}
          loading={loading}
          showSaveSuccess={showSaveSuccess}
          showSaveError={showSaveError}
          showRunSuccess={showRunSuccess}
          showRunError={showRunError}
          fileEditorContent={fileEditorContent}
        />
        <CacheSelection 
          selectedCache={selectedCache}
          onCacheChange={onCacheChange}
          cacheFiles={cacheFiles}
          onLoadVisualization={onLoadVisualization}
          visualizationLoading={visualizationLoading}
        />
      </div>
    </div>
  )
}

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

// Main App Component
function App() {
  // State management
  const [editorCollapsed, setEditorCollapsed] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileEditorContent, setFileEditorContent] = useState('')
  const [editorSaving, setEditorSaving] = useState(false)
  const [loading, setLoading] = useState(false)
  const [showSaveSuccess, setShowSaveSuccess] = useState(false)
  const [showSaveError, setShowSaveError] = useState(false)
  const [showRunSuccess, setShowRunSuccess] = useState(false)
  const [showRunError, setShowRunError] = useState(false)
  const [selectedCache, setSelectedCache] = useState('')
  const [cacheFiles] = useState([]) // Placeholder for cache files
  const [visualizationLoading, setVisualizationLoading] = useState(false)
  const [visualizationLoaded, setVisualizationLoaded] = useState(false)
  const [editorWidth, setEditorWidth] = useState(400) // Default editor width

  // Event handlers
  const handleToggleEditor = () => {
    setEditorCollapsed(!editorCollapsed)
  }

  const handleResize = useCallback((newWidth) => {
    setEditorWidth(newWidth)
  }, [])

  const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (file) {
      setSelectedFile(file)
      // In a real implementation, you would read the file content here
      const reader = new FileReader()
      reader.onload = (e) => {
        setFileEditorContent(e.target.result)
      }
      reader.readAsText(file)
    }
  }

  const handleContentChange = (event) => {
    setFileEditorContent(event.target.value)
  }

  const handleSave = () => {
    // Placeholder for save functionality
    setEditorSaving(true)
    setTimeout(() => {
      setEditorSaving(false)
      setShowSaveSuccess(true)
      setTimeout(() => setShowSaveSuccess(false), 2000)
    }, 1000)
  }

  const handleRun = () => {
    // Placeholder for run functionality
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      setShowRunSuccess(true)
      setTimeout(() => setShowRunSuccess(false), 2000)
    }, 2000)
  }

  const handleCacheChange = (event) => {
    setSelectedCache(event.target.value)
  }

  const handleLoadVisualization = () => {
    // Placeholder for load visualization functionality
    setVisualizationLoading(true)
    setTimeout(() => {
      setVisualizationLoading(false)
      setVisualizationLoaded(true)
    }, 1500)
  }

  return (
    <div className="app">
      <div className="main-layout">
        <EditorPanel 
          editorCollapsed={editorCollapsed}
          onToggleEditor={handleToggleEditor}
          selectedFile={selectedFile}
          fileEditorContent={fileEditorContent}
          onContentChange={handleContentChange}
          onFileUpload={handleFileUpload}
          onSave={handleSave}
          onRun={handleRun}
          editorSaving={editorSaving}
          loading={loading}
          showSaveSuccess={showSaveSuccess}
          showSaveError={showSaveError}
          showRunSuccess={showRunSuccess}
          showRunError={showRunError}
          selectedCache={selectedCache}
          onCacheChange={handleCacheChange}
          cacheFiles={cacheFiles}
          onLoadVisualization={handleLoadVisualization}
          visualizationLoading={visualizationLoading}
          width={editorWidth}
        />
        {!editorCollapsed && <Resizer onResize={handleResize} />}
        <VisualizationPanel 
          editorCollapsed={editorCollapsed}
          onToggleEditor={handleToggleEditor}
          visualizationLoaded={visualizationLoaded}
        />
      </div>
    </div>
  )
}

export default App
