/**
 * Simulation and Cache Management Functions
 * Handles GridLAB-D simulation workflow and cache file operations
 */

/**
 * Load and populate cache files in the dropdown selector
 */
function loadCacheFiles() {
    const cacheSelect = document.getElementById('cacheFileSelect');
    
    fetch('/list_cache_files')
    .then(response => response.json())
    .then(data => {
        // Clear existing options except the first one
        cacheSelect.innerHTML = '<option value="">-- Select file to visualize --</option>';
        
        if (data.files && data.files.length > 0) {
            data.files.forEach(file => {
                const option = document.createElement('option');
                option.value = file.name;
                const modifiedDate = new Date(file.modified * 1000).toLocaleString();
                option.textContent = `${file.name} (${(file.size/1024).toFixed(1)}KB - ${modifiedDate})`;
                cacheSelect.appendChild(option);
            });
        }
    })
    .catch(error => {
        console.error('Error loading cache files:', error);
        // Add error option
        const errorOption = document.createElement('option');
        errorOption.value = '';
        errorOption.textContent = 'Error loading cache files';
        errorOption.disabled = true;
        cacheSelect.appendChild(errorOption);
    });
}

/**
 * Run GridLAB-D simulation on selected file
 * Step 1 of the workflow
 */
function runSimulationOnSelectedFile() {
    const fileInput = document.getElementById('simulationFileInput');
    const randomseed = document.getElementById('randomseed').value;
    const resultDiv = document.getElementById('simulationResult');
    
    // Check if a file is selected from computer
    if (!fileInput.files.length) {
        alert('Please select a GLM file from your computer.');
        return;
    }
    
    const selectedFile = fileInput.files[0];
    
    // Check if it's a GLM file
    if (!selectedFile.name.toLowerCase().endsWith('.glm')) {
        alert('Please select a valid GLM file.');
        return;
    }
    
    resultDiv.innerHTML = `<p>Running GridLAB-D simulation on ${selectedFile.name}...</p>`;
    
    // Create form data with the selected file
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('randomseed', randomseed);
    
    // Send to the run_gridlabd_with_file endpoint
    fetch('/run_gridlabd_with_file', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            let html = '<div style="color: green;"><strong>✅ Simulation completed successfully!</strong></div>';
            if (data.output_files && data.output_files.length > 0) {
                html += '<p><strong>Output files generated:</strong></p>';
                html += '<ul>';
                data.output_files.forEach(file => {
                    html += `<li>${file}</li>`;
                });
                html += '</ul>';
                html += '<p><em>💡 Go to Step 2 and click "Refresh" to load these results for visualization.</em></p>';
            }
            if (data.stdout) {
                html += '<details><summary>GridLAB-D Output</summary><pre>' + data.stdout + '</pre></details>';
            }
            resultDiv.innerHTML = html;
            // Refresh cache files list for Step 2
            loadCacheFiles();
        } else {
            let html = '<div style="color: red;"><strong>❌ Simulation failed!</strong></div>';
            if (data.stderr) {
                html += '<p><strong>Error:</strong></p><pre>' + data.stderr + '</pre>';
            }
            if (data.stdout) {
                html += '<p><strong>Output:</strong></p><pre>' + data.stdout + '</pre>';
            }
            resultDiv.innerHTML = html;
        }
    })
    .catch(error => {
        resultDiv.innerHTML = '<div style="color: red;">Error: ' + error.message + '</div>';
    });
}

/**
 * Load selected cache file for visualization
 * Step 2 of the workflow
 */
function loadSelectedCacheFile() {
    const cacheSelect = document.getElementById('cacheFileSelect');
    
    if (!cacheSelect.value) {
        alert('Please select a file from the cache first.');
        return;
    }
    
    // Load from cache
    fetch('/load_cache_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: cacheSelect.value })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ File loaded successfully: ' + data.filename);
            // Refresh the visualization
            window.location.reload();
        } else {
            alert('❌ Error loading file: ' + data.error);
        }
    })
    .catch(error => {
        alert('❌ Error: ' + error.message);
    });
}

/**
 * Initialize the application when DOM is loaded
 */
function initializeApp() {
    // Load cache files on page load
    loadCacheFiles();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeApp);
