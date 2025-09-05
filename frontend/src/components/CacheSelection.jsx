export { CacheSelection }

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