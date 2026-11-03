import { ArrowLeftIcon } from "@heroicons/react/24/solid";
import { useNavigate } from "react-router";

type NavigateBackBtnProps = {
  label?: string;
  /** Fallback route when there is no in-app history (direct link / refresh). */
  to?: string;
};

export default function NavigateBackBtn({ label = "Back", to }: NavigateBackBtnProps) {
  const navigate = useNavigate()

  const handleClick = () => {
    // React Router stores the history index in history.state; idx 0 == nothing to go back to.
    const idx = window.history.state?.idx
    const hasInAppHistory = typeof idx === "number" && idx > 0

    if (!hasInAppHistory && to) {
      navigate(to, { replace: true })
      return
    }
    navigate(-1)
  }

  return (
    <button
      type="button"
      className="btn btn-ghost btn-sm -ml-2 shrink-0 gap-1 text-base-content/70 hover:text-base-content"
      onClick={handleClick}
    >
      <ArrowLeftIcon className="size-3" />
      {label}
    </button >
  )
}
