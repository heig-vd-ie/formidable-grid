import { useRef, useCallback } from 'react'

export { Resizer }

// Resizer Component
function Resizer({ onResize }) {
  const isResizing = useRef(false)
  const startX = useRef(0)
  const startWidth = useRef(0)

  const handleMouseDown = useCallback((e) => {
    isResizing.current = true
    startX.current = e.clientX
    startWidth.current = parseInt(document.defaultView.getComputedStyle(e.target.previousElementSibling).width, 10)
    
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    
    // Prevent text selection during resize
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'col-resize'
  }, [])

  const handleMouseMove = useCallback((e) => {
    if (!isResizing.current) return
    
    const dx = e.clientX - startX.current
    const newWidth = startWidth.current + dx
    const containerWidth = document.querySelector('.main-layout').offsetWidth
    
    // Set minimum and maximum widths
    const minWidth = 300
    const maxWidth = containerWidth - 350 // Leave at least 350px for visualization panel
    
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      onResize(newWidth)
    }
  }, [onResize])

  const handleMouseUp = useCallback(() => {
    isResizing.current = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
    
    // Restore text selection
    document.body.style.userSelect = ''
    document.body.style.cursor = ''
  }, [handleMouseMove])

  return (
    <div 
      className="resizer" 
      onMouseDown={handleMouseDown}
    />
  )
}
