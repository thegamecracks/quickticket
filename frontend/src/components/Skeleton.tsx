/**
 * Very basic, deliberately generic skeleton placeholders. Pages change often,
 * so these approximate "some text" / "some list rows" instead of mirroring
 * exact layouts (EventCardSkeleton is the one detailed exception).
 */

const TEXT_WIDTHS = ['w-full', 'w-11/12', 'w-3/4'] as const;

/** A stack of text-shaped bars — for detail/form pages. */
export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-3" aria-hidden="true">
      {Array.from({ length: lines }, (_, i) => (
        <div key={i} className={`skeleton h-4 ${TEXT_WIDTHS[i % TEXT_WIDTHS.length]}`} />
      ))}
    </div>
  );
}

/** A stack of list-row placeholders — for list pages. */
export function SkeletonRows({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-2" aria-hidden="true">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center gap-4">
          <div className="skeleton h-16 w-24 shrink-0 rounded-lg" />
          <div className="space-y-2">
            <div className="skeleton h-4 w-48" />
            <div className="skeleton h-3 w-28" />
          </div>
        </div>
      ))}
    </div>
  );
}
