// ============================================
// api.js - Backend API İletişimi
// ============================================

const API_BASE_URL = 'http://localhost:8000/api';

// ==========================================
// TOKEN YÖNETİMİ
// ==========================================

function getToken() {
    return localStorage.getItem('access_token');
}

function setToken(token) {
    localStorage.setItem('access_token', token);
}

function removeToken() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
}

function getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

function isLoggedIn() {
    return !!getToken();
}

// ==========================================
// AUTH API
// ==========================================

async function apiLogin(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'username': email,
            'password': password
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Giriş başarısız');
    }
    
    const data = await response.json();
    setToken(data.access_token);
    setUser({
        id: data.user_id,
        email: data.email,
        role: data.role,
        full_name: data.full_name
    });
    
    return data;
}

async function apiRegister(email, password, fullName) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            password: password,
            password_confirm: password,
            full_name: fullName
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Kayıt başarısız');
    }
    
    const data = await response.json();
    setToken(data.access_token);
    setUser({
        id: data.user_id,
        email: data.email,
        role: 'Student',
        full_name: fullName
    });
    
    return data;
}

async function apiLogout() {
    removeToken();
    window.location.href = 'login.html';
}

async function apiGetMe() {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
            'Authorization': `Bearer ${getToken()}`
        }
    });
    
    if (!response.ok) {
        throw new Error('Oturum geçersiz');
    }
    
    return await response.json();
}

// ==========================================
// TEST API
// ==========================================

async function apiStartTest() {
    const response = await fetch(`${API_BASE_URL}/test/start`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        }
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Test başlatılamadı');
    }
    
    const data = await response.json();
    localStorage.setItem('current_session', JSON.stringify(data));
    return data;
}

async function apiStartModule(sessionId, moduleName, cefrLevel = 'B1') {
    const response = await fetch(`${API_BASE_URL}/test/module/start`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: sessionId,
            module_name: moduleName,
            cefr_level: cefrLevel
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Modül başlatılamadı');
    }
    
    return await response.json();
}

async function apiSubmitModule(sessionId, moduleName, data) {
    const body = {
        session_id: sessionId,
        module_name: moduleName,
        ...data
    };
    
    const response = await fetch(`${API_BASE_URL}/test/module/submit`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Cevaplar gönderilemedi');
    }
    
    return await response.json();
}

async function apiGetProgress(sessionId) {
    const response = await fetch(`${API_BASE_URL}/test/progress/${sessionId}`, {
        headers: {
            'Authorization': `Bearer ${getToken()}`
        }
    });
    
    if (!response.ok) {
        throw new Error('İlerleme alınamadı');
    }
    
    return await response.json();
}

async function apiGetResult(sessionId) {
    const response = await fetch(`${API_BASE_URL}/test/result/${sessionId}`, {
        headers: {
            'Authorization': `Bearer ${getToken()}`
        }
    });
    
    if (!response.ok) {
        throw new Error('Sonuç alınamadı');
    }
    
    return await response.json();
}

// ==========================================
// YARDIMCI FONKSİYONLAR
// ==========================================

function getCurrentSession() {
    const session = localStorage.getItem('current_session');
    return session ? JSON.parse(session) : null;
}

function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

function updateUserUI() {
    const user = getUser();
    if (user) {
        document.querySelectorAll('.u-name').forEach(el => {
            el.textContent = user.full_name || user.email;
        });
    }
}