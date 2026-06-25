import { useState, useRef, useEffect } from 'react'
import { Paperclip, ArrowUp, Sparkles, Loader2 } from 'lucide-react'

const ChatInput = ({ 
  onSubmit, 
  isLoading = false, 
  loadingStep = "Analyzing Intent...", 
  placeholder = "Ask RouteMind a query... (e.g. Write a fast Rust HTTP server)",
  helperText = "Code, research, writing, reasoning — RouteMind will choose the best model."
}) => {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  // Auto-expand height logic
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return

    // Reset height to compute scrollHeight accurately
    textarea.style.height = 'auto'
    
    // Set height based on scrollHeight, constrained between 56px and 200px
    const newHeight = Math.min(Math.max(textarea.scrollHeight, 56), 200)
    textarea.style.height = `${newHeight}px`
  }, [value])

  const handleSubmit = (e) => {
    if (e) e.preventDefault()
    if (!value.trim() || isLoading) return
    
    if (onSubmit) {
      onSubmit(value.trim())
    }
    setValue('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="w-full max-w-[900px] mx-auto px-4 py-4 flex flex-col gap-2">
      {/* Helper / Reassurance Text */}
      {!isLoading && helperText && (
        <div className="text-[11px] text-neutral-500 font-mono tracking-wide px-1.5 select-none transition-opacity duration-200">
          {helperText}
        </div>
      )}

      {/* Loading Steps Indicator */}
      {isLoading && (
        <div className="text-[11px] text-blue-400 font-mono tracking-wide px-1.5 flex items-center gap-1.5 select-none transition-opacity duration-200">
          <Loader2 size={12} className="animate-spin text-blue-500" />
          <span className="animate-pulse">{loadingStep}</span>
        </div>
      )}

      {/* Input Surface */}
      <form 
        onSubmit={handleSubmit}
        className={`
          relative flex flex-col bg-card-bg border border-border-app rounded-2xl 
          transition-all duration-200 ease-out shadow-2xl p-2
          ${isLoading ? 'opacity-60 pointer-events-none' : 'focus-within:border-blue-500/40 focus-within:ring-1 focus-within:ring-blue-500/20'}
        `}
      >
        {/* Text Area */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          placeholder={isLoading ? "RouteMind is choosing the best model..." : placeholder}
          rows={1}
          aria-label="Ask RouteMind a query"
          className="w-full bg-transparent border-0 ring-0 focus:ring-0 focus:outline-none px-3.5 pt-2.5 pb-1 text-sm text-primary placeholder-[#71717A] resize-none overflow-y-auto scrollbar-thin scrollbar-thumb-neutral-800 scrollbar-track-transparent leading-relaxed"
          style={{ minHeight: '56px', maxHeight: '200px' }}
        />

        {/* Bottom Toolbar */}
        <div className="flex items-center justify-between border-t border-border-app/40 pt-2 mt-2 px-1">
          {/* Left: Attach Button */}
          <div className="flex items-center gap-1">
            <button
              type="button"
              disabled={isLoading}
              className="p-2 rounded-lg text-neutral-500 hover:text-primary hover:bg-card-bg transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 cursor-pointer"
              title="Attach File (PDF, Image, Document)"
              aria-label="Attach file"
            >
              <Paperclip size={16} />
            </button>
          </div>

          {/* Center: Subtle Routing Indicator */}
          <div className="flex items-center gap-1.5 select-none text-[10px] text-neutral-500 font-mono font-medium px-3 py-1 bg-sidebar-bg/40 border border-border-app/50 rounded-full">
            <Sparkles size={10} className="text-blue-400 animate-pulse" />
            <span>RouteMind AI</span>
          </div>

          {/* Right: Send Button */}
          <button
            type="submit"
            disabled={!value.trim() || isLoading}
            className={`
              p-2 rounded-xl flex items-center justify-center transition-all duration-200 outline-none
              ${value.trim() && !isLoading
                ? 'bg-blue-600 text-white hover:bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:scale-[1.03] active:scale-[0.98] cursor-pointer'
                : 'bg-blue-50 text-blue-400 border border-blue-100 dark:bg-neutral-900 dark:text-neutral-600 dark:border-neutral-800 cursor-not-allowed'
              }
            `}
            title="Send Message"
            aria-label="Send message"
          >
            <ArrowUp size={16} />
          </button>
        </div>
      </form>
    </div>
  )
}

export default ChatInput
