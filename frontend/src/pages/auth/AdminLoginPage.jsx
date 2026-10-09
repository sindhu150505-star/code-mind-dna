import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

function getErrorMessage(error) {
  const detail = error.response?.data?.detail;
  if (Array.isArray(detail)) return 'Enter a valid phone number.';
  return detail || 'Unable to authenticate as an administrator. Please try again.';
}

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const { adminLogin } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      await adminLogin({ phone_number: phoneNumber });
      setSuccess('Admin authentication successful.');
      window.setTimeout(() => navigate('/admin/dashboard', { replace: true }), 500);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)]">
      <section className="flex min-h-screen items-center justify-center px-4 py-10 sm:px-6">
        <div className="auth-card w-full max-w-md">
          <p className="kicker">CodeMind DNA</p>
          <h1 className="mt-3 text-3xl font-semibold">Admin Access</h1>
          <p className="mt-2 text-sm text-[var(--text-secondary)]">Authorized administrators only.</p>

          <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
            <label className="block text-sm font-medium text-[var(--text-secondary)]">
              <span className="mb-1 block">Phone Number</span>
              <input
                className="w-full rounded-2xl border border-[var(--border-subtle)] bg-[var(--surface-elevated)] px-3 py-3 text-[var(--text-primary)] outline-none transition focus:border-[var(--brand-primary)]"
                type="tel"
                inputMode="tel"
                autoComplete="tel"
                placeholder="Enter authorized phone number"
                value={phoneNumber}
                onChange={(event) => setPhoneNumber(event.target.value)}
                required
              />
            </label>
            {error ? <p className="rounded-2xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p> : null}
            {success ? <p className="rounded-2xl border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">{success}</p> : null}
            <button className="btn-primary w-full" type="submit" disabled={loading}>
              {loading ? 'Authenticating...' : 'Login as Admin'}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
