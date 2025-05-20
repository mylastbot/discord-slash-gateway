// main.js - Main JavaScript functionality for the web interface

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize status refresh
    initStatusRefresh();
    
    // Initialize UI event handlers
    initUIHandlers();
});

// Initialize automatic status refresh
function initStatusRefresh() {
    // Function to refresh bot status manually
    window.refreshBotStatus = function() {
        fetch('/api/bot/status')
            .then(response => response.json())
            .then(data => {
                updateStatusDisplay(data);
            })
            .catch(error => {
                console.error('Error fetching bot status:', error);
            });
    };
    
    // Set interval for periodic updates (every 30 seconds)
    setInterval(refreshBotStatus, 30000);
    
    // Initial status update
    refreshBotStatus();
}

// Update status display with data
function updateStatusDisplay(data) {
    // Update status indicator
    const statusBadge = document.getElementById('status-badge');
    if (statusBadge) {
        statusBadge.className = data.online ? 'badge bg-success' : 'badge bg-danger';
        statusBadge.textContent = data.online ? 'Online' : 'Offline';
    }
    
    // Update other status elements
    updateElement('guilds-count', data.guilds);
    updateElement('uptime-display', data.uptime);
    updateElement('commands-count', data.commands_used);
    
    // Update active users if available
    if (data.active_users !== undefined) {
        updateElement('active-users-count', data.active_users);
    }
    
    // Update last command info
    if (data.last_command) {
        const lastCmd = document.getElementById('last-command-info');
        if (lastCmd) {
            const cmd = data.last_command;
            const timeAgo = timeAgoFromISOString(cmd.time);
            lastCmd.innerHTML = `<strong>${cmd.name}</strong> by ${cmd.user} (${timeAgo})`;
        }
    }
    
    // Update active focus sessions
    updateActiveSessions(data);
}

// Helper to update element content
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element && value !== undefined) {
        element.textContent = value;
    }
}

// Update active focus sessions display
function updateActiveSessions(data) {
    // This would be populated by socket.io events
    // This function can be used for initial data loading
}

// Initialize UI event handlers
function initUIHandlers() {
    // Toggle sidebar on mobile
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.body.classList.toggle('sidebar-collapsed');
        });
    }
    
    // Event log clear button
    const clearLogBtn = document.getElementById('clear-log-btn');
    if (clearLogBtn) {
        clearLogBtn.addEventListener('click', function() {
            const eventLog = document.getElementById('event-log');
            if (eventLog) {
                eventLog.innerHTML = '';
            }
        });
    }
    
    // Tab switching
    const dashboardTabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    dashboardTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            // Maybe trigger specific updates when switching tabs
            const targetTab = event.target.getAttribute('aria-controls');
            if (targetTab === 'leaderboard') {
                // Could refresh leaderboard data here
            }
        });
    });
}

// Helper function for time formatting
function timeAgoFromISOString(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.round(diffMs / 1000);
    
    if (diffSec < 60) {
        return `${diffSec} seconds ago`;
    }
    
    const diffMin = Math.round(diffSec / 60);
    if (diffMin < 60) {
        return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
    }
    
    const diffHour = Math.round(diffMin / 60);
    if (diffHour < 24) {
        return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`;
    }
    
    const diffDay = Math.round(diffHour / 24);
    return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`;
}

// Format a duration in seconds to a human-readable string
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds}s`;
    }
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
        return `${minutes}m ${seconds % 60}s`;
    }
    
    const hours = Math.floor(minutes / 60);
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
}
