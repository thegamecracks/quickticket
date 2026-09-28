import { useState } from 'react'

type AuthModalProps = {
  open: boolean
  onClose: () => void
}

/** Sign in / register modal. */
export default function AuthModal({ open, onClose }: AuthModalProps) {
  const [mode, setMode] = useState<'signin' | 'register'>('signin')

  if (!open) return null

  return (
    <div className="modal modal-open">
      <div className="modal-box max-w-sm">
        <div className="mb-4 flex gap-2">
          <button
            className={`btn btn-sm flex-1 ${mode === 'signin' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setMode('signin')}
          >
            Sign in
          </button>
          <button
            className={`btn btn-sm flex-1 ${mode === 'register' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setMode('register')}
          >
            Register
          </button>
        </div>

        <form className="flex flex-col gap-3">
          {mode === 'register' && (
            <input type="text" placeholder="Name" className="input input-bordered" />
          )}
          <input type="email" placeholder="Email" className="input input-bordered" />
          <input type="password" placeholder="Password" className="input input-bordered" />
          <button type="button" className="btn btn-primary mt-2">
            {mode === 'signin' ? 'Sign in' : 'Create account'}
          </button>
        </form>
      </div>
      <button className="modal-backdrop" onClick={onClose} aria-label="Close" />
    </div>
  )
}
