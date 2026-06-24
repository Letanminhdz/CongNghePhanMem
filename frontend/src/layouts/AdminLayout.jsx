import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import SidebarAdmin from '../components/SidebarAdmin';
import { useUser } from '../context/UserContext';

const AdminLayout = () => {
  const { user } = useUser();

  const displayName = user?.full_name || user?.email?.split('@')[0] || 'Admin';
  const avatarLetter = displayName.charAt(0).toUpperCase();

  return (
    <div className="min-h-screen w-full bg-background flex flex-row relative font-sans text-foreground">
      <SidebarAdmin />
      <main className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        {/* Admin Header */}
        <header className="h-16 flex-shrink-0 bg-card border-b border-border flex items-center justify-between px-6 sticky top-0 z-10">
          <div className="flex items-center gap-4 flex-1">
            <div className="relative w-full max-w-md hidden sm:block">
              <iconify-icon icon="lucide:search" class="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"></iconify-icon>
              <input type="text" placeholder="Search admin panel..." className="w-full pl-10 pr-4 py-2 bg-secondary border-none rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all" />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div
              className="flex items-center gap-3 text-left"
            >
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-sm font-bold">
                {avatarLetter}
              </div>
              <div className="hidden sm:block">
                <p className="text-sm font-medium leading-none text-foreground">{displayName}</p>
                <p className="text-xs text-muted-foreground mt-1">Super Admin</p>
              </div>
            </div>
          </div>
        </header>
        <div className="p-6 lg:p-8 w-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AdminLayout;
