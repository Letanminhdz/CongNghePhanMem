import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const SidebarAdmin = () => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;
  const getLinkClass = (path) => {
    const base = "flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-colors";
    return isActive(path)
      ? `${base} bg-primary/10 text-primary`
      : `${base} text-muted-foreground hover:bg-secondary hover:text-foreground`;
  };
  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col hidden md:flex h-screen sticky top-0">
      <div className="h-16 flex items-center px-6 border-b border-border">
        <Link to="/admin" className="flex items-center gap-2 text-primary font-heading font-bold text-xl">
          <iconify-icon icon="lucide:activity"></iconify-icon>
          <span>MediAI Admin</span>
        </Link>
      </div>
      <div className="flex-1 overflow-y-auto py-6 px-4 flex flex-col gap-1">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">Overview</p>
        <Link to="/admin" className={getLinkClass("/admin")}>
          <iconify-icon icon="lucide:layout-dashboard" class="text-lg"></iconify-icon>
          Dashboard
        </Link>
        <Link to="/admin/users" className={getLinkClass("/admin/users")}>
          <iconify-icon icon="lucide:users" class="text-lg"></iconify-icon>
          User Management
        </Link>
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-6 mb-2 px-2">Database</p>
        <Link to="/admin/medicines" className={getLinkClass("/admin/medicines")}>
          <iconify-icon icon="lucide:pill" class="text-lg"></iconify-icon>
          Medicines
        </Link>
        <Link to="/admin/diseases" className={getLinkClass("/admin/diseases")}>
          <iconify-icon icon="lucide:microscope" class="text-lg"></iconify-icon>
          Diseases
        </Link>
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-6 mb-2 px-2">System</p>
        <Link to="/admin/ai" className={getLinkClass("/admin/ai")}>
          <iconify-icon icon="lucide:bot" class="text-lg"></iconify-icon>
          AI Logs
        </Link>
        <Link to="/admin/reports" className={getLinkClass("/admin/reports")}>
          <iconify-icon icon="lucide:bar-chart-2" class="text-lg"></iconify-icon>
          Reports
        </Link>
      </div>
      <div className="p-4 border-t border-border">
        <Link to="/admin/settings" className={getLinkClass("/admin/settings")}>
          <iconify-icon icon="lucide:settings" class="text-lg"></iconify-icon>
          Settings
        </Link>
        <Link to="/login" className="flex items-center gap-3 px-3 py-2.5 text-destructive hover:bg-destructive/10 rounded-lg font-medium transition-colors mt-1">
          <iconify-icon icon="lucide:log-out" class="text-lg"></iconify-icon>
          Log Out
        </Link>
      </div>
    </aside>
  );
};

export default SidebarAdmin;
