import { useNavigate } from "react-router";

export default function NavigateBackBtn() {
  const navigate = useNavigate()
  return (
    <button className="btn btn-primary" onClick={() => navigate(-1)}>
      Back
    </button>
  )
}
