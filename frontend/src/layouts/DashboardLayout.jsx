import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import SidebarUser from '../components/SidebarUser';
import Header from '../components/Header';

const DashboardLayout = () => {
  const location = useLocation();
  const isChat = location.pathname.includes('/app/chat');

  return (
    <div className="min-h-screen w-full bg-background flex flex-row relative font-sans text-foreground">
      <SidebarUser />
      
      <main className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        <Header />
        
        {/* Nội dung trang thay đổi ở đây */}
        {isChat ? (
          <Outlet />
        ) : (
          <div className="p-6 lg:p-8 max-w-6xl mx-auto w-full">
            <Outlet />
          </div>
        )}
      </main>
    </div>
  );
};

export default DashboardLayout;
