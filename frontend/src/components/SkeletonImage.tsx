import { useState } from 'react';

type SkeletonImageProps = {
  /**
   * Ordered candidate sources. On load-error the next source is tried; the
   * last entry is the final fallback (typically a placeholder URL). Add a
   * `key` when the same component instance can switch entities.
   */
  sources: string[];
  alt: string;
  className?: string;
};

export default function SkeletonImage({ sources, alt, className }: SkeletonImageProps) {
  const [index, setIndex] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const src = sources[Math.min(index, sources.length - 1)];

  return (
    <div className={`relative ${className}`}>
      {!loaded && <div className="skeleton absolute inset-0 h-full w-full" />}
      <img
        src={src}
        alt={alt}
        onLoad={() => setLoaded(true)}
        onError={() => setIndex((i) => Math.min(i + 1, sources.length - 1))}
        className={`${className} ${loaded ? 'opacity-100' : 'opacity-0'} transition-opacity`}
      />
    </div>
  );
}
