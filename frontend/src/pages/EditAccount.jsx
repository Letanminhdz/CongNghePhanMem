import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const EditAccount = () => {
  const navigate = useNavigate();
  const [userName, setUserName] = useState('Alex Morgan');

  const handleSave = () => {
    // Save logic would go here
    navigate(-1);
  };

  return (
    <div className="flex flex-col items-center justify-center w-full h-full min-h-[calc(100vh-12rem)]">
      <div className="w-full max-w-[800px] bg-card rounded-2xl shadow-sm border border-border flex flex-col relative p-8">
        {/* Top: Back & Title */}
        <div className="flex items-center gap-4 mb-6">
          <button 
            onClick={() => navigate(-1)} 
            className="p-2 hover:bg-muted rounded-full transition-colors text-muted-foreground hover:text-foreground -ml-2"
          >
            <iconify-icon icon="lucide:arrow-left" class="text-xl"></iconify-icon>
          </button>
          <h1 className="text-2xl font-bold text-foreground">Edit Account</h1>
        </div>

        {/* Center Area: Form & Avatar */}
        <div className="flex-1 flex flex-col max-w-md mx-auto w-full">
          {/* Avatar Upload */}
          <div className="flex justify-center mb-4">
            <div className="relative">
              <img src="https://randomuser.me/api/portraits/men/32.jpg" alt="Profile Avatar" className="w-24 h-24 rounded-full object-cover border-2 border-border shadow-sm" />
              <button className="absolute bottom-0 right-0 bg-card border border-border text-foreground p-2 rounded-full shadow-sm hover:bg-muted transition-colors flex items-center justify-center">
                <iconify-icon icon="lucide:camera" class="text-sm"></iconify-icon>
              </button>
            </div>
          </div>

          {/* Form Fields */}
          <div className="flex flex-col gap-6">
            {/* User Name */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-foreground ml-1">User Name</label>
              <input 
                type="text" 
                value={userName} 
                onChange={(e) => setUserName(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" 
              />
            </div>
          </div>
        </div>

        {/* Bottom Right: Save Button */}
        <div className="flex justify-end mt-4">
          <button 
            onClick={handleSave}
            className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-full text-sm font-medium shadow-sm transition-colors"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default EditAccount;
