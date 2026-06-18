import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';

const Navbar = () => {
  const navigate = useNavigate();
  const { user, logout } = useUser();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-50 w-full bg-card/80 backdrop-blur-md border-b border-border">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-primary font-heading font-bold text-xl">
          <iconify-icon icon="lucide:activity" class="text-2xl"></iconify-icon>
          <span>MediAI</span>
        </Link>
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
          <Link to="/" className="text-primary transition-colors">Home</Link>
          <Link to="/medicines" className="hover:text-foreground transition-colors">Medicines</Link>
        </nav>
        <div className="flex items-center gap-4">
          {user ? (
            <>
              {/* Nút vào Dashboard/Admin tùy theo vai trò */}
              <button
                onClick={() => navigate(user.is_superuser ? '/admin' : '/app')}
                className="text-sm font-medium text-foreground hover:text-primary transition-colors flex items-center gap-1.5"
              >
                <iconify-icon icon={user.is_superuser ? "lucide:shield" : "lucide:layout-dashboard"} class="text-base"></iconify-icon>
                {user.is_superuser ? 'Admin Panel' : 'Dashboard'}
              </button>
              <button
                onClick={handleLogout}
                className="bg-destructive/10 text-destructive px-5 py-2.5 rounded-full text-sm font-medium hover:bg-destructive/20 transition-colors"
              >
                Log Out
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => navigate('/login')}
                className="text-sm font-medium text-foreground hover:text-primary transition-colors"
              >
                Log In
              </button>
              <button
                onClick={() => navigate('/register')}
                className="bg-primary text-primary-foreground px-5 py-2.5 rounded-full text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
              >
                Sign Up
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
