let currentMode = 'gui';
let ws = null;
let isJobRunning = false;

// DOM Elements
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const taskInput = document.getElementById('task-input');
const terminal = document.getElementById('terminal-output');
const statusIndicator = document.getElementById('status-indicator');
const visualizer = document.getElementById('visualizer');
const screenshotView = document.getElementById('screenshot-view');
const clickOverlay = document.getElementById('click-overlay');
const permissionBox = document.getElementById('permission-request');

function setMode(mode) {
    if (isJobRunning) {
        alert("Please stop the current task before switching modes.");
        return;
    }
    currentMode = mode;

    // Update UI
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    if (mode === 'code') {
        visualizer.classList.add('hidden');
    } else {
        visualizer.classList.remove('hidden');
    }

    log("system", `Switched to ${mode.toUpperCase()} Agent mode.`);
}

function connectWS() {
    return new Promise((resolve, reject) => {
        if (ws) {
            ws.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(`${protocol}//${window.location.host}/ws/${currentMode}`);

        ws.onopen = () => {
            updateStatus('Connected', 'success');
            resolve();
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            handleMessage(msg);
        };

        ws.onclose = () => {
            updateStatus('Disconnected', 'error');
            isJobRunning = false;
            toggleControls(false);
        };

        ws.onerror = (error) => {
            log("error", "WebSocket Error");
            console.error(error);
        };
    });
}

function handleMessage(msg) {
    // console.log("Received:", msg);

    switch (msg.type) {
        case 'ai_content':
            if (msg.content !== '[BEGIN]' && msg.content !== '[END]') {
                appendToLastLog(msg.content);
            } else if (msg.content === '[BEGIN]') {
                createNewLogEntry('ai');
            }
            break;

        case 'status':
            // Handle block start/stop
            if (msg.content === '[START]') {
                updateStatus('Running', 'warning');
            } else if (msg.content === '[STOP]') {
                updateStatus('Idle', 'success');
                isJobRunning = false;
                toggleControls(false);
                log("system", "Task finished or stopped.");
            } else {
                log("system", `Status: ${msg.content}`);
            }
            break;

        case 'image/png':
        case 'image/jpeg':
            // Update Screenshot
            if (currentMode === 'gui' || currentMode === 'code') {
                visualizer.classList.remove('hidden');
                screenshotView.src = `data:${msg.type};base64,${msg.content}`;

                // Reset overlays
                clickOverlay.style.display = 'none';
            }
            break;

        case 'action_point':
            // Draw red dot
            showActionPoint(msg.content);
            log("system", `Action: ${msg.content.action} at (${msg.content.x}, ${msg.content.y})`);
            break;

        case 'request':
            if (msg.content && msg.content.includes('need_permission')) {
                showPermissionRequest();
                log("system", "Waiting for user permission...");
            } else if (msg.content === 'stop_agent') {
                // handled by status [STOP] usually
            }
            break;

        case 'text':
            log("user", msg.content);
            break;

        case 'error':
            log("error", msg.content);
            break;
    }
}

async function startTask() {
    const task = taskInput.value.trim();
    if (!task) return alert("Please enter a task description.");

    clearLogs();
    log("system", "Initializing Agent...");

    await connectWS();

    ws.send(JSON.stringify({
        action: 'start',
        task: task
    }));

    isJobRunning = true;
    toggleControls(true);
}

function stopTask() {
    if (ws) {
        ws.send(JSON.stringify({ action: 'stop' }));
        log("system", "Sending stop signal...");
    }
}

function sendPermission(decision) {
    if (ws) {
        ws.send(JSON.stringify({
            action: 'input',
            content: decision
        }));
        permissionBox.classList.add('hidden');
        log("user", `Permission ${decision}.`);
    }
}

/* UI Helpers */

function toggleControls(running) {
    startBtn.disabled = running;
    stopBtn.disabled = !running;
    taskInput.disabled = running;
    document.querySelectorAll('.mode-btn').forEach(b => b.disabled = running);
}

function updateStatus(text, state) {
    statusIndicator.innerHTML = `<span class="status-dot" style="background-color: var(--${state}-color); box-shadow: 0 0 8px var(--${state}-color);"></span> ${text}`;
}

function showPermissionRequest() {
    permissionBox.classList.remove('hidden');
    // Scroll to bottom control panel
    permissionBox.scrollIntoView({ behavior: 'smooth' });
}

function showActionPoint(coords) {
    // Show overlay
    // Need to handle scaling. Simple approach: wait for image load
    // But since image is base64, it loads instantly mostly.

    // We need 'naturalWidth' of the image
    const natW = screenshotView.naturalWidth;
    const natH = screenshotView.naturalHeight;
    const clientW = screenshotView.clientWidth;
    const clientH = screenshotView.clientHeight;

    if (natW && clientW) {
        const scaleX = clientW / natW;
        const scaleY = clientH / natH;

        // Center the dot
        // Assuming image is centered in container with object-fit: contain
        // Setting coords directly on image if possible is hard if object-fit adds empty space
        // A better way is: place marker relative to image

        // Simplified: just log it for now as CSS mapping is complex with object-fit: contain
        // But let's try a best effort if image fills width

        // Actually, screenshotView is inside a flex container. 
        // Let's just put the marker on the screenshotView parent and use %

        const left = (coords.x / natW) * 100;
        const top = (coords.y / natH) * 100;

        clickOverlay.style.left = `${left}%`;
        clickOverlay.style.top = `${top}%`;
        clickOverlay.style.display = 'block';
    }
}

// Log Management
let currentLogType = null;
let lastLogEntry = null;

function createNewLogEntry(type) {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    terminal.appendChild(entry);
    terminal.scrollTop = terminal.scrollHeight;
    lastLogEntry = entry;
    currentLogType = type;
}

function appendToLastLog(text) {
    if (currentLogType === 'ai' && lastLogEntry) {
        lastLogEntry.textContent += text;
        terminal.scrollTop = terminal.scrollHeight;
    } else {
        log('ai', text);
    }
}

function log(type, text) {
    createNewLogEntry(type);
    lastLogEntry.textContent = `> ${text}`;
    currentLogType = null; // Reset specific stream tracking
}

function clearLogs() {
    terminal.innerHTML = '';
}

// Init
log("system", "Ready to initialize.");
