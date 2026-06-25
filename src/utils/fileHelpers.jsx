import { Image, FileText, Code, File } from 'lucide-react'

export const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export const getFileIcon = (fileName, size = 13) => {
  if (!fileName) return <File size={size} className="text-neutral-400 shrink-0" />
  const ext = fileName.split('.').pop().toLowerCase()
  if (['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext)) {
    return <Image size={size} className="text-blue-400 shrink-0" />
  }
  if (['pdf'].includes(ext)) {
    return <FileText size={size} className="text-red-400 shrink-0" />
  }
  if (['doc', 'docx'].includes(ext)) {
    return <FileText size={size} className="text-blue-500 shrink-0" />
  }
  if (['txt', 'md'].includes(ext)) {
    return <FileText size={size} className="text-neutral-400 shrink-0" />
  }
  if (['js', 'jsx', 'ts', 'tsx', 'py', 'cpp', 'java', 'json', 'html', 'css'].includes(ext)) {
    return <Code size={size} className="text-green-400 shrink-0" />
  }
  return <File size={size} className="text-neutral-400 shrink-0" />
}
