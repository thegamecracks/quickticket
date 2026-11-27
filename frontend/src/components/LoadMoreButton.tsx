interface LoadMoreButtonProps {
  /** false once the cursor is exhausted (backend returned `next: null`). */
  hasMore: boolean;
  loading: boolean;
  onClick: () => void;
  /** Text shown instead of the button when there is nothing more to load. */
  endLabel?: string;
}

// TODO: replace this button with infinite scroll (IntersectionObserver) once
// the basic flow is verified; agreed to ship "Load more" first.
export function LoadMoreButton(props: LoadMoreButtonProps) {
  const { hasMore, loading, onClick, endLabel } = props;

  if (!hasMore) {
    if (!endLabel) return null;
    return <p className="text-base-content/70">{endLabel}</p>;
  }

  return (
    <div className="flex justify-center">
      <button type="button" className="btn btn-outline" disabled={loading} onClick={onClick}>
        {loading ? <span className="loading loading-spinner" aria-label="Loading" /> : 'Load more'}
      </button>
    </div>
  );
}
