
interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onChangePage: (page: number) => void;
}

// Clamp a page number into the valid range [1, max(totalPages, 1)]
// not totally necessary as there are already visual catches for this.
// The original Math.min only was fine to use.
export const safePage = (page: number, totalPages: number): number =>
  Math.max(1, Math.min(page, Math.max(totalPages, 1)))

export function Pagination(props: PaginationProps) {
  const { currentPage, totalPages, onChangePage } = props;

  return (
    <>
      {/* Pagination */}
      {
        totalPages > 1 && (
          <div className="mt-8 flex items-center justify-center gap-4">

            <button
              type="button"
              className="btn btn-outline"
              disabled={currentPage === 1}
              onClick={() => onChangePage(currentPage - 1)}
            >
              Previous
            </button>

            <span className="text-sm">
              Page {currentPage} of {totalPages}
            </span>

            <button
              type="button"
              className="btn btn-primary"
              disabled={currentPage === totalPages}
              onClick={() => onChangePage(currentPage + 1)}
            >
              Next
            </button>

          </div>
        )
      }
    </>
  );
}
