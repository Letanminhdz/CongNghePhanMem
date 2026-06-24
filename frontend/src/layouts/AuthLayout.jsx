import React from 'react';
import { Outlet, Link } from 'react-router-dom';

const AuthLayout = () => {
  return (
    <div className="min-h-screen w-full bg-background flex flex-col relative items-center justify-center p-6 text-foreground font-sans">
      {/* Nút quay lại trang chủ ở góc trên cùng trái */}
      <div className="absolute top-6 left-6">
        <Link to="/" className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors font-medium">
          <iconify-icon icon="lucide:arrow-left"></iconify-icon>
          Home
        </Link>
      </div>

      <div className="w-full max-w-md bg-card rounded-2xl shadow-sm p-8 border border-border">
        <Outlet />
      </div>
    </div>
  );
};

export default AuthLayout;
