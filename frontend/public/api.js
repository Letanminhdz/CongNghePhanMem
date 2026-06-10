const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:8000/api/v1' : '/api/v1';

window.apiClient = {
  getToken() {
    return localStorage.getItem('access_token');
  },
  setToken(token) {
    localStorage.setItem('access_token', token);
  },
  clearToken() {
    localStorage.removeItem('access_token');
  },

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(url, { ...options, headers });
      
      if (response.status === 401) {
        this.clearToken();
        window.location.href = '/Log In.html';
        throw new Error('Unauthorized');
      }
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'An error occurred');
      }
      
      return data;
    } catch (error) {
      console.error('API Request Error:', error);
      throw error;
    }
  },

  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/login/access-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: formData
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    this.setToken(data.access_token);
    return data;
  },

  async getMe() {
    return this.request('/users/me');
  }
};
