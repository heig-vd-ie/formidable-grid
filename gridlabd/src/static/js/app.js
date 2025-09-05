// GridLAB-D Network Plotter Application - Streamlined Version
function gridLabApp() {
    return {
        // Core Application State
        selectedFile: null,
        selectedFileData: null, // Store file data to avoid stale File object issues
        randomSeed: 42,
        selectedCache: '',
        cacheFiles: [],
        loading: false,
        visualizationLoading: false,
        visualizationLoaded: false,
        simulationResult: '',
        simulationSuccess: false,
        
        // Advanced Options State
        nodeSearchTerm: '',
        gravityValue: 0.05,
        
        // Legend filter state
        legendFilters: {
            links: {
                overhead_line: true,
                underground_line: true,
                switch: true,
                regulator: true,
                transformer: true
            },
            nodes: {
                load: true,
                capacitor: true,
                meter: true,
                diesel_dg: true,
                node: true
            }
        },

        // Detail modal state
        showDetailModal: false,
        selectedNodeDetails: null,
        showResultsModal: false,
        simulationResults: null,
        resultsLoading: false,

        // File editor state
        fileEditorContent: '',
        editorSaving: false,
        editorMessage: '',
        editorMessageType: 'success', // 'success' or 'error'
        editorCollapsed: false, // Controls whether editor panel is shown

        // Initialize application
        init() {
            this.loadCacheFiles();
        },

        // CORE FUNCTIONALITY 1: Load GLM File
        async handleFileUpload(event) {
            const file = event.target.files[0];
            this.selectedFile = file;
            
            if (file) {
                this.simulationResult = '';
                this.simulationSuccess = false;
                this.editorMessage = '';
                
                // Store file data to avoid stale File object issues
                try {
                    this.selectedFileData = {
                        name: file.name,
                        type: file.type,
                        size: file.size,
                        arrayBuffer: await file.arrayBuffer()
                    };
                    
                    // Read file content and display in editor
                    const text = new TextDecoder().decode(this.selectedFileData.arrayBuffer);
                    this.fileEditorContent = text;
                    
                    console.log('File data stored:', this.selectedFileData.name);
                } catch (error) {
                    console.error('Error reading file:', error);
                    this.selectedFileData = null;
                    this.fileEditorContent = '';
                }
            } else {
                this.selectedFileData = null;
                this.fileEditorContent = '';
            }
        },

        // CORE FUNCTIONALITY 2: Run Simulation
        async runSimulation() {
            if (!this.selectedFileData) {
                this.simulationResult = 'Please select a GLM file first.';
                return;
            }
            
            this.loading = true;
            this.simulationResult = '';
            this.simulationSuccess = false;
            
            try {
                // Create fresh file from stored data each time
                const file = new File(
                    [this.selectedFileData.arrayBuffer], 
                    this.selectedFileData.name, 
                    { type: this.selectedFileData.type }
                );
                
                // Create fresh FormData each time
                const formData = new FormData();
                formData.append('file', file);
                formData.append('randomseed', this.randomSeed || '42');

                console.log('Sending request to /run-powerflow with file:', file.name, 'size:', file.size);

                const response = await fetch('/run-powerflow', {
                    method: 'POST',
                    body: formData
                });
                
                console.log('Response status:', response.status);
                console.log('Response ok:', response.ok);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                console.log('Response data:', result);
                
                if (result.success) {
                    this.simulationResult = `Simulation completed successfully! Output: ${result.output_file}`;
                    this.simulationSuccess = true;
                    await this.loadCacheFiles();
                } else {
                    this.simulationResult = `Simulation failed: ${result.error}`;
                    this.simulationSuccess = false;
                }
            } catch (error) {
                console.error('Simulation error:', error);
                this.simulationResult = `Error: ${error.message}`;
                this.simulationSuccess = false;
            } finally {
                this.loading = false;
            }
        },

        // CORE FUNCTIONALITY 3: Load Results from Cache
        async loadCacheFiles() {
            try {
                const response = await fetch('/list_cache_files');
                const data = await response.json();
                this.cacheFiles = data.files || [];
            } catch (error) {
                console.error('Error loading cache files:', error);
                this.cacheFiles = [];
            }
        },

        async loadVisualization() {
            if (!this.selectedCache) return;
            
            this.visualizationLoading = true;
            
            try {
                const response = await fetch('/load_cache_data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ filename: this.selectedCache })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.visualizationLoaded = true;
                    this.resetLegendFilters();
                    
                    if (typeof loadNetworkVisualization === 'function') {
                        setTimeout(() => {
                            loadNetworkVisualization();
                        }, 100);
                    }
                } else {
                    alert('Failed to load visualization: ' + result.error);
                }
            } catch (error) {
                console.error('Error loading visualization:', error);
                alert('Error loading visualization: ' + error.message);
            } finally {
                this.visualizationLoading = false;
            }
        },

        // CORE FUNCTIONALITY 4: Advanced Options
        
        // Zoom controls
        zoomIn() {
            if (window.zoom) {
                const currentScale = window.zoom.scale();
                const newScale = Math.min(currentScale * 1.2, 5);
                window.zoom.scale(newScale);
                window.zoom.event(d3.select("#main svg"));
            }
        },

        zoomOut() {
            if (window.zoom) {
                const currentScale = window.zoom.scale();
                const newScale = Math.max(currentScale * 0.8, 0.1);
                window.zoom.scale(newScale);
                window.zoom.event(d3.select("#main svg"));
            }
        },

        resetZoom() {
            if (window.zoom) {
                window.zoom.scale(1);
                window.zoom.translate([0, 0]);
                window.zoom.event(d3.select("#main svg"));
            }
        },

        // Export coordinates
        saveXY() {
            if (typeof window.saveXY === 'function') {
                window.saveXY();
            } else {
                alert('No visualization loaded');
            }
        },

        saveXYfixed() {
            if (typeof window.saveXYfixed === 'function') {
                window.saveXYfixed();
            } else {
                alert('No visualization loaded');
            }
        },

        // Node search
        searchNode() {
            if (typeof window.nodeSearcher === 'function') {
                document.getElementById('nodeSearchNm').value = this.nodeSearchTerm;
                window.nodeSearcher();
            } else {
                alert('No visualization loaded');
            }
        },

        // Gravity control
        changeGravity() {
            if (typeof window.changeGravity === 'function') {
                document.getElementById('gravityVal').value = this.gravityValue;
                window.changeGravity();
            } else {
                alert('No visualization loaded');
            }
        },

        // Legend filtering
        toggleLegendItem(type, itemType) {
            if (type === 'link') {
                this.legendFilters.links[itemType] = !this.legendFilters.links[itemType];
            } else if (type === 'node') {
                this.legendFilters.nodes[itemType] = !this.legendFilters.nodes[itemType];
            }
            this.applyLegendFilters();
        },

        applyLegendFilters() {
            if (!this.visualizationLoaded) return;
            
            Object.keys(this.legendFilters.links).forEach(linkType => {
                const isVisible = this.legendFilters.links[linkType];
                d3.selectAll('.link.' + linkType)
                    .style('display', isVisible ? 'block' : 'none');
            });
            
            Object.keys(this.legendFilters.nodes).forEach(nodeType => {
                const isVisible = this.legendFilters.nodes[nodeType];
                if (nodeType === 'node') {
                    d3.selectAll('.node:not(.load):not(.meter):not(.diesel_dg):not(.capacitor)')
                        .style('display', isVisible ? 'block' : 'none');
                } else {
                    d3.selectAll('.node.' + nodeType)
                        .style('display', isVisible ? 'block' : 'none');
                }
            });
        },

        resetLegendFilters() {
            // Reset all filters to true
            Object.keys(this.legendFilters.links).forEach(linkType => {
                this.legendFilters.links[linkType] = true;
            });
            Object.keys(this.legendFilters.nodes).forEach(nodeType => {
                this.legendFilters.nodes[nodeType] = true;
            });
            this.applyLegendFilters();
        },

        // Detail modal functions (Advanced)
        showNodeDetails(nodeData) {
            this.selectedNodeDetails = nodeData;
            this.showDetailModal = true;
        },

        showLinkDetails(linkData) {
            // For links, we'll fetch the link details and show them in the modal
            this.fetchLinkDetailsAndShow(linkData);
        },

        async fetchLinkDetailsAndShow(linkData) {
            try {
                const loadingLinkData = {
                    ...linkData,
                    type: 'link',
                    loading: true,
                    name: `${linkData.linkType} (${linkData.source} → ${linkData.target})`
                };
                
                this.selectedNodeDetails = loadingLinkData;
                this.showDetailModal = true;

                const details = await this.fetchLinkDetails(linkData.source, linkData.target, linkData.linkType);
                
                if (details && details.success) {
                    const linkDetails = {
                        ...linkData,
                        type: 'link',
                        loading: false,
                        name: `${linkData.linkType} (${linkData.source} → ${linkData.target})`,
                        properties: details.properties || {},
                        class: linkData.linkType
                    };
                    this.selectedNodeDetails = linkDetails;
                } else {
                    const errorLinkData = {
                        ...linkData,
                        type: 'link',
                        loading: false,
                        error: 'Failed to fetch link details',
                        name: `${linkData.linkType} (${linkData.source} → ${linkData.target})`
                    };
                    this.selectedNodeDetails = errorLinkData;
                }
            } catch (error) {
                console.error('Error fetching link details:', error);
                const errorLinkData = {
                    ...linkData,
                    type: 'link',
                    loading: false,
                    error: error.message,
                    name: `${linkData.linkType} (${linkData.source} → ${linkData.target})`
                };
                this.selectedNodeDetails = errorLinkData;
            }
        },

        closeDetailModal() {
            this.showDetailModal = false;
            this.selectedNodeDetails = null;
        },

        async fetchNodeDetails(nodeName) {
            try {
                const response = await fetch('/get_node_details', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ node_name: nodeName })
                });
                
                if (response.ok) {
                    return await response.json();
                } else {
                    console.error('Failed to fetch node details');
                    return null;
                }
                
            } catch (error) {
                console.error('Error fetching node details:', error);
                return null;
            }
        },

        async fetchLinkDetails(sourceNode, targetNode, linkType) {
            try {
                const response = await fetch('/get_link_details', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        source: sourceNode, 
                        target: targetNode, 
                        link_type: linkType 
                    })
                });
                
                if (response.ok) {
                    return await response.json();
                } else {
                    console.error('Failed to fetch link details');
                    return null;
                }
            } catch (error) {
                console.error('Error fetching link details:', error);
                return null;
            }
        },

        formatPropertyValue(value) {
            if (Array.isArray(value)) {
                return value.join(' ');
            }
            if (typeof value === 'object' && value !== null) {
                return JSON.stringify(value);
            }
            return value;
        },

        // Simulation results functions (Advanced)
        async showAllSimulationResults() {
            this.resultsLoading = true;
            this.showResultsModal = true;
            
            try {
                const response = await fetch('/get_simulation_results');
                if (response.ok) {
                    const data = await response.json();
                    this.simulationResults = data;
                } else {
                    console.error('Failed to fetch simulation results');
                    this.simulationResults = null;
                }
            } catch (error) {
                console.error('Error fetching simulation results:', error);
                this.simulationResults = null;
            } finally {
                this.resultsLoading = false;
            }
        },

        closeResultsModal() {
            this.showResultsModal = false;
            this.simulationResults = null;
        },

        getVoltageColor(voltagePercent) {
            if (voltagePercent >= 95) return 'text-green-600';
            if (voltagePercent >= 90) return 'text-yellow-600';
            return 'text-red-600';
        },

        async saveFileContent() {
            if (!this.selectedFileData || !this.fileEditorContent) {
                this.editorMessage = 'No content to save';
                this.editorMessageType = 'error';
                return;
            }

            this.editorSaving = true;
            this.editorMessage = '';

            try {
                const response = await fetch('/save_glm_file', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        filename: this.selectedFileData.name,
                        content: this.fileEditorContent
                    })
                });

                const result = await response.json();

                if (result.success) {
                    this.editorMessage = result.message;
                    this.editorMessageType = 'success';
                    
                    // Update the selectedFileData with new content
                    const encoder = new TextEncoder();
                    const newArrayBuffer = encoder.encode(this.fileEditorContent);
                    
                    this.selectedFileData = {
                        ...this.selectedFileData,
                        arrayBuffer: newArrayBuffer,
                        size: newArrayBuffer.byteLength
                    };
                    
                    // Clear any previous simulation results
                    this.simulationResult = '';
                    this.simulationSuccess = false;
                } else {
                    throw new Error(result.error);
                }
            } catch (error) {
                console.error('Error saving file:', error);
                this.editorMessage = `Error saving file: ${error.message}`;
                this.editorMessageType = 'error';
            } finally {
                this.editorSaving = false;
            }
        }
    }
}
