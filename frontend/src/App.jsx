import { useState, useCallback } from 'react'
import { Resizer } from './components/Resizer'
import { EditorPanel } from './components/EditorialPanel'
import { VisualizationPanel } from './components/VisualizationPanel'
import './App.css'

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
