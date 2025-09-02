// GridLAB-D Network Plotter Application
function gridLabApp() {
    return {
        // Application State
        selectedFile: null,
        randomSeed: 42,
        selectedCache: '',
        cacheFiles: [],
        loading: false,
        visualizationLoading: false,
        visualizationLoaded: false,
        simulationResult: '',
        simulationSuccess: false,
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

        // Initialize application
        init() {
            this.loadCacheFiles();
        },

        // File handling
        handleFileUpload(event) {
            const file = event.target.files[0];
            this.selectedFile = file;
            if (file) {
                this.simulationResult = '';
            }
        },

        // Cache file management
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

        // Simulation
        async runSimulation() {
            if (!this.selectedFile) return;
            
            this.loading = true;
            this.simulationResult = '';
            
            try {
                const formData = new FormData();
                formData.append('file', this.selectedFile);
                formData.append('randomseed', this.randomSeed || '42');

                const response = await fetch('/run_simulation', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.simulationResult = `Simulation completed successfully! Output: ${result.output_file}`;
                    this.simulationSuccess = true;
                    await this.loadCacheFiles();
                } else {
                    this.simulationResult = `Simulation failed: ${result.error}`;
                    this.simulationSuccess = false;
                }
            } catch (error) {
                this.simulationResult = `Error: ${error.message}`;
                this.simulationSuccess = false;
            } finally {
                this.loading = false;
            }
        },

        // Visualization
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

        // Advanced options
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

        searchNode() {
            if (typeof window.nodeSearcher === 'function') {
                document.getElementById('nodeSearchNm').value = this.nodeSearchTerm;
                window.nodeSearcher();
            } else {
                alert('No visualization loaded');
            }
        },

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
            Object.keys(this.legendFilters.links).forEach(key => {
                this.legendFilters.links[key] = true;
            });
            Object.keys(this.legendFilters.nodes).forEach(key => {
                this.legendFilters.nodes[key] = true;
            });
            this.applyLegendFilters();
        }
    }
}
