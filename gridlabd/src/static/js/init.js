// Application initialization and utilities
document.addEventListener('DOMContentLoaded', function() {
    // Create hidden inputs for compatibility with legacy functions
    const hiddenInputs = `
        <input type="hidden" id="nodeSearchNm" value="">
        <input type="hidden" id="gravityVal" value="0.05">
    `;
    document.body.insertAdjacentHTML('beforeend', hiddenInputs);
});

// Window resize handler for responsive visualization
window.addEventListener('resize', function() {
    if (window.visualizationLoaded && typeof loadNetworkVisualization === 'function') {
        clearTimeout(window.resizeTimeout);
        window.resizeTimeout = setTimeout(function() {
            loadNetworkVisualization();
        }, 250);
    }
});
