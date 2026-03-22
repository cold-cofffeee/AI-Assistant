// Common utility functions for all pages

// Show loading state
function showLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'block';
    }
}

// Hide loading state
function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

// Show output section
function showOutput() {
    const output = document.getElementById('outputSection');
    if (output) {
        output.style.display = 'block';
        // Smooth scroll to output
        output.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Hide output section
function hideOutput() {
    const output = document.getElementById('outputSection');
    if (output) {
        output.style.display = 'none';
    }
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        // Smooth scroll to error
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Hide error message
function hideError() {
    const errorDiv = document.getElementById('error');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

// Validate input text
function validateInput(text, minLength = 1) {
    if (!text || text.trim().length === 0) {
        return { valid: false, message: 'Please enter some text.' };
    }
    
    if (text.trim().length < minLength) {
        return { valid: false, message: `Text must be at least ${minLength} characters long.` };
    }
    
    return { valid: true };
}

// Handle API responses
async function handleApiResponse(response) {
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.error || `Server error: ${response.status}`);
    }
    
    return data;
}

// Make API request with error handling
async function makeApiRequest(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        return await handleApiResponse(response);
    } catch (error) {
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            throw new Error('Network error. Please check your connection and try again.');
        }
        throw error;
    }
}

// Format text for display
function formatText(text) {
    return text
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/^/, '<p>')
        .replace(/$/, '</p>');
}

function escapeHtml(text) {
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function applyInlineMarkdown(text) {
    return text
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
}

function renderAiOutput(text) {
    if (!text) {
        return '';
    }

    const normalized = String(text).replace(/\r\n/g, '\n');
    const lines = normalized.split('\n');
    const htmlParts = [];
    let inUnorderedList = false;
    let inOrderedList = false;

    const closeLists = () => {
        if (inUnorderedList) {
            htmlParts.push('</ul>');
            inUnorderedList = false;
        }
        if (inOrderedList) {
            htmlParts.push('</ol>');
            inOrderedList = false;
        }
    };

    for (const rawLine of lines) {
        const line = rawLine.trim();

        if (!line) {
            closeLists();
            continue;
        }

        const safeLine = applyInlineMarkdown(escapeHtml(line));

        if (line.startsWith('### ')) {
            closeLists();
            htmlParts.push(`<h3>${applyInlineMarkdown(escapeHtml(line.slice(4)))}</h3>`);
            continue;
        }

        if (line.startsWith('## ')) {
            closeLists();
            htmlParts.push(`<h2>${applyInlineMarkdown(escapeHtml(line.slice(3)))}</h2>`);
            continue;
        }

        if (line.startsWith('# ')) {
            closeLists();
            htmlParts.push(`<h1>${applyInlineMarkdown(escapeHtml(line.slice(2)))}</h1>`);
            continue;
        }

        if (line.startsWith('- ') || line.startsWith('* ')) {
            if (inOrderedList) {
                htmlParts.push('</ol>');
                inOrderedList = false;
            }
            if (!inUnorderedList) {
                htmlParts.push('<ul>');
                inUnorderedList = true;
            }
            htmlParts.push(`<li>${applyInlineMarkdown(escapeHtml(line.slice(2).trim()))}</li>`);
            continue;
        }

        if (/^\d+\.\s+/.test(line)) {
            if (inUnorderedList) {
                htmlParts.push('</ul>');
                inUnorderedList = false;
            }
            if (!inOrderedList) {
                htmlParts.push('<ol>');
                inOrderedList = true;
            }
            htmlParts.push(`<li>${applyInlineMarkdown(escapeHtml(line.replace(/^\d+\.\s+/, '')))}</li>`);
            continue;
        }

        closeLists();
        htmlParts.push(`<p>${safeLine}</p>`);
    }

    closeLists();
    return htmlParts.join('');
}

// Copy text to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied to clipboard!');
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showToast('Copied to clipboard!');
    }
}

// Show toast notification
function showToast(message, duration = 3000) {
    // Remove existing toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create new toast
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #2c3e50;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        font-size: 14px;
        font-weight: 500;
        transform: translateX(400px);
        transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Animate out and remove
    setTimeout(() => {
        toast.style.transform = 'translateX(400px)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, duration);
}

// Add copy buttons to result boxes
function addCopyButton(resultElement) {
    const copyBtn = document.createElement('button');
    copyBtn.textContent = 'Copy';
    copyBtn.className = 'copy-btn';
    copyBtn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        background: #667eea;
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
        opacity: 0.8;
        transition: opacity 0.2s;
    `;
    
    copyBtn.addEventListener('click', () => {
        const text = resultElement.textContent || resultElement.innerText;
        copyToClipboard(text);
    });
    
    copyBtn.addEventListener('mouseenter', () => {
        copyBtn.style.opacity = '1';
    });
    
    copyBtn.addEventListener('mouseleave', () => {
        copyBtn.style.opacity = '0.8';
    });
    
    // Make parent relative if not already
    if (getComputedStyle(resultElement).position === 'static') {
        resultElement.style.position = 'relative';
    }
    
    resultElement.appendChild(copyBtn);
}

// Initialize page-specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling to all internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    // Add focus management for better accessibility
    const inputs = document.querySelectorAll('input, textarea');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.style.borderColor = '#667eea';
            this.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
        });
        
        input.addEventListener('blur', function() {
            this.style.borderColor = '#e0e6ed';
            this.style.boxShadow = 'none';
        });
    });
    
    // Add enter key support for single-line inputs
    document.querySelectorAll('input[type="text"]').forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const button = this.parentElement.querySelector('button');
                if (button) {
                    button.click();
                }
            }
        });
    });
    
    // Auto-resize textareas
    document.querySelectorAll('textarea').forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });
});

// Add loading state to buttons
function setButtonLoading(button, loading = true) {
    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = '<span class="spinner" style="width: 16px; height: 16px; margin-right: 8px;"></span>Loading...';
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || button.textContent;
    }
}

// Debounce function for search/input optimization
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