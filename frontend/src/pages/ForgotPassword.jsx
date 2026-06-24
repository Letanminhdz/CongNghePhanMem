import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthService } from '../client';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await AuthService.forgotPasswordApiV1AuthForgotPasswordPost({
        requestBody: { email },
      });
      setSubmitted(true);
    } catch (err) {
      setError(err.message || 'Failed to send reset link. Please check if your email is correct.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="flex items-center justify-center mb-6">
        <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
          <iconify-icon icon="lucide:key" class="text-2xl"></iconify-icon>
        </div>
      </div>

      {!submitted ? (
        <>
          <div className="text-center mb-8">
            <h2 className="text-2xl font-heading font-bold text-foreground">Reset Password</h2>
            <p className="text-muted-foreground mt-2 text-sm">Enter the email address associated with your account and we'll send you a reset link.</p>
            {error && <p className="text-destructive mt-3 text-sm bg-destructive/10 px-4 py-2 rounded-lg">{error}</p>}
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5 ml-4">Email Address</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-muted-foreground">
                  <iconify-icon icon="lucide:mail"></iconify-icon>
                </div>
                <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 bg-background border border-input rounded-full text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-shadow"
                  placeholder="name@example.com" />
              </div>
            </div>

            <button type="submit" disabled={loading}
              className="w-full py-3 px-4 bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-full shadow-sm transition-colors disabled:opacity-50">
              {loading ? 'Sending...' : 'Send Reset Link'}
            </button>
          </form>
        </>
      ) : (
        <div className="text-center">
          <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4">
            <iconify-icon icon="lucide:check" class="text-2xl"></iconify-icon>
          </div>
          <h2 className="text-xl font-heading font-bold text-foreground mb-2">Email Sent!</h2>
          <p className="text-muted-foreground text-sm">Check your inbox for a password reset link.</p>
        </div>
      )}

      <div className="mt-8 text-center">
        <Link to="/login"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-primary transition-colors font-medium">
          <iconify-icon icon="lucide:arrow-left" class="mr-2 text-lg"></iconify-icon>
          Back to login
        </Link>
      </div>
    </>
  );
};

export default ForgotPassword;
