
interface PaginationProps {
  currentPage: number;
  totalPages: number;
  safePage: number;
  onChangePage: (page: number) => void;
}

export const safePage = (currentPage: number, totalPages: number, safePage: number): number => {
  return Math.min(currentPage, Math.max(totalPages, 1));

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
                disabled={safePage === 1}
                onClick={() => onChangePage(safePage(currentPage, totalPages) - 1)}
              >
                Previous
              </button>

              <span className="text-sm">
                Page {safePage(currentPage, totalPages)} of {totalPages}
              </span>

              <button
                type="button"
                className="btn btn-primary"
                disabled={safePage(currentPage, totalPages) === totalPages}
                onClick={() => onChangePage(safePage(currentPage, totalPages) + 1)}
              >
                Next
              </button>

            </div>
          )
        }
      </>
    );
  }
