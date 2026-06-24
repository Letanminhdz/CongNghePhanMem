import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';

const Header = () => {
  const navigate = useNavigate();
  const { user } = useUser();

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : '?';

  return (
    <header className="h-16 flex-shrink-0 bg-card border-b border-border flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center gap-4 flex-1">
        <button className="md:hidden text-muted-foreground hover:text-foreground">
          <iconify-icon icon="lucide:menu" class="text-2xl"></iconify-icon>
        </button>
      </div>
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/app/settings', { state: { tab: 'account' } })}
          className="flex items-center gap-3 pl-4 border-l border-border text-left hover:opacity-80 transition-opacity"
        >
          <div className="w-8 h-8 rounded-full bg-primary/10 border border-border flex items-center justify-center text-primary text-sm font-bold">
            {initials}
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-medium leading-none text-foreground">{user?.full_name || 'Loading...'}</p>
            <p className="text-xs text-muted-foreground mt-1">{user?.email || ''}</p>
          </div>
        </button>
      </div>
    </header>
  );
};

export default Header;
