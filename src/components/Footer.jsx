import { Terminal } from 'lucide-react'

const Footer = () => (
  <footer className="py-12 border-t border-border-app/40 bg-app-bg text-neutral-500 text-xs relative select-none">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
      <div className="flex items-center gap-2">
        <Terminal size={14} className="text-[#3B82F6]" />
        <span className="font-semibold text-primary">RouteMind AI Engine</span>
        <span className="text-neutral-700">|</span>
        <span>Edge Nodes Enabled</span>
      </div>
      <p className="text-neutral-600 font-mono">
        &copy; {new Date().getFullYear()} RouteMind Proxy Corp. Production Grade.
      </p>
    </div>
  </footer>
)

export default Footer
