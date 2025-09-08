export { ActionButtons }

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
