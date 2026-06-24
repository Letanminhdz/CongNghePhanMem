import React, { useState, useEffect } from 'react';
import { AdminService } from '../client';

const roleOptions = ['User', 'Administrator'];

const statusStyle = {
  Active: 'text-green-600',
  Suspended: 'text-destructive',
};
const statusDot = {
  Active: 'bg-green-600',
  Suspended: 'bg-destructive',
};
const roleBadge = {
  User: 'bg-accent text-foreground',
  Administrator: 'bg-purple-50 text-purple-700',
};

// Helper to assign randomish colors based on id
const getColorForId = (id) => {
  const colors = [
    'bg-primary/10 text-primary',
    'bg-blue-100 text-blue-600',
    'bg-emerald-100 text-emerald-600',
    'bg-amber-100 text-amber-600',
    'bg-purple-100 text-purple-600',
    'bg-rose-100 text-rose-600'
  ];
  const num = typeof id === 'number' ? id : String(id).length;
  return colors[num % colors.length];
};

const getInitials = (name, email) => {
  if (name) {
    const parts = name.split(' ');
    if (parts.length > 1) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.slice(0, 2).toUpperCase();
  }
  return email.slice(0, 2).toUpperCase();
};

const AdminUserManagement = () => {
  const [users, setUsers] = useState([]);
  const [editingUser, setEditingUser] = useState(null);
  const [selectedRole, setSelectedRole] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await AdminService.getUsersApiV1AdminUsersGet({ limit: 100, skip: 0 });
      // Map API response to UI format
      const formattedUsers = (Array.isArray(data) ? data : []).map(u => ({
        id: u.id,
        initials: getInitials(u.full_name, u.email),
        bg: getColorForId(u.id),
        name: u.full_name || 'No Name',
        email: u.email,
        role: u.is_superuser ? 'Administrator' : 'User',
        status: u.is_active ? 'Active' : 'Suspended',
        lastLogin: new Date(u.created_at).toLocaleDateString()
      }));
      setUsers(formattedUsers);
    } catch (err) {
      console.error('Failed to fetch users', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const openEdit = (user) => {
    setEditingUser(user);
    setSelectedRole(user.role);
  };
  const closeEdit = () => setEditingUser(null);

  const handleSaveRole = async () => {
    try {
      await AdminService.updateUserRoleApiV1AdminUsersIdRolePut({
        id: editingUser.id,
        isSuperuser: selectedRole === 'Administrator'
      });
      setUsers(prev => prev.map(u => u.id === editingUser.id ? { ...u, role: selectedRole } : u));
      closeEdit();
    } catch (err) {
      console.error('Failed to update role', err);
      alert('Failed to update role');
    }
  };

  const handleToggleStatus = async (id, currentStatus) => {
    try {
      const newStatus = currentStatus === 'Active' ? 'Suspended' : 'Active';
      const isActive = newStatus === 'Active';
      await AdminService.updateUserStatusApiV1AdminUsersIdStatusPut({
        id,
        isActive
      });
      setUsers(prev => prev.map(u => u.id === id ? { ...u, status: newStatus } : u));
    } catch (err) {
      console.error('Failed to toggle status', err);
      alert('Failed to change status');
    }
  };

  return (
    <>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-heading font-semibold">User Management</h1>
          <span className="px-2 py-0.5 rounded-md bg-accent text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
            {loading ? '...' : users.length.toLocaleString()} Total Users
          </span>
        </div>
      </div>

      <div className="space-y-6">
        {/* Table */}
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-accent/50 border-b border-border">
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">User</th>
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Role</th>
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Created At</th>
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr><td colSpan={5} className="px-6 py-12 text-center text-muted-foreground text-sm">Loading users...</td></tr>
                ) : users.length === 0 ? (
                  <tr><td colSpan={5} className="px-6 py-12 text-center text-muted-foreground text-sm">No users found.</td></tr>
                ) : (
                  users.map((u) => (
                    <tr key={u.id} className="hover:bg-accent/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0 ${u.bg}`}>{u.initials}</div>
                          <div className="flex flex-col">
                            <span className="font-medium text-sm">{u.name}</span>
                            <span className="text-xs text-muted-foreground">{u.email}</span>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${roleBadge[u.role] || 'bg-accent text-foreground'}`}>{u.role}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`flex items-center gap-1.5 text-xs font-medium ${statusStyle[u.status]}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${statusDot[u.status]}`}></span>
                          {u.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">{u.lastLogin}</td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => openEdit(u)}
                            className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-primary transition-colors"
                            title="Edit Role"
                          >
                            <iconify-icon icon="lucide:pencil"></iconify-icon>
                          </button>
                          <button
                            onClick={() => handleToggleStatus(u.id, u.status)}
                            className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-primary transition-colors"
                            title="Block/Unblock account"
                          >
                            <iconify-icon icon={u.status === 'Suspended' ? 'lucide:lock' : 'lucide:lock-open'}></iconify-icon>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Edit Role Modal */}
      {editingUser && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={closeEdit}>
          <div className="bg-card rounded-2xl shadow-xl border border-border w-full max-w-sm" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-6 border-b border-border">
              <h2 className="text-lg font-heading font-semibold text-foreground">Edit User Role</h2>
              <button onClick={closeEdit} className="p-1.5 rounded-full hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">
                <iconify-icon icon="lucide:x" class="text-xl"></iconify-icon>
              </button>
            </div>
            <div className="p-6">
              {/* User Info */}
              <div className="flex items-center gap-3 mb-6 p-4 bg-accent/50 rounded-xl">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0 ${editingUser.bg}`}>
                  {editingUser.initials}
                </div>
                <div>
                  <p className="font-medium text-sm text-foreground">{editingUser.name}</p>
                  <p className="text-xs text-muted-foreground">{editingUser.email}</p>
                </div>
              </div>

              {/* Role Select */}
              <div className="mb-6">
                <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                  Role
                </label>
                <div className="flex flex-col gap-2">
                  {roleOptions.map(role => (
                    <label
                      key={role}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${selectedRole === role
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:bg-accent/50'
                        }`}
                    >
                      <input
                        type="radio"
                        name="role"
                        value={role}
                        checked={selectedRole === role}
                        onChange={() => setSelectedRole(role)}
                        className="accent-primary"
                      />
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${roleBadge[role] || 'bg-accent text-foreground'}`}>{role}</span>
                        <span className="text-xs text-muted-foreground">
                          {role === 'User' && '— Truy cập cơ bản'}
                          {role === 'Administrator' && '— Toàn quyền quản trị'}
                        </span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={handleSaveRole}
                  className="px-5 py-2 bg-primary text-primary-foreground rounded-full text-sm font-medium hover:bg-primary/90 transition-colors"
                >
                  Save Changes
                </button>
                <button
                  onClick={closeEdit}
                  className="px-5 py-2 border border-border rounded-full text-sm font-medium hover:bg-muted transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AdminUserManagement;
