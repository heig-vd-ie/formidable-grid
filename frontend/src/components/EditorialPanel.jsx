import { FileUpload } from './FileUpload'
import { ActionButtons } from './ActionButtons'
import { CacheSelection } from './CacheSelection'
export { EditorPanel }

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
