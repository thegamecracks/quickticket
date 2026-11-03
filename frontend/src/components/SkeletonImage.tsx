import { useState } from 'react'
import type { StorageObjectRef } from '../features/events/types'

type SkeletonImageProps = {
  src: StorageObjectRef | string
  alt: string
  className?: string
}

export default function SkeletonImage({ src, alt, className }: SkeletonImageProps) {
  const [status, setStatus] = useState<'loading' | 'loaded' | 'error'>('loading');

  return (
    <div className={`relative ${className}`}>
      {status === 'loading' && (
        <div className="skeleton absolute inset-0 h-full w-full" />
      )}
      <img
        src={src.toString()}
        alt={alt}
        onLoad={() => setStatus('loaded')}
        onError={() => setStatus('error')}
        className={`${className} ${status === 'loaded' ? 'opacity-100' :
          'opacity-0'} transition-opacity`}
      />
    </div>
  )
}
