import React, { createContext, useContext, useState, useEffect } from 'react';
import { UsersService } from '../client';

const UserContext = createContext(null);

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return null;
    }
    try {
      const data = await UsersService.readCurrentUserApiV1UsersMeGet();
      setUser(data);
      return data;
    } catch (err) {
      console.error('Failed to fetch current user', err);
      localStorage.removeItem('access_token');
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const updateUser = (newData) => {
    setUser(prev => ({ ...prev, ...newData }));
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return (
    <UserContext.Provider value={{ user, loading, fetchUser, updateUser, logout }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);
