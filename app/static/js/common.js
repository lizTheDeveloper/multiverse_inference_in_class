/**
 * Common JavaScript utilities for Multiverse Inference Gateway Web UI
 * 
 * Provides API client, toast notifications, utilities, and helpers.
 */

// =============================================================================
// API Client
// =============================================================================

class APIClient {
    constructor() {
        this.baseURL = window.location.origin;
        this.apiKey = localStorage.getItem('apiKey') || '';
    }

    /**
     * Get headers for API requests
     */
    getHeaders(includeApiKey = false) {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (includeApiKey && this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }
        
        return headers;
    }

    /**
     * Make a GET request
     */
    async get(endpoint, requiresAuth = false) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'GET',
                headers: this.getHeaders(requiresAuth)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error?.message || error.detail || 'Request failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('GET request failed:', error);
            throw error;
        }
    }

    /**
     * Make a POST request
     */
    async post(endpoint, data, requiresAuth = false) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'POST',
                headers: this.getHeaders(requiresAuth),
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error?.message || error.detail || 'Request failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('POST request failed:', error);
            throw error;
        }
    }

    /**
     * Make a PUT request
     */
    async put(endpoint, data, requiresAuth = false) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'PUT',
                headers: this.getHeaders(requiresAuth),
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error?.message || error.detail || 'Request failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('PUT request failed:', error);
            throw error;
        }
    }

    /**
     * Make a DELETE request
     */
    async delete(endpoint, requiresAuth = false) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'DELETE',
                headers: this.getHeaders(requiresAuth)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error?.message || error.detail || 'Request failed');
            }
            
            return response.status === 204 ? null : await response.json();
        } catch (error) {
            console.error('DELETE request failed:', error);
            throw error;
        }
    }

    /**
     * Create a streaming connection (SSE)
     */
    createStreamingRequest(endpoint, data, onChunk, onComplete, onError) {
        // For SSE streaming, we use fetch with ReadableStream
        fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers: this.getHeaders(false),
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            function processChunk() {
                return reader.read().then(({ done, value }) => {
                    if (done) {
                        onComplete();
                        return;
                    }
                    
                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.substring(6);
                            if (data === '[DONE]') {
                                onComplete();
                                return;
                            }
                            try {
                                const parsed = JSON.parse(data);
                                onChunk(parsed);
                            } catch (e) {
                                console.warn('Failed to parse chunk:', e);
                            }
                        }
                    }
                    
                    return processChunk();
                });
            }
            
            return processChunk();
        })
        .catch(error => {
            console.error('Streaming request failed:', error);
            onError(error);
        });
    }
}

// Global API client instance
const api = new APIClient();

// =============================================================================
// Toast Notifications
// =============================================================================

class ToastNotification {
    constructor() {
        this.container = document.getElementById('toast-container');
    }

    /**
     * Show a toast notification
     */
    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast max-w-sm w-full shadow-lg rounded-lg pointer-events-auto overflow-hidden`;
        
        // Set colors based on type
        let bgColor, iconSvg;
        switch(type) {
            case 'success':
                bgColor = 'bg-green-50';
                iconSvg = `<svg class="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>`;
                break;
            case 'error':
                bgColor = 'bg-red-50';
                iconSvg = `<svg class="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>`;
                break;
            case 'warning':
                bgColor = 'bg-yellow-50';
                iconSvg = `<svg class="h-6 w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>`;
                break;
            default: // info
                bgColor = 'bg-blue-50';
                iconSvg = `<svg class="h-6 w-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                </svg>`;
        }
        
        toast.innerHTML = `
            <div class="${bgColor} p-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        ${iconSvg}
                    </div>
                    <div class="ml-3 flex-1 pt-0.5">
                        <p class="text-sm font-medium text-gray-900">${message}</p>
                    </div>
                    <div class="ml-4 flex flex-shrink-0">
                        <button onclick="this.parentElement.parentElement.parentElement.parentElement.remove()" 
                                class="inline-flex rounded-md ${bgColor} text-gray-400 hover:text-gray-500 focus:outline-none">
                            <span class="sr-only">Close</span>
                            <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        this.container.appendChild(toast);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                toast.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
    }

    success(message, duration) {
        this.show(message, 'success', duration);
    }

    error(message, duration) {
        this.show(message, 'error', duration);
    }

    warning(message, duration) {
        this.show(message, 'warning', duration);
    }

    info(message, duration) {
        this.show(message, 'info', duration);
    }
}

// Global toast instance
const toast = new ToastNotification();

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Debounce function to limit rate of function calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Format timestamp to readable string
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

/**
 * Format relative time (e.g., "2 minutes ago")
 */
function formatRelativeTime(timestamp) {
    if (!timestamp) return 'Never';
    
    const now = new Date();
    const date = new Date(timestamp);
    const diff = Math.floor((now - date) / 1000); // seconds
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    return `${Math.floor(diff / 86400)} days ago`;
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        toast.success('Copied to clipboard!');
    } catch (error) {
        toast.error('Failed to copy to clipboard');
        console.error('Copy failed:', error);
    }
}

/**
 * Get health status badge HTML
 */
function getHealthBadge(status) {
    const statusMap = {
        'healthy': { class: 'status-healthy', text: 'Healthy' },
        'unhealthy': { class: 'status-unhealthy', text: 'Unhealthy' },
        'unknown': { class: 'status-unknown', text: 'Unknown' }
    };
    
    const config = statusMap[status] || statusMap['unknown'];
    return `<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.class}">${config.text}</span>`;
}

/**
 * Show loading state
 */
function showLoading(element, show = true) {
    if (show) {
        element.disabled = true;
        element.dataset.originalText = element.innerHTML;
        element.innerHTML = `
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Loading...
        `;
    } else {
        element.disabled = false;
        element.innerHTML = element.dataset.originalText || 'Submit';
    }
}

/**
 * Validate URL format
 */
function isValidURL(url) {
    try {
        const parsed = new URL(url);
        return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    } catch {
        return false;
    }
}

/**
 * Check if user is authenticated (has API key)
 */
function isAuthenticated() {
    return localStorage.getItem('apiKey') !== null && localStorage.getItem('apiKey') !== '';
}

/**
 * Prompt for API key if not authenticated
 */
function requireAuth(callback) {
    if (!isAuthenticated()) {
        toast.warning('Please set your admin API key first');
        // Trigger the Alpine.js modal
        window.dispatchEvent(new CustomEvent('show-api-key-modal'));
        return false;
    }
    if (callback) callback();
    return true;
}

// =============================================================================
// Initialize on page load
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Multiverse Gateway UI loaded');
    
    // Check if we're on a protected page and API key is needed
    const protectedPages = ['/register', '/dashboard'];
    const currentPath = window.location.pathname;
    
    if (protectedPages.some(page => currentPath.startsWith(page)) && !isAuthenticated()) {
        // Don't show toast immediately, let user see the page first
        setTimeout(() => {
            toast.info('Set your admin API key to access management features', 8000);
        }, 1000);
    }
});

// Export for use in other scripts
window.api = api;
window.toast = toast;
window.debounce = debounce;
window.formatTimestamp = formatTimestamp;
window.formatRelativeTime = formatRelativeTime;
window.copyToClipboard = copyToClipboard;
window.getHealthBadge = getHealthBadge;
window.showLoading = showLoading;
window.isValidURL = isValidURL;
window.isAuthenticated = isAuthenticated;
window.requireAuth = requireAuth;

