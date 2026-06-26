/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const ThemeContext = createContext({
  theme: 'system',
  setTheme: () => null,
  resolvedTheme: 'dark',
})

/**
 * Apply dark/light class to <html> with a smooth transition.
 * Uses the View Transition API when available (Chrome 111+, Edge 111+)
 * for a native hardware-accelerated cross-fade.
 * Falls back to a CSS class-based transition on older browsers.
 */
function applyTheme(isDark) {
  const root = document.documentElement

  const doApply = () => {
    if (isDark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }

  // View Transition API path — gives a native GPU cross-fade
  if (document.startViewTransition) {
    root.setAttribute('data-theme-switching', '')
    const transition = document.startViewTransition(() => {
      doApply()
    })
    transition.finished.finally(() => {
      root.removeAttribute('data-theme-switching')
    })
    return
  }

  // CSS fallback for browsers without View Transition API
  root.classList.add('theme-transition')
  doApply()
  const timer = setTimeout(() => {
    root.classList.remove('theme-transition')
  }, 350)
  return () => clearTimeout(timer)
}

/** Resolve 'system' → actual 'dark' | 'light' without triggering an effect. */
function resolveTheme(theme) {
  if (theme === 'dark' || theme === 'light') return theme
  if (typeof window !== 'undefined') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return 'dark'
}

export const ThemeProvider = ({ children }) => {
  const [theme, setThemeState] = useState(() => {
    return localStorage.getItem('theme') || 'system'
  })

  // Derived synchronously — no setState inside an effect
  const resolvedTheme = useMemo(() => resolveTheme(theme), [theme])

  const setTheme = (newTheme) => {
    if (newTheme !== 'light' && newTheme !== 'dark' && newTheme !== 'system') return
    setThemeState(newTheme)
    localStorage.setItem('theme', newTheme)
  }

  useEffect(() => {
    const isDark = resolvedTheme === 'dark'
    const cleanup = applyTheme(isDark)

    if (theme === 'system') {
      const mq = window.matchMedia('(prefers-color-scheme: dark)')
      const listener = () => {
        applyTheme(mq.matches)
        // Force a re-render so resolvedTheme updates for system preference changes
        setThemeState('system')
      }
      mq.addEventListener ? mq.addEventListener('change', listener) : mq.addListener(listener)
      return () => {
        cleanup?.()
        mq.removeEventListener
          ? mq.removeEventListener('change', listener)
          : mq.removeListener(listener)
      }
    }

    return cleanup
  }, [theme, resolvedTheme])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
