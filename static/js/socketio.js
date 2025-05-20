// socketio.js - Handles WebSocket communication for real-time updates

// SocketIO instance
let socket;

// Connect to WebSocket server
function connectWebSocket() {
    // Connect to the socket.io server
    socket = io();
    
    // Connection established
    socket.on('connect', function() {
        console.log('WebSocket connected');
        document.getElementById('connection-status').innerHTML = 
            '<span class="badge bg-success">Connected</span>';
        
        // Request initial status
        socket.emit('request_status');
    });
    
    // Connection lost
    socket.on('disconnect', function() {
        console.log('WebSocket disconnected');
        document.getElementById('connection-status').innerHTML = 
            '<span class="badge bg-danger">Disconnected</span>';
    });
    
    // Handle bot status updates
    socket.on('status_update', function(status) {
        updateBotStatus(status);
    });
    
    // Handle bot events
    socket.on('bot_event', function(event) {
        displayBotEvent(event);
    });
    
    // Handle game updates
    socket.on('game_update', function(data) {
        updateGameData(data);
    });
}

// Update the bot status display
function updateBotStatus(status) {
    // Update online status indicator
    const statusIndicator = document.getElementById('bot-status');
    if (statusIndicator) {
        if (status.online) {
            statusIndicator.innerHTML = '<span class="badge bg-success">Online</span>';
        } else {
            statusIndicator.innerHTML = '<span class="badge bg-danger">Offline</span>';
        }
    }
    
    // Update uptime
    const uptimeElement = document.getElementById('bot-uptime');
    if (uptimeElement && status.uptime) {
        uptimeElement.textContent = status.uptime;
    }
    
    // Update guild count
    const guildCountElement = document.getElementById('guild-count');
    if (guildCountElement) {
        guildCountElement.textContent = status.guilds;
    }
    
    // Update commands used
    const commandsUsedElement = document.getElementById('commands-used');
    if (commandsUsedElement) {
        commandsUsedElement.textContent = status.commands_used || 0;
    }
    
    // Update active users
    const activeUsersElement = document.getElementById('active-users');
    if (activeUsersElement && status.active_users !== undefined) {
        activeUsersElement.textContent = status.active_users;
    }
    
    // Update total focus score
    const totalScoreElement = document.getElementById('total-focus-score');
    if (totalScoreElement && status.total_focus_score !== undefined) {
        totalScoreElement.textContent = status.total_focus_score;
    }
    
    // Update last command info
    const lastCommandElement = document.getElementById('last-command');
    if (lastCommandElement && status.last_command) {
        const command = status.last_command;
        const timeAgo = timeAgoFromISOString(command.time);
        lastCommandElement.innerHTML = `<strong>${command.name}</strong> by ${command.user} (${timeAgo})`;
    }
}

// Display bot events in the event log
function displayBotEvent(event) {
    const eventLog = document.getElementById('event-log');
    if (!eventLog) return;
    
    // Create event entry
    const eventEntry = document.createElement('div');
    eventEntry.className = 'alert alert-info mb-2';
    
    // Format based on event type
    let content = '';
    switch (event.type) {
        case 'command_used':
            content = `<strong>Command Used:</strong> /${event.data.name} by ${event.data.user}`;
            break;
        case 'guild_join':
            content = `<strong>Joined Server:</strong> ${event.data.name}`;
            break;
        case 'guild_leave':
            content = `<strong>Left Server:</strong> ${event.data.name}`;
            break;
        case 'focus_start':
            content = `<strong>Focus Session Started:</strong> User ${event.data.user}`;
            break;
        case 'focus_end':
            content = `<strong>Focus Session Ended:</strong> User ${event.data.user} (Score: ${event.data.score})`;
            break;
        default:
            content = `<strong>${event.type}:</strong> ${JSON.stringify(event.data)}`;
    }
    
    eventEntry.innerHTML = content;
    
    // Add timestamp
    const timestamp = document.createElement('small');
    timestamp.className = 'text-muted d-block mt-1';
    timestamp.textContent = new Date().toLocaleTimeString();
    eventEntry.appendChild(timestamp);
    
    // Add to log and limit entries
    eventLog.prepend(eventEntry);
    
    // Limit to 10 most recent events
    const maxEvents = 10;
    while (eventLog.children.length > maxEvents) {
        eventLog.removeChild(eventLog.lastChild);
    }
}

// Update game data display
function updateGameData(data) {
    // Update leaderboard if it exists
    updateLeaderboard(data);
    
    // Update active games if element exists
    const activeGamesElement = document.getElementById('active-games');
    if (activeGamesElement) {
        // Try to add or update player entry
        const playerId = data.user_id;
        let playerElement = document.getElementById(`player-${playerId}`);
        
        if (!playerElement && data.score > 0) {
            // Create new entry
            playerElement = document.createElement('li');
            playerElement.id = `player-${playerId}`;
            playerElement.className = 'list-group-item d-flex justify-content-between align-items-center';
            activeGamesElement.appendChild(playerElement);
        }
        
        if (playerElement) {
            if (data.score <= 0) {
                // Remove player if score is zero (session ended)
                playerElement.remove();
            } else {
                // Update player data
                playerElement.innerHTML = `
                    <div>
                        <span class="fw-bold">User ${data.user_id}</span>
                        <div class="progress mt-1" style="height: 5px;">
                            <div class="progress-bar bg-success" style="width: ${Math.min(100, data.score/10)}%"></div>
                        </div>
                    </div>
                    <span class="badge bg-primary rounded-pill">${data.score}</span>
                `;
            }
        }
    }
}

// Update leaderboard with new data
function updateLeaderboard(newData) {
    const leaderboardTable = document.getElementById('leaderboard-table');
    if (!leaderboardTable) return;
    
    // Check if player already exists in table
    const rows = leaderboardTable.querySelectorAll('tbody tr');
    let found = false;
    
    // Update existing row or add to scores array for resorting
    const scores = [];
    rows.forEach(row => {
        const userId = row.getAttribute('data-user-id');
        const scoreCell = row.querySelector('.score-cell');
        
        if (userId === newData.user_id) {
            found = true;
            scoreCell.textContent = newData.score;
        }
        
        scores.push({
            userId: userId,
            score: parseInt(scoreCell.textContent),
            row: row
        });
    });
    
    // Add new row if not found
    if (!found && newData.score > 0) {
        const newRow = document.createElement('tr');
        newRow.setAttribute('data-user-id', newData.user_id);
        
        newRow.innerHTML = `
            <td class="rank-cell"></td>
            <td>User ${newData.user_id}</td>
            <td class="score-cell">${newData.score}</td>
        `;
        
        scores.push({
            userId: newData.user_id,
            score: newData.score,
            row: newRow
        });
    }
    
    // Sort scores and rebuild table
    scores.sort((a, b) => b.score - a.score);
    
    const tbody = leaderboardTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    scores.forEach((item, index) => {
        // Update rank
        const rankCell = item.row.querySelector('.rank-cell');
        rankCell.textContent = index + 1;
        
        // Add medal for top 3
        if (index < 3) {
            rankCell.innerHTML = rankCell.textContent + ' ' + 
                ['🥇', '🥈', '🥉'][index];
        }
        
        tbody.appendChild(item.row);
    });
}

// Helper function to format time ago
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

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    connectWebSocket();
});
