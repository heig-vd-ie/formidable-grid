// API utility functions for connecting to the backend

const API_BASE_URL = '/api'

// Helper function to handle API responses
const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.error || error.detail || 'Network error')
  }
  return response.json()
}

// Upload a GLM file
export const uploadGLMFile = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/upload_glm_file`, {
    method: 'POST',
    body: formData,
  })

  return handleResponse(response)
}

// Read GLM file content for editing
export const readGLMFile = async (filename) => {
  const response = await fetch(`${API_BASE_URL}/read_glm_file`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ filename }),
  })

  return handleResponse(response)
}

// Save GLM file content after editing
export const saveGLMFile = async (filename, content) => {
  const response = await fetch(`${API_BASE_URL}/save_glm_file`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ filename, content }),
  })

  return handleResponse(response)
}

// Run power flow simulation
export const runPowerFlow = async (file, randomseed = 42) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('randomseed', randomseed)

  const response = await fetch(`${API_BASE_URL}/run-powerflow`, {
    method: 'POST',
    body: formData,
  })

  return handleResponse(response)
}

// List cache files
export const listCacheFiles = async () => {
  const response = await fetch(`${API_BASE_URL}/list_cache_files`, {
    method: 'GET',
  })

  return handleResponse(response)
}

// Load cache data for visualization
export const loadCacheData = async (filename) => {
  const response = await fetch(`${API_BASE_URL}/load_cache_data`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ filename }),
  })

  return handleResponse(response)
}

// Get visualization data
export const getVisualizationData = async () => {
  const response = await fetch(`${API_BASE_URL}/get_data`, {
    method: 'GET',
  })

  return handleResponse(response)
}

// Get simulation results
export const getSimulationResults = async () => {
  const response = await fetch(`${API_BASE_URL}/get_simulation_results`, {
    method: 'GET',
  })

  return handleResponse(response)
}

// Get node details
export const getNodeDetails = async (nodeId) => {
  const response = await fetch(`${API_BASE_URL}/get_node_details`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ node_id: nodeId }),
  })

  return handleResponse(response)
}

// Get link details
export const getLinkDetails = async (linkId) => {
  const response = await fetch(`${API_BASE_URL}/get_link_details`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ link_id: linkId }),
  })

  return handleResponse(response)
}

// Get current time (health check)
export const getCurrentTime = async () => {
  const response = await fetch(`${API_BASE_URL}/time`, {
    method: 'GET',
  })

  return handleResponse(response)
}
