import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';

const SidebarUser = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useUser();

  const isActive = (path) => {
    return location.pathname === path;
  };

  const getLinkClass = (path) => {
    const baseClass = "flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-colors";
    return isActive(path)
      ? `${baseClass} bg-primary/10 text-primary`
      : `${baseClass} text-muted-foreground hover:bg-secondary hover:text-foreground`;
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col hidden md:flex h-screen sticky top-0">
      <div className="h-16 flex items-center px-6 border-b border-border">
        <Link to="/app" className="flex items-center gap-2 text-primary font-heading font-bold text-xl">
          <iconify-icon icon="lucide:activity"></iconify-icon>
          <span>MediAI</span>
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto py-6 px-4 flex flex-col gap-1">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">Main Menu</p>
        <Link to="/app" className={getLinkClass("/app")}>
          <iconify-icon icon="lucide:layout-dashboard" class="text-lg"></iconify-icon>
          Dashboard
        </Link>
        <Link to="/app/chat" className={getLinkClass("/app/chat")}>
          <iconify-icon icon="lucide:message-circle" class="text-lg"></iconify-icon>
          AI Consult
        </Link>
        <Link to="/app/medicines" className={getLinkClass("/app/medicines")}>
          <iconify-icon icon="lucide:pill" class="text-lg"></iconify-icon>
          Medicines
        </Link>
        <Link to="/app/diseases" className={getLinkClass("/app/diseases")}>
          <iconify-icon icon="lucide:microscope" class="text-lg"></iconify-icon>
          Diseases
        </Link>
        <Link to="/app/interactions" className={getLinkClass("/app/interactions")}>
          <iconify-icon icon="lucide:shield-alert" class="text-lg"></iconify-icon>
          Interactions
        </Link>

        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-6 mb-2 px-2">Personal</p>
        <Link to="/app/saved" className={getLinkClass("/app/saved")}>
          <iconify-icon icon="lucide:bookmark" class="text-lg"></iconify-icon>
          Saved Items
        </Link>
      </div>

      <div className="p-4 border-t border-border">
        <Link to="/app/settings" className={getLinkClass("/app/settings")}>
          <iconify-icon icon="lucide:settings" class="text-lg"></iconify-icon>
          Settings
        </Link>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 text-destructive hover:bg-destructive/10 rounded-lg font-medium transition-colors mt-1 w-full text-left"
        >
          <iconify-icon icon="lucide:log-out" class="text-lg"></iconify-icon>
          Log Out
        </button>
      </div>
    </aside>
  );
};

export default SidebarUser;
