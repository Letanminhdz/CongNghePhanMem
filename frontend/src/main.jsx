import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

import { ThemeProvider } from 'next-themes'
import { OpenAPI } from './client/core/OpenAPI'
import { UserProvider } from './context/UserContext'

OpenAPI.BASE = import.meta.env.VITE_API_URL || '';
OpenAPI.TOKEN = async () => {
  return localStorage.getItem('access_token') || '';
};

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
      <UserProvider>
        <App />
      </UserProvider>
    </ThemeProvider>
  </StrictMode>,
)
