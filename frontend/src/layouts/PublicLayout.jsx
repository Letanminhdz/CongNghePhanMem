import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const PublicLayout = () => {
  const location = useLocation();
  const isChat = location.pathname.includes('/chat');
  const isHome = location.pathname === '/';

  return (
    <div className="min-h-screen w-full bg-background flex flex-col font-sans text-foreground">
      <Navbar />
      <main className="flex-1 flex flex-col w-full relative">
        {isChat || isHome ? (
          <Outlet />
        ) : (
          <div className="p-6 lg:p-8 max-w-6xl mx-auto w-full">
            <Outlet />
          </div>
        )}
      </main>
      {!isChat && !isHome && <Footer />}
    </div>
  );
};

export default PublicLayout;
