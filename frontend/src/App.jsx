import { useState, useCallback, useEffect } from 'react'
import { Resizer } from './components/Resizer'
import { EditorPanel } from './components/EditorialPanel'
import { VisualizationPanel } from './components/VisualizationPanel'
import * as api from './utils/api'
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
  const [cacheFiles, setCacheFiles] = useState([])
  const [visualizationLoading, setVisualizationLoading] = useState(false)
  const [visualizationLoaded, setVisualizationLoaded] = useState(false)
  const [editorWidth, setEditorWidth] = useState(400) // Default editor width
  const [visualizationData, setVisualizationData] = useState(null)

  // Load cache files on component mount
  useEffect(() => {
    const loadCacheFiles = async () => {
      try {
        const response = await api.listCacheFiles()
        setCacheFiles(response.files || [])
      } catch (error) {
        console.error('Failed to load cache files:', error)
      }
    }
    
    loadCacheFiles()
  }, [])

  // Event handlers
  const handleToggleEditor = () => {
    setEditorCollapsed(!editorCollapsed)
  }

  const handleResize = useCallback((newWidth) => {
    setEditorWidth(newWidth)
  }, [])

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (file) {
      try {
        // Upload the file to the server
        const uploadResponse = await api.uploadGLMFile(file)
        
        if (uploadResponse.success) {
          setSelectedFile({
            name: uploadResponse.filename,
            originalFile: file
          })
          
          // Read the file content for the editor
          const readResponse = await api.readGLMFile(uploadResponse.filename)
          if (readResponse.success) {
            setFileEditorContent(readResponse.content)
          }
        }
      } catch (error) {
        console.error('Failed to upload file:', error)
        setShowSaveError(true)
        setTimeout(() => setShowSaveError(false), 3000)
      }
    }
  }

  const handleContentChange = (event) => {
    setFileEditorContent(event.target.value)
  }

  const handleSave = async () => {
    if (!selectedFile || !fileEditorContent) return
    
    setEditorSaving(true)
    setShowSaveSuccess(false)
    setShowSaveError(false)
    
    try {
      const response = await api.saveGLMFile(selectedFile.name, fileEditorContent)
      
      if (response.success) {
        setShowSaveSuccess(true)
        setTimeout(() => setShowSaveSuccess(false), 2000)
      } else {
        setShowSaveError(true)
        setTimeout(() => setShowSaveError(false), 3000)
      }
    } catch (error) {
      console.error('Failed to save file:', error)
      setShowSaveError(true)
      setTimeout(() => setShowSaveError(false), 3000)
    } finally {
      setEditorSaving(false)
    }
  }

  const handleRun = async () => {
    if (!selectedFile || !selectedFile.originalFile) return
    
    setLoading(true)
    setShowRunSuccess(false)
    setShowRunError(false)
    
    try {
      const response = await api.runPowerFlow(selectedFile.originalFile)
      
      if (response.success) {
        setShowRunSuccess(true)
        setTimeout(() => setShowRunSuccess(false), 2000)
        
        // Reload cache files after successful run
        const cacheResponse = await api.listCacheFiles()
        setCacheFiles(cacheResponse.files || [])
      } else {
        setShowRunError(true)
        setTimeout(() => setShowRunError(false), 3000)
      }
    } catch (error) {
      console.error('Failed to run simulation:', error)
      setShowRunError(true)
      setTimeout(() => setShowRunError(false), 3000)
    } finally {
      setLoading(false)
    }
  }

  const handleCacheChange = (event) => {
    setSelectedCache(event.target.value)
  }

  const handleLoadVisualization = async () => {
    if (!selectedCache) return
    
    setVisualizationLoading(true)
    
    try {
      // Load the cache data
      const loadResponse = await api.loadCacheData(selectedCache)
      
      if (loadResponse.success) {
        // Get visualization data
        const visualData = await api.getVisualizationData()
        setVisualizationData(visualData)
        setVisualizationLoaded(true)
      }
    } catch (error) {
      console.error('Failed to load visualization:', error)
    } finally {
      setVisualizationLoading(false)
    }
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
          visualizationData={visualizationData}
        />
      </div>
    </div>
  )
}

export default App
