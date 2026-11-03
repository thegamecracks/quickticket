import type { ReactNode } from "react";
import NavigateBackBtn from "./NavigateBack";

/** Every page shares one content width so nothing jumps between routes. */
const CONTENT_WIDTH = "max-w-5xl";

export type PageLayoutProps = {
  /** Page heading. Pass `undefined` while data loads and set `fallbackTitle`. */
  title?: ReactNode;
  /** Shown instead of `title` while it is unavailable (e.g. during fetch). */
  fallbackTitle?: string;
  /** Show the back button. Pass `{ to }` for a fallback route on deep links. */
  back?: boolean | { to?: string };
  /** Optional right-aligned header controls (edit/save/etc.). */
  actions?: ReactNode;
  /** Full-bleed content rendered above the padded container (e.g. a hero). */
  hero?: ReactNode;
  /** Extra classes for the outer section. */
  className?: string;
  children: ReactNode;
};

export default function PageLayout({
  title,
  fallbackTitle,
  back = false,
  actions,
  hero,
  className = "",
  children,
}: PageLayoutProps) {
  const heading = title ?? fallbackTitle;

  return (
    <>
      {hero}
      <section
        className={`mx-auto w-full ${CONTENT_WIDTH} grow px-4 py-12 ${className}`}
      >
        {(back || heading || actions) && (
          <div className="mb-4 flex min-w-0 items-center gap-1">
            {back && (
              <NavigateBackBtn
                to={typeof back === "object" ? back.to : undefined}
              />
            )}
            {heading && (
              <h1 className="truncate text-3xl font-bold">{heading}</h1>
            )}
            {actions && (
              <div className="ml-auto flex shrink-0 items-center gap-2">
                {actions}
              </div>
            )}
          </div>
        )}
        {children}
      </section>
    </>
  );
}
