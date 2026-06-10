// auth.js - Tự động xử lý xác thực cho giao diện
window.API_BASE = "http://localhost:8000";

async function loginAdmin() {
    const params = new URLSearchParams();
    params.append('username', 'admin@example.com');
    params.append('password', 'admin123');

    try {
        const response = await fetch(`${window.API_BASE}/api/v1/login/access-token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: params
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            console.log("Logged in automatically as admin");
            return data.access_token;
        } else {
            console.error("Failed to login as admin");
        }
    } catch (e) {
        console.error("Login request failed", e);
    }
    return null;
}

window.fetchWithAuth = async function(url, options = {}) {
    let token = localStorage.getItem('access_token');
    if (!token) {
        token = await loginAdmin();
    }
    
    if (!options.headers) {
        options.headers = {};
    }
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    let response = await fetch(url, options);
    
    // Nếu token hết hạn, thử đăng nhập lại 1 lần
    if (response.status === 401 || response.status === 403) {
        token = await loginAdmin();
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
            response = await fetch(url, options);
        }
    }
    
    return response;
};

// Tự động gọi login ngay khi script được nạp để lấy sẵn token
if (!localStorage.getItem('access_token')) {
    loginAdmin();
}
