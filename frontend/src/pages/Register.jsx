import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UsersService, AuthService } from '../client';

const Register = () => {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }
    if (email.length < 8) {
      setError('Email must be at least 8 characters long');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await UsersService.signupApiV1UsersSignupPost({
        requestBody: {
          email: email,
          password: password,
          full_name: fullName
        }
      });
      // Optionally login after register
      const loginResp = await AuthService.loginAccessTokenApiV1AuthLoginAccessTokenPost({
        formData: {
          username: email,
          password: password,
        }
      });
      localStorage.setItem('access_token', loginResp.access_token);
      navigate('/app');
    } catch (err) {
      setError('Registration failed. Email might be taken.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="flex items-center justify-center mb-8">
        <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary mr-3">
          <iconify-icon icon="lucide:activity" class="text-2xl"></iconify-icon>
        </div>
        <h1 className="text-2xl font-heading font-bold text-foreground tracking-tight">MediChat AI</h1>
      </div>

      <div className="text-center mb-8">
        <h2 className="text-xl font-heading font-semibold text-foreground">Create an account</h2>
        <p className="text-muted-foreground mt-2 text-sm">Join our platform to manage your health data securely.</p>
        {error && <p className="text-destructive mt-2 text-sm">{error}</p>}
      </div>

      <form className="space-y-4" onSubmit={handleRegister}>
        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5 ml-4">Full Name</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-muted-foreground">
              <iconify-icon icon="lucide:user"></iconify-icon>
            </div>
            <input type="text" required value={fullName} onChange={e => setFullName(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-background border border-input rounded-full text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-shadow"
              placeholder="John Doe" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5 ml-4">Email Address</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-muted-foreground">
              <iconify-icon icon="lucide:mail"></iconify-icon>
            </div>
            <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-background border border-input rounded-full text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-shadow"
              placeholder="name@example.com" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5 ml-4">Password</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-muted-foreground">
              <iconify-icon icon="lucide:lock"></iconify-icon>
            </div>
            <input type="password" required value={password} onChange={e => setPassword(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-background border border-input rounded-full text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-shadow"
              placeholder="••••••••" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5 ml-4">Confirm Password</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-muted-foreground">
              <iconify-icon icon="lucide:lock-keyhole"></iconify-icon>
            </div>
            <input type="password" required value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-background border border-input rounded-full text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-shadow"
              placeholder="••••••••" />
          </div>
        </div>

        <div className="flex items-start pt-2 ml-2">
          <div className="flex items-center h-5">
            <input id="terms" type="checkbox" required
              className="w-4 h-4 border border-input rounded bg-background focus:ring-3 focus:ring-primary/30 text-primary" />
          </div>
          <label htmlFor="terms" className="ml-3 text-sm text-muted-foreground">
            I agree to the <a href="#terms" className="text-primary hover:underline font-medium">Terms of Service</a> and <a
              href="#privacy" className="text-primary hover:underline font-medium">Privacy Policy</a>.
          </label>
        </div>

        <div className="pt-4">
          <button type="submit" disabled={loading}
            className="w-full py-3 px-4 bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-full shadow-sm transition-colors flex items-center justify-center disabled:opacity-50">
            {loading ? 'Creating...' : 'Create Account'}
            <iconify-icon icon="lucide:arrow-right" class="ml-2"></iconify-icon>
          </button>
        </div>
      </form>

      <div className="mt-8 text-center text-sm text-muted-foreground">
        Already have an account? <Link to="/login" className="text-primary hover:underline font-medium">Log in here</Link>
      </div>
    </>
  );
};

export default Register;
