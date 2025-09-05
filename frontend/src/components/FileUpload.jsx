export { FileUpload }

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