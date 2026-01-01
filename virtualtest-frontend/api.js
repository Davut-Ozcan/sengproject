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
        throw new Error(error.detail || 'Login failed');
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
        throw new Error(error.detail || 'Registration failed');
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
        throw new Error('Invalid session');
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
        throw new Error(error.detail || 'Test could not be started');
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
        throw new Error(error.detail || 'Module could not be started');
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
        throw new Error(error.detail || 'Answers could not be submitted');
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
        throw new Error('Progress could not be retrieved');
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
        throw new Error('Result could not be retrieved');
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

// ==========================================
// USER MENU DROPDOWN
// ==========================================

function toggleUserMenu(event) {
    // Stop event propagation to prevent document click from closing immediately
    if (event) {
        event.stopPropagation();
    }
    
    const dropdown = document.getElementById('user-menu-dropdown');
    const button = document.getElementById('user-menu-btn');
    
    if (!dropdown || !button) {
        console.error('User menu elements not found');
        return;
    }
    
    const isOpen = dropdown.classList.contains('show');
    
    // Close all dropdowns first
    document.querySelectorAll('.user-menu-dropdown').forEach(menu => {
        menu.classList.remove('show');
    });
    document.querySelectorAll('.user-menu-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Toggle current dropdown
    if (!isOpen) {
        dropdown.classList.add('show');
        button.classList.add('active');
    }
}

function handleLogout() {
    showConfirm(
        'Logout',
        'Are you sure you want to logout?',
        function() {
            apiLogout();
        }
    );
}

// ==========================================
// CUSTOM MODAL FUNCTIONS
// ==========================================

function showModal(type, title, message, buttons) {
    const modal = document.getElementById('custom-modal');
    const iconEl = document.getElementById('modal-icon');
    const titleEl = document.getElementById('modal-title');
    const messageEl = document.getElementById('modal-message');
    const buttonsEl = document.getElementById('modal-buttons');
    
    // Set icon and type
    const iconMap = {
        'info': 'fa-info-circle',
        'success': 'fa-check-circle',
        'warning': 'fa-exclamation-triangle',
        'error': 'fa-times-circle',
        'question': 'fa-right-from-bracket'
    };
    
    iconEl.className = `fa-solid ${iconMap[type] || iconMap.info}`;
    iconEl.parentElement.className = `custom-modal-icon ${type}`;
    
    // Set content
    titleEl.textContent = title;
    messageEl.textContent = message;
    
    // Clear and add buttons
    buttonsEl.innerHTML = '';
    if (buttons && buttons.length > 0) {
        buttons.forEach(btn => {
            const button = document.createElement('button');
            button.className = `custom-modal-btn ${btn.class || 'custom-modal-btn-primary'}`;
            button.textContent = btn.text;
            button.onclick = function() {
                if (btn.onclick) {
                    btn.onclick();
                }
                closeModal();
            };
            buttonsEl.appendChild(button);
        });
    } else {
        // Default OK button
        const okButton = document.createElement('button');
        okButton.className = 'custom-modal-btn custom-modal-btn-primary';
        okButton.textContent = 'OK';
        okButton.onclick = closeModal;
        buttonsEl.appendChild(okButton);
    }
    
    // Show modal
    modal.classList.add('show');
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    const modal = document.getElementById('custom-modal');
    modal.classList.remove('show');
    document.body.style.overflow = '';
}

function showAlert(title, message, type = 'info') {
    return new Promise((resolve) => {
        showModal(type, title, message, [
            {
                text: 'OK',
                class: 'custom-modal-btn-primary',
                onclick: () => resolve(true)
            }
        ]);
    });
}

function showConfirm(title, message, onConfirm, onCancel = null) {
    return new Promise((resolve) => {
        showModal('question', title, message, [
            {
                text: 'Cancel',
                class: 'custom-modal-btn-secondary',
                onclick: () => {
                    if (onCancel) onCancel();
                    resolve(false);
                }
            },
            {
                text: 'Confirm',
                class: 'custom-modal-btn-primary',
                onclick: () => {
                    resolve(true);
                    if (onConfirm) onConfirm();
                }
            }
        ]);
    });
}

// Close modal when clicking overlay
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        const modal = document.getElementById('custom-modal');
        if (modal) {
            const overlay = modal.querySelector('.custom-modal-overlay');
            if (overlay) {
                overlay.addEventListener('click', function(e) {
                    if (e.target === overlay) {
                        closeModal();
                    }
                });
            }
        }
    });
}

// Close dropdown when clicking outside
if (typeof document !== 'undefined') {
    // Use a small delay to ensure this runs after button click handlers
    document.addEventListener('click', function(event) {
        // Don't close if clicking inside the user menu container
        const container = event.target.closest('.user-menu-container');
        if (container) {
            return;
        }
        
        // Close all dropdowns
        document.querySelectorAll('.user-menu-dropdown').forEach(menu => {
            menu.classList.remove('show');
        });
        document.querySelectorAll('.user-menu-btn').forEach(btn => {
            btn.classList.remove('active');
        });
    });
}