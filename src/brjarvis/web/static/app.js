// web/app.js — BR JARVIS Next-Generation AI Workspace Client Engine v41.0.3
(function (window, document) {
    'use strict';

    const host = window.location.host || '127.0.0.1:8000';
    const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const API_BASE = `${protocol}://${host}`;

    // ── HELPER: Safe HTML escaping ──
    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function debounce(func, delay = 200) {
        let timer = null;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => func.apply(this, args), delay);
        };
    }

    
    // ── THEME TOGGLE ──
    function getPreferredTheme() {
        const stored = localStorage.getItem('jarvis_theme');
        if (stored) return stored;
        return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('jarvis_theme', theme);
        const darkIcon = document.querySelector('.theme-icon-dark');
        const lightIcon = document.querySelector('.theme-icon-light');
        if (darkIcon) darkIcon.style.display = theme === 'dark' ? 'inline' : 'none';
        if (lightIcon) lightIcon.style.display = theme === 'light' ? 'inline' : 'none';
    }

    window.toggleTheme = function() {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        applyTheme(current === 'dark' ? 'light' : 'dark');
    };

    // Apply saved theme on load
    applyTheme(getPreferredTheme());

// ── GLOBAL WORKSPACE STATE ──
    let currentConversationId = localStorage.getItem('jarvis_active_conversation_id') || null;
    let currentBranchId = 'main';
    let currentProjectId = null;
    let isGenerating = false;
    let activeStreamMsgBubble = null;
    let activeStreamTextEl = null;

    let socket = null;
    let heartbeatInterval = null;
    let wsReconnectDelay = 1000;
    let wsReconnectTimer = null;
    let serverApiKey = '';

    // ── AUTHENTICATION & API WRAPPER ──
    window.getServerApiKey = function () {
        return serverApiKey;
    };

    window.setServerApiKey = function (key) {
        serverApiKey = key || '';
        localStorage.removeItem('jarvis_server_api_key');
        localStorage.removeItem('jarvis_api_key');
    };

    window.apiFetch = async function (url, options = {}) {
        const opts = Object.assign({}, options);
        opts.headers = Object.assign({}, opts.headers || {});
        opts.credentials = 'include';

        const apiKey = window.getServerApiKey();
        if (apiKey && !opts.headers['Authorization'] && !opts.headers['X-API-Key']) {
            opts.headers['Authorization'] = `Bearer ${apiKey}`;
            opts.headers['X-API-Key'] = apiKey;
        }

        try {
            const res = await fetch(url, opts);
            if (res.status === 401 && !url.includes('/api/auth/status') && !url.includes('/api/auth/login')) {
                window.showServerAuthModal();
            }
            return res;
        } catch (err) {
            console.debug('Network fetch error:', url, err);
            throw err;
        }
    };

    // ── MODAL HELPERS (Globally Bound Early) ──
    window.showServerAuthModal = function () {
        const modal = document.getElementById('serverAuthModal');
        if (modal) {
            modal.style.display = 'flex';
            const input = document.getElementById('serverApiKeyInput');
            if (input) {
                input.value = '';
                setTimeout(() => input.focus(), 50);
            }
        }
    };

    window.closeServerAuthModal = function () {
        const modal = document.getElementById('serverAuthModal');
        if (modal) modal.style.display = 'none';
    };

    window.submitServerAuth = async function () {
        const input = document.getElementById('serverApiKeyInput');
        const apiKey = input ? input.value.trim() : '';
        if (!apiKey) return;
        try {
            const response = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey }),
            });
            if (!response.ok) throw new Error('Invalid server API key');
            window.setServerApiKey('');
            if (input) input.value = '';
            window.closeServerAuthModal();
            if (socket) socket.close();
            if (window.reconnectWebSocket) window.reconnectWebSocket();
            window.showToast('Authenticated', 'Secure server session established.', 'success');
        } catch (error) {
            window.showToast('Authentication failed', String(error), 'error');
        }
    };

    window.openNewProjectModal = function () {
        const modal = document.getElementById('newProjectModal');
        if (modal) {
            modal.style.display = 'flex';
            const input = document.getElementById('newProjectName');
            if (input) setTimeout(() => input.focus(), 50);
        }
    };

    window.closeNewProjectModal = function () {
        const modal = document.getElementById('newProjectModal');
        if (modal) modal.style.display = 'none';
    };

    window.openArtifactPreviewModal = function () {
        const modal = document.getElementById('artifactPreviewModal');
        if (modal) modal.style.display = 'flex';
    };

    window.closeArtifactPreviewModal = function () {
        const modal = document.getElementById('artifactPreviewModal');
        if (modal) modal.style.display = 'none';
    };

    window.openAddContactModal = function () {
        const modal = document.getElementById('addContactModal');
        if (modal) {
            modal.style.display = 'flex';
            const input = document.getElementById('addContactName');
            if (input) setTimeout(() => input.focus(), 50);
        }
    };

    window.closeAddContactModal = function () {
        const modal = document.getElementById('addContactModal');
        if (modal) modal.style.display = 'none';
    };

    window.openCommandPalette = function () {
        const modal = document.getElementById('cmdPaletteModal');
        const input = document.getElementById('cmdPaletteInput');
        const results = document.getElementById('cmdPaletteResults');
        if (modal) {
            modal.style.display = 'flex';
            if (input) {
                input.value = '';
                setTimeout(() => input.focus(), 50);
            }
            if (results) results.innerHTML = '<div class="sidebar-empty-state">Type to search conversations, projects, files, tasks, artifacts...</div>';
        }
    };

    window.closeCommandPalette = function () {
        const modal = document.getElementById('cmdPaletteModal');
        if (modal) modal.style.display = 'none';
    };

    // ── TOAST NOTIFICATIONS ──
    window.showToast = function (title, message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const titleEl = document.createElement('div');
        titleEl.className = 'toast-title';
        titleEl.textContent = title;

        const msgEl = document.createElement('div');
        msgEl.className = 'toast-msg';
        msgEl.textContent = message;

        toast.appendChild(titleEl);
        toast.appendChild(msgEl);
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 400);
        }, 4000);
    };

    // ── VIEW SWITCHING (Globally Accessible) ──
    window.switchView = function (viewId) {
        const navItems = document.querySelectorAll('.nav-item');
        const viewContainers = document.querySelectorAll('.view-container');

        navItems.forEach(item => {
            if (item.dataset.view === viewId) item.classList.add('active');
            else item.classList.remove('active');
        });
        viewContainers.forEach(container => {
            if (container.id === viewId) container.classList.add('active');
            else container.classList.remove('active');
        });

        const sidebarNav = document.getElementById('sidebarNav');
        if (sidebarNav && sidebarNav.classList.contains('mobile-open')) {
            sidebarNav.classList.remove('mobile-open');
        }

        if (viewId === 'projectsView') window.fetchProjects();
        if (viewId === 'artifactsView') window.fetchArtifacts();
        if (viewId === 'automationsView') window.fetchAutomations();
        if (viewId === 'contactsView') window.fetchContacts();
        if (viewId === 'connectorsView') window.fetchConnectors();
        if (viewId === 'skillsView') window.fetchSkills();
        if (viewId === 'knowledgeView') window.fetchMemories();
        if (viewId === 'careerView') window.loadCareerProfile();
    };

        // ── DESKTOP WORKSPACE HANDOFF ──
    window.redeemWorkspaceHandoff = async function () {
        const params = new URLSearchParams(window.location.search);
        const handoff = params.get('handoff');
        if (!handoff) return true;
        try {
            const response = await fetch(`${API_BASE}/api/auth/desktop-handoff/redeem`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ handoff }),
            });
            if (!response.ok) throw new Error('Workspace handoff expired or was already used.');
            params.delete('handoff');
            const cleanQuery = params.toString();
            window.history.replaceState({}, document.title, `${window.location.pathname}${cleanQuery ? `?${cleanQuery}` : ''}${window.location.hash}`);
            return true;
        } catch (error) {
            console.error('Workspace handoff failed:', error);
            window.showToast('Workspace connection failed', String(error.message || error), 'error');
            return false;
        }
    };

    // ── INITIALIZATION ON DOM READY ──
    document.addEventListener('DOMContentLoaded', async () => {
        await window.redeemWorkspaceHandoff();

        // DOM Elements
        const networkLatencyEl = document.getElementById('network-latency');
        const backendSelector = document.getElementById('backendSelector');
        const roleSelector = document.getElementById('roleSelector');
        const permissionSelector = document.getElementById('permissionSelector');
        const systemTimeEl = document.getElementById('system-time');

        const chatWindow = document.getElementById('chatWindow');
        const chatInput = document.getElementById('chatInput');
        const sendChatBtn = document.getElementById('sendChatBtn');
        const planOnlyCheckbox = document.getElementById('planOnlyCheckbox');
        const draftStatusIndicator = document.getElementById('draftStatusIndicator');
        const attachFileBtn = document.getElementById('attachFileBtn');
        const chatFileInput = document.getElementById('chatFileInput');

        const activeConvTitle = document.getElementById('activeConvTitle');
        const activeBranchBadge = document.getElementById('activeBranchBadge');
        const headerConvTitle = document.getElementById('headerConvTitle');
        const headerProjectPill = document.getElementById('headerProjectPill');

        const newChatBtn = document.getElementById('newChatBtn');
        const convSearchFilter = document.getElementById('convSearchFilter');
        const convListPinned = document.getElementById('convListPinned');
        const convListRecent = document.getElementById('convListRecent');
        const convListArchived = document.getElementById('convListArchived');
        const convGroupPinned = document.getElementById('convGroupPinned');
        const convGroupArchived = document.getElementById('convGroupArchived');
        const pinnedCount = document.getElementById('pinnedCount');
        const recentCount = document.getElementById('recentCount');
        const archivedCount = document.getElementById('archivedCount');

        const toggleRightPanelBtn = document.getElementById('toggleRightPanelBtn');
        const rightContextPanel = document.getElementById('rightContextPanel');
        const contextTabBtns = document.querySelectorAll('.context-tab-btn');
        const contextTabContents = document.querySelectorAll('.context-tab-content');

        // Header Action Buttons
        const branchConvBtn = document.getElementById('branchConvBtn');
        const duplicateConvBtn = document.getElementById('duplicateConvBtn');
        const exportConvBtn = document.getElementById('exportConvBtn');
        const pinConvBtn = document.getElementById('pinConvBtn');
        const openAddContactBtn = document.getElementById('openAddContactBtn');
        const cmdPaletteTrigger = document.getElementById('cmdPaletteTrigger');
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');

        // Telemetry & Gauges
        const cpuRing = document.getElementById('cpu-ring');
        const ramRing = document.getElementById('ram-ring');
        const diskRing = document.getElementById('disk-ring');
        const cpuValue = document.getElementById('cpu-value');
        const ramValue = document.getElementById('ram-value');
        const diskValue = document.getElementById('disk-value');

        // ── TELEMETRY GAUGE UPDATER ──
        function setGauge(ring, textEl, value) {
            if (!ring || !textEl) return;
            const val = Math.min(100, Math.max(0, parseFloat(value) || 0));
            const offset = 188.4 - (188.4 * val) / 100;
            ring.style.strokeDashoffset = offset;
            textEl.textContent = `${Math.round(val)}%`;
        }

        function fetchTelemetry() {
            const startTime = Date.now();
            window.apiFetch(`${API_BASE}/health`)
                .then(res => res.json())
                .then(data => {
                    const latency = Date.now() - startTime;
                    if (networkLatencyEl) networkLatencyEl.textContent = `${latency}ms`;
                    if (data.cpu_percent !== undefined) setGauge(cpuRing, cpuValue, data.cpu_percent);
                    if (data.memory_percent !== undefined) setGauge(ramRing, ramValue, data.memory_percent);
                    if (data.disk_percent !== undefined) setGauge(diskRing, diskValue, data.disk_percent);
                })
                .catch(() => {});
        }
        setInterval(fetchTelemetry, 10000);

        function updateSystemTime() {
            if (systemTimeEl) systemTimeEl.textContent = new Date().toLocaleTimeString();
        }
        setInterval(updateSystemTime, 1000);
        updateSystemTime();

        // ── EVENT BINDINGS FOR BUTTONS ──
        if (newChatBtn) {
            newChatBtn.addEventListener('click', (e) => {
                e.preventDefault();
                window.createNewConversation();
            });
        }

        if (sendChatBtn) {
            sendChatBtn.addEventListener('click', (e) => {
                e.preventDefault();
                handleSendMessage();
            });
        }

        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                }
            });
            chatInput.addEventListener('input', debounce(() => {
                if (currentConversationId) {
                    localStorage.setItem(`jarvis_draft_${currentConversationId}`, chatInput.value);
                    if (draftStatusIndicator) draftStatusIndicator.textContent = chatInput.value ? 'Draft saved' : '';
                }
            }, 300));
        }

        if (attachFileBtn && chatFileInput) {
            attachFileBtn.addEventListener('click', () => chatFileInput.click());
            chatFileInput.addEventListener('change', async () => {
                const file = chatFileInput.files && chatFileInput.files[0];
                if (!file) return;
                const form = new FormData();
                form.append('file', file, file.name);
                window.showToast('Attachment', `Importing ${file.name}…`, 'info');
                try {
                    const response = await window.apiFetch(`${API_BASE}/api/import/file`, { method: 'POST', body: form });
                    const payload = await response.json().catch(() => ({}));
                    if (!response.ok) throw new Error(payload?.error?.message || payload?.detail || `HTTP ${response.status}`);
                    window.showToast('Attachment imported', payload.message || `${file.name} is available to the knowledge workflow.`, 'success');
                } catch (error) {
                    window.showToast('Attachment import failed', String(error), 'error');
                } finally {
                    chatFileInput.value = '';
                }
            });
        }

        if (toggleRightPanelBtn && rightContextPanel) {
            toggleRightPanelBtn.addEventListener('click', () => {
                rightContextPanel.classList.toggle('collapsed');
            });
        }

        if (mobileMenuToggle) {
            mobileMenuToggle.addEventListener('click', () => {
                const sidebar = document.getElementById('sidebarNav');
                if (sidebar) sidebar.classList.toggle('mobile-open');
            });
        }

        if (cmdPaletteTrigger) {
            cmdPaletteTrigger.addEventListener('click', window.openCommandPalette);
        }

        if (openAddContactBtn) {
            openAddContactBtn.addEventListener('click', window.openAddContactModal);
        }

        if (branchConvBtn) {
            branchConvBtn.addEventListener('click', () => {
                if (currentConversationId) window.branchConversation(currentConversationId);
            });
        }

        if (duplicateConvBtn) {
            duplicateConvBtn.addEventListener('click', () => {
                if (currentConversationId) window.duplicateConversation(currentConversationId);
            });
        }

        if (exportConvBtn) {
            exportConvBtn.addEventListener('click', () => {
                if (currentConversationId) window.exportConversation(currentConversationId);
            });
        }

        if (pinConvBtn) {
            pinConvBtn.addEventListener('click', () => {
                if (currentConversationId) window.togglePinConversation(currentConversationId, true);
            });
        }

        // Navigation Menu
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const viewId = item.dataset.view;
                if (viewId) window.switchView(viewId);
            });
        });

        // Context Tabs
        contextTabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.dataset.tab;
                contextTabBtns.forEach(b => b.classList.remove('active'));
                contextTabContents.forEach(c => c.classList.remove('active'));
                btn.classList.add('active');
                const targetEl = document.getElementById(targetTab);
                if (targetEl) targetEl.classList.add('active');

                if (targetTab === 'tabMemory') window.fetchMemories();
                if (targetTab === 'tabArtifacts') window.fetchTabArtifacts();
                if (targetTab === 'tabFiles') window.fetchTabFiles();
            });
        });

        // Search Filter in Sidebar
        if (convSearchFilter) {
            convSearchFilter.addEventListener('input', debounce(fetchConversations, 200));
        }

        // Global Shortcuts
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                const modal = document.getElementById('cmdPaletteModal');
                if (modal && modal.style.display === 'flex') {
                    window.closeCommandPalette();
                } else {
                    window.openCommandPalette();
                }
            } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'n') {
                e.preventDefault();
                window.createNewConversation();
            } else if (e.key === 'Escape') {
                window.closeCommandPalette();
                window.closeArtifactPreviewModal();
                window.closeNewProjectModal();
                window.closeServerAuthModal();
                window.closeAddContactModal();
            }
        });

        // ── WEBSOCKET CONNECTION & STREAMING ──
        function _setWsStatus(connected) {
            document.querySelectorAll('.ws-status-dot').forEach(el => {
                el.style.background = connected ? 'var(--accent-green, #00dfa2)' : '#ff4444';
            });
        }

        async function initWebSocket() {
            if (socket && (socket.readyState === WebSocket.CONNECTING || socket.readyState === WebSocket.OPEN)) return;

            try {
                const ticketResponse = await window.apiFetch(`${API_BASE}/api/auth/ws-ticket`, { method: 'POST' });
                if (!ticketResponse.ok) {
                    window.showServerAuthModal();
                    return;
                }
                const ticketPayload = await ticketResponse.json();
                const wsUrl = `${wsProtocol}://${host}/ws?ticket=${encodeURIComponent(ticketPayload.ticket)}`;

                socket = new WebSocket(wsUrl);

                socket.onopen = () => {
                    wsReconnectDelay = 1000;
                    _setWsStatus(true);
                    window.dispatchEvent(new CustomEvent('brjarvis:legacy-connection', { detail: { status: 'connected' } }));
                    fetchTelemetry();

                    fetchConnectorStatus();

                    if (heartbeatInterval) clearInterval(heartbeatInterval);
                    heartbeatInterval = setInterval(() => {
                        if (socket && socket.readyState === WebSocket.OPEN) {
                            socket.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
                        }
                    }, 25000);
                };

                socket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        handleServerMessage(data);
                    } catch (e) {
                        console.log('WS Raw Message:', event.data);
                    }
                };

                socket.onclose = () => {
                    _setWsStatus(false);
                    window.dispatchEvent(new CustomEvent('brjarvis:legacy-connection', { detail: { status: 'reconnecting' } }));

                    if (heartbeatInterval) clearInterval(heartbeatInterval);
                    if (wsReconnectTimer) clearTimeout(wsReconnectTimer);
                    wsReconnectTimer = setTimeout(initWebSocket, wsReconnectDelay);
                    wsReconnectDelay = Math.min(wsReconnectDelay * 2, 30000);
                };

                socket.onerror = () => {
                    _setWsStatus(false);
                    window.dispatchEvent(new CustomEvent('brjarvis:legacy-connection', { detail: { status: 'error' } }));

                };
            } catch (e) {
                console.error('WebSocket Init Error:', e);
            }
        }

        // ── WEBSOCKET MESSAGE HANDLER ──
        function handleServerMessage(data) {
            window.dispatchEvent(new CustomEvent('brjarvis:legacy-message', { detail: data }));
            const type = (data.type || '').toLowerCase();

            const payload = data.payload || {};

            if (type === 'message.delta_start' || type === 'stream_start') {
                isGenerating = true;
                if (sendChatBtn) sendChatBtn.textContent = 'STOP ⏹';
                createStreamingAssistantBubble();
            } else if (type === 'message.delta' || type === 'stream_chunk') {
                const token = payload.delta || payload.chunk || data.text || '';
                appendStreamToken(token);
            } else if (type === 'message.completed' || type === 'stream_end') {
                isGenerating = false;
                if (sendChatBtn) sendChatBtn.textContent = 'SEND ▸';
                finalizeStreamingAssistantBubble();
                fetchConversations();
                window.fetchTabArtifacts();
            } else if (type === 'task.started') {
                const taskBadge = document.getElementById('taskStatusBadge');
                if (taskBadge) taskBadge.textContent = 'RUNNING';
                const goalBox = document.getElementById('taskGoalDisplay');
                if (goalBox) goalBox.textContent = payload.goal || 'Executing autonomous task...';
            } else if (type === 'task.completed') {
                const taskBadge = document.getElementById('taskStatusBadge');
                if (taskBadge) taskBadge.textContent = 'SUCCESS';
                window.showToast('Task Completed', 'Task fulfilled and verified.', 'success');
            } else if (type === 'notification.created') {
                window.showToast(payload.title || 'Notification', payload.message || '', payload.severity || 'info');
            }
        }

        // ── CONVERSATIONS CRUD ──
        async function fetchConversations() {
            try {
                const searchVal = convSearchFilter ? convSearchFilter.value.trim() : '';
                let url = `${API_BASE}/api/conversations?include_archived=true`;
                if (currentProjectId) url += `&project_id=${encodeURIComponent(currentProjectId)}`;
                if (searchVal) url += `&search=${encodeURIComponent(searchVal)}`;

                const res = await window.apiFetch(url);
                if (!res.ok) return;
                const data = await res.json();
                renderConversationsSidebar(data.conversations || []);
            } catch (e) {
                console.debug('Error fetching conversations:', e);
            }
        }

        function renderConversationsSidebar(conversations) {
            if (!convListRecent) return;

            const pinned = conversations.filter(c => c.pinned && !c.archived);
            const recent = conversations.filter(c => !c.pinned && !c.archived);
            const archived = conversations.filter(c => c.archived);

            if (pinnedCount) pinnedCount.textContent = pinned.length;
            if (recentCount) recentCount.textContent = recent.length;
            if (archivedCount) archivedCount.textContent = archived.length;

            if (convGroupPinned) convGroupPinned.style.display = pinned.length ? 'flex' : 'none';
            if (convGroupArchived) convGroupArchived.style.display = archived.length ? 'flex' : 'none';

            if (convListPinned) {
                convListPinned.innerHTML = '';
                pinned.forEach(c => convListPinned.appendChild(createConvItemEl(c)));
            }

            convListRecent.innerHTML = '';
            if (recent.length === 0) {
                convListRecent.innerHTML = '<div class="sidebar-empty-state">No conversations yet. Click + New Chat</div>';
            } else {
                recent.forEach(c => convListRecent.appendChild(createConvItemEl(c)));
            }

            if (convListArchived) {
                convListArchived.innerHTML = '';
                archived.forEach(c => convListArchived.appendChild(createConvItemEl(c)));
            }
        }

        function createConvItemEl(conv) {
            const item = document.createElement('div');
            item.className = `conv-item ${conv.conversation_id === currentConversationId ? 'active' : ''}`;
            item.dataset.id = conv.conversation_id;

            const mainDiv = document.createElement('div');
            mainDiv.className = 'conv-item-main';
            mainDiv.onclick = () => window.selectConversation(conv.conversation_id);

            const titleSpan = document.createElement('span');
            titleSpan.className = 'conv-item-title';
            titleSpan.textContent = conv.title || 'New Chat';

            const metaDiv = document.createElement('div');
            metaDiv.className = 'conv-item-meta';
            const dateStr = new Date(conv.updated_at * 1000).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
            metaDiv.innerHTML = `<span>${dateStr}</span>${conv.pinned ? '<span>📌</span>' : ''}`;

            mainDiv.appendChild(titleSpan);
            mainDiv.appendChild(metaDiv);

            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'conv-item-actions';

            const btn = document.createElement('button');
            btn.className = 'ellipsis-btn';
            btn.innerHTML = '⋮';
            btn.title = 'Options';
            btn.onclick = (e) => {
                e.stopPropagation();
                window.renameConversation(conv.conversation_id, conv.title);
            };

            actionsDiv.appendChild(btn);
            item.appendChild(mainDiv);
            item.appendChild(actionsDiv);
            return item;
        }

        window.createNewConversation = async function () {
            try {
                const res = await window.apiFetch(`${API_BASE}/api/conversations`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: 'New Chat', project_id: currentProjectId }),
                });
                if (res.ok) {
                    const data = await res.json();
                    const conv = data.conversation;
                    currentConversationId = conv.conversation_id;
                    currentBranchId = 'main';
                    localStorage.setItem('jarvis_active_conversation_id', currentConversationId);
                    updateConversationHeader(conv);
                    clearChatWindow();
                    fetchConversations();
                    window.switchView('chatView');
                    if (chatInput) {
                        chatInput.value = '';
                        chatInput.focus();
                    }
                    window.showToast('New Chat', 'Fresh conversation ready.', 'info');
                }
            } catch (e) {
                console.error('Error creating conversation:', e);
            }
        };

        window.selectConversation = async function (convId) {
            if (!convId) return;
            currentConversationId = convId;
            localStorage.setItem('jarvis_active_conversation_id', convId);

            try {
                const res = await window.apiFetch(`${API_BASE}/api/conversations/${convId}`);
                if (!res.ok) return;
                const data = await res.json();
                const conv = data.conversation;
                const messages = data.messages || [];

                updateConversationHeader(conv);
                renderTranscript(messages);
                fetchConversations();
                window.switchView('chatView');

                const savedDraft = localStorage.getItem(`jarvis_draft_${convId}`);
                if (chatInput && savedDraft) {
                    chatInput.value = savedDraft;
                    if (draftStatusIndicator) draftStatusIndicator.textContent = 'Draft restored';
                }
            } catch (e) {
                console.error('Error loading conversation:', e);
            }
        };

        window.renameConversation = async function (convId, currentTitle) {
            const newTitle = prompt('Enter new conversation title:', currentTitle || '');
            if (newTitle && newTitle.trim()) {
                await window.apiFetch(`${API_BASE}/api/conversations/${convId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: newTitle.trim() }),
                });
                fetchConversations();
                if (convId === currentConversationId) {
                    if (activeConvTitle) activeConvTitle.textContent = newTitle.trim();
                    if (headerConvTitle) headerConvTitle.textContent = newTitle.trim();
                }
            }
        };

        window.togglePinConversation = async function (convId, pinned) {
            await window.apiFetch(`${API_BASE}/api/conversations/${convId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pinned: pinned }),
            });
            fetchConversations();
        };

        window.duplicateConversation = async function (convId) {
            const res = await window.apiFetch(`${API_BASE}/api/conversations/${convId}/duplicate`, { method: 'POST' });
            if (res.ok) {
                const data = await res.json();
                window.selectConversation(data.conversation.conversation_id);
                window.showToast('Duplicated', 'Conversation duplicated.', 'success');
            }
        };

        window.exportConversation = async function (convId) {
            const res = await window.apiFetch(`${API_BASE}/api/conversations/${convId}/export?format=markdown`);
            if (res.ok) {
                const data = await res.json();
                const blob = new Blob([data.content], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = data.filename || 'transcript.md';
                a.click();
                URL.revokeObjectURL(url);
                window.showToast('Export Ready', 'Transcript downloaded.', 'success');
            }
        };

        window.branchConversation = async function (convId) {
            const name = prompt('Branch name:', 'Alternative Branch');
            if (!name) return;
            const res = await window.apiFetch(`${API_BASE}/api/conversations/${convId}/branch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name.trim() }),
            });
            if (res.ok) {
                const d = await res.json();
                currentBranchId = d.branch_id;
                if (activeBranchBadge) activeBranchBadge.textContent = name.trim();
                window.showToast('Branch Created', `Switched to branch '${name}'.`, 'success');
            }
        };

        function updateConversationHeader(conv) {
            if (activeConvTitle) activeConvTitle.textContent = conv.title || 'New Chat';
            if (headerConvTitle) headerConvTitle.textContent = conv.title || 'New Chat';
            if (activeBranchBadge) activeBranchBadge.textContent = conv.active_branch_id || 'main';
            if (headerProjectPill) headerProjectPill.textContent = conv.project_id ? `Proj: ${conv.project_id}` : 'General';
        }

        // ── CHAT TRANSCRIPT RENDERING ──
        function clearChatWindow() {
            if (!chatWindow) return;
            chatWindow.innerHTML = `
                <div class="msg-bubble system">
                    <div class="msg-author">⚡ BR JARVIS COGNITIVE CORE</div>
                    <div class="msg-body">
                        Welcome to <strong>BR JARVIS v41.0.3 Workspace</strong>. Type a question or task request to begin.
                    </div>
                </div>
            `;
        }

        function renderTranscript(messages) {
            if (!chatWindow) return;
            chatWindow.innerHTML = '';
            if (messages.length === 0) {
                clearChatWindow();
                return;
            }

            messages.forEach(msg => {
                const bubble = createMessageBubble(msg);
                chatWindow.appendChild(bubble);
            });
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }

        function createMessageBubble(msg) {
            const bubble = document.createElement('div');
            bubble.className = `msg-bubble ${msg.role === 'user' ? 'user' : 'assistant'}`;

            const authorDiv = document.createElement('div');
            authorDiv.className = 'msg-author';
            authorDiv.innerHTML = `<span>${msg.role === 'user' ? '👤 YOU' : '⚡ JARVIS CORE'}</span>`;
            if (msg.latency_ms) {
                authorDiv.innerHTML += `<span style="font-size:0.6rem; color:var(--text-muted);">${msg.latency_ms}ms</span>`;
            }

            const bodyDiv = document.createElement('div');
            bodyDiv.className = 'msg-body';
            bodyDiv.innerHTML = formatMarkdown(msg.content);

            bubble.appendChild(authorDiv);
            bubble.appendChild(bodyDiv);
            return bubble;
        }

        function createStreamingAssistantBubble() {
            if (!chatWindow) return;
            const bubble = document.createElement('div');
            bubble.className = 'msg-bubble assistant';

            const authorDiv = document.createElement('div');
            authorDiv.className = 'msg-author';
            authorDiv.innerHTML = '<span>⚡ JARVIS CORE <span class="status-pulse" style="display:inline-block; width:6px; height:6px;"></span></span>';

            const bodyDiv = document.createElement('div');
            bodyDiv.className = 'msg-body';
            bodyDiv.innerHTML = '<span class="streaming-text"></span><span class="typing-cursor">▌</span>';

            bubble.appendChild(authorDiv);
            bubble.appendChild(bodyDiv);
            chatWindow.appendChild(bubble);
            chatWindow.scrollTop = chatWindow.scrollHeight;

            activeStreamMsgBubble = bubble;
            activeStreamTextEl = bodyDiv.querySelector('.streaming-text');
        }

        function appendStreamToken(token) {
            if (!activeStreamTextEl) return;
            activeStreamTextEl.dataset.raw = (activeStreamTextEl.dataset.raw || '') + token;
            activeStreamTextEl.innerHTML = formatMarkdown(activeStreamTextEl.dataset.raw);
            if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;
        }

        function finalizeStreamingAssistantBubble() {
            if (activeStreamMsgBubble) {
                const cursor = activeStreamMsgBubble.querySelector('.typing-cursor');
                if (cursor) cursor.remove();
            }
            activeStreamMsgBubble = null;
            activeStreamTextEl = null;
        }

        function formatMarkdown(text) {
            if (!text) return '';
            let html = escapeHTML(text);
            html = html.replace(/```([a-zA-Z0-9_\-]*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
            html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
            html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
            html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
            html = html.replace(/\n/g, '<br>');
            return html;
        }

        // ── SEND MESSAGE ──
        async function handleSendMessage() {
            if (!chatInput) return;
            const text = chatInput.value.trim();
            if (!text) return;

            const isPlanOnly = planOnlyCheckbox ? planOnlyCheckbox.checked : false;
            const backendVal = backendSelector ? backendSelector.value : 'gemini';

            if (!currentConversationId) {
                try {
                    const res = await window.apiFetch(`${API_BASE}/api/conversations`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title: text.slice(0, 30) || 'New Chat', project_id: currentProjectId }),
                    });
                    if (res.ok) {
                        const d = await res.json();
                        currentConversationId = d.conversation.conversation_id;
                        localStorage.setItem('jarvis_active_conversation_id', currentConversationId);
                        updateConversationHeader(d.conversation);
                    }
                } catch (e) {
                    console.debug('Auto-conversation init note:', e);
                }
            }

            const userBubble = createMessageBubble({ role: 'user', content: text });
            if (chatWindow) {
                chatWindow.appendChild(userBubble);
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }

            chatInput.value = '';
            localStorage.removeItem(`jarvis_draft_${currentConversationId}`);
            if (draftStatusIndicator) draftStatusIndicator.textContent = '';

            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({
                    type: 'chat_prompt',
                    message: text,
                    conversation_id: currentConversationId,
                    branch_id: currentBranchId,
                    backend: backendVal,
                    plan_only: isPlanOnly,
                }));
            } else {
                createStreamingAssistantBubble();
                try {
                    const res = await window.apiFetch(`${API_BASE}/api/chat`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            message: text,
                            conversation_id: currentConversationId,
                            branch_id: currentBranchId,
                            backend: backendVal,
                        }),
                    });
                    const d = await res.json();
                    appendStreamToken(d.response || 'Task completed.');
                    finalizeStreamingAssistantBubble();
                    fetchConversations();
                } catch (e) {
                    appendStreamToken('Server communication error.');
                    finalizeStreamingAssistantBubble();
                }
            }
        }
        window.handleSendMessage = handleSendMessage;

        // ── INITIAL FETCHES ──
        fetchConversations();
        window.reconnectWebSocket = initWebSocket;
        initWebSocket();
        if (currentConversationId) {
            window.selectConversation(currentConversationId);
        }
    });

    // ── PROJECTS WORKSPACE ──
    window.fetchProjects = async function () {
        const grid = document.getElementById('projectsGrid');
        if (!grid) return;
        try {
            const res = await window.apiFetch(`${API_BASE}/api/projects`);
            if (!res.ok) return;
            const data = await res.json();
            const projects = data.projects || [];

            grid.innerHTML = '';
            if (projects.length === 0) {
                grid.innerHTML = '<div class="sidebar-empty-state">No projects created yet. Click "+ New Project" to organize workspaces.</div>';
                return;
            }

            projects.forEach(p => {
                const card = document.createElement('div');
                card.className = 'connector-card';
                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <h3 style="color:#fff; font-family:var(--font-heading);">${escapeHTML(p.name)}</h3>
                        <span class="os-badge">${p.pinned ? '📌 PINNED' : 'ACTIVE'}</span>
                    </div>
                    <p style="color:var(--text-secondary); font-size:0.82rem; margin-bottom:12px;">${escapeHTML(p.description || 'Dedicated workspace project.')}</p>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-primary" onclick="window.selectProjectWorkspace('${p.project_id}')">Open Workspace</button>
                        <button class="btn btn-secondary" onclick="window.deleteProject('${p.project_id}')">Delete</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        } catch (e) {
            console.error('Error fetching projects:', e);
        }
    };

    window.selectProjectWorkspace = function (projectId) {
        currentProjectId = projectId;
        window.switchView('chatView');
        window.showToast('Workspace Filtered', 'Switched to project workspace.', 'info');
    };

    window.submitNewProject = async function () {
        const name = (document.getElementById('newProjectName').value || '').trim();
        const desc = (document.getElementById('newProjectDescription').value || '').trim();
        const inst = (document.getElementById('newProjectInstructions').value || '').trim();

        if (!name) return;
        const res = await window.apiFetch(`${API_BASE}/api/projects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, description: desc, instructions: inst }),
        });
        if (res.ok) {
            window.closeNewProjectModal();
            window.fetchProjects();
            window.showToast('Project Created', `Project '${name}' online.`, 'success');
        }
    };

    window.deleteProject = async function (projectId) {
        if (!confirm('Are you sure you want to delete this project?')) return;
        await window.apiFetch(`${API_BASE}/api/projects/${projectId}`, { method: 'DELETE' });
        if (currentProjectId === projectId) currentProjectId = null;
        window.fetchProjects();
    };

    // ── ARTIFACTS CENTER ──
    window.fetchArtifacts = async function () {
        const grid = document.getElementById('artifactsGrid');
        if (!grid) return;
        try {
            const res = await window.apiFetch(`${API_BASE}/api/artifacts`);
            if (!res.ok) return;
            const data = await res.json();
            const artifacts = data.artifacts || [];

            grid.innerHTML = '';
            if (artifacts.length === 0) {
                grid.innerHTML = '<div class="sidebar-empty-state">No artifacts recorded in the provenance ledger yet.</div>';
                return;
            }

            artifacts.forEach(a => {
                const card = document.createElement('div');
                card.className = 'connector-card';
                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <h3 style="color:#fff; font-family:var(--font-heading); font-size:0.95rem;">📄 ${escapeHTML(a.filename)}</h3>
                        <span class="os-badge" style="color:var(--accent-green);">${a.verification_status}</span>
                    </div>
                    <div style="font-family:var(--font-code); font-size:0.7rem; color:var(--text-muted); margin-bottom:10px;">
                        <div>Type: ${a.mime_type || 'Document'}</div>
                        <div>Task: ${a.task_id || 'Direct'}</div>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-primary" onclick="window.openArtifactPreview('${a.artifact_id}')">Preview</button>
                        <a href="/api/artifacts/${a.artifact_id}/download" class="btn btn-secondary" download style="text-decoration:none;">Download</a>
                    </div>
                `;
                grid.appendChild(card);
            });
        } catch (e) {
            console.error('Error fetching artifacts:', e);
        }
    };

    window.openArtifactPreview = async function (artifactId) {
        const modal = document.getElementById('artifactPreviewModal');
        const bodyEl = document.getElementById('previewArtifactBody');
        const titleEl = document.getElementById('previewArtifactTitle');
        const downloadBtn = document.getElementById('previewDownloadBtn');

        if (!modal || !bodyEl) return;
        modal.style.display = 'flex';
        bodyEl.innerHTML = '<div class="sidebar-empty-state">Loading artifact content...</div>';

        try {
            const res = await window.apiFetch(`${API_BASE}/api/artifacts/${artifactId}/preview`);
            if (res.ok) {
                const d = await res.json();
                if (titleEl) titleEl.textContent = `Artifact Preview: ${d.filename}`;
                if (downloadBtn) downloadBtn.href = `/api/artifacts/${artifactId}/download`;
                if (d.is_text) {
                    bodyEl.innerHTML = `<pre><code>${escapeHTML(d.content)}</code></pre>`;
                } else {
                    bodyEl.innerHTML = `<div style="text-align:center; padding:20px;"><p>Binary File (${d.mime_type})</p></div>`;
                }
            }
        } catch (e) {
            bodyEl.innerHTML = `<div class="toast error">Error loading preview: ${e}</div>`;
        }
    };

    // ── AUTOMATIONS ──
    window.fetchAutomations = async function () {
        const grid = document.getElementById('automationsGrid');
        if (!grid) return;
        try {
            const res = await window.apiFetch(`${API_BASE}/api/automations`);
            if (!res.ok) return;
            const data = await res.json();
            const automations = data.automations || [];

            grid.innerHTML = '';
            if (automations.length === 0) {
                grid.innerHTML = '<div class="sidebar-empty-state">No scheduled automations registered.</div>';
                return;
            }

            automations.forEach(r => {
                const card = document.createElement('div');
                card.className = 'connector-card';
                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <h3 style="color:#fff; font-family:var(--font-heading);">${escapeHTML(r.name || r.goal)}</h3>
                        <span class="os-badge" style="color:${r.enabled ? 'var(--accent-green)' : 'var(--text-muted)'};">${r.enabled ? 'ENABLED' : 'DISABLED'}</span>
                    </div>
                    <p style="color:var(--text-secondary); font-size:0.82rem; margin-bottom:10px;">${escapeHTML(r.goal || '')}</p>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-primary" onclick="window.runAutomationNow('${r.routine_id}')">Run Now ▸</button>
                        <button class="btn btn-secondary" onclick="window.toggleAutomation('${r.routine_id}', ${!r.enabled})">${r.enabled ? 'Disable' : 'Enable'}</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        } catch (e) {
            console.error('Error fetching automations:', e);
        }
    };

    window.runAutomationNow = async function (routineId) {
        await window.apiFetch(`${API_BASE}/api/automations/${routineId}/run`, { method: 'POST' });
        window.showToast('Triggered', 'Automation launched.', 'success');
    };

    window.toggleAutomation = async function (routineId, enabled) {
        await window.apiFetch(`${API_BASE}/api/automations/${routineId}/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: enabled }),
        });
        window.fetchAutomations();
    };

    // ── CONTEXT PANEL TAB FETCHERS ──
    window.fetchTabArtifacts = async function () {
        const container = document.getElementById('tabArtifactsList');
        if (!container || !currentConversationId) return;
        try {
            const res = await window.apiFetch(`${API_BASE}/api/artifacts?conversation_id=${currentConversationId}`);
            if (!res.ok) return;
            const data = await res.json();
            const artifacts = data.artifacts || [];

            const countEl = document.getElementById('tabArtifactsCount');
            if (countEl) countEl.textContent = artifacts.length;

            container.innerHTML = '';
            if (artifacts.length === 0) {
                container.innerHTML = '<div class="sidebar-empty-state">No artifacts generated in this conversation yet.</div>';
                return;
            }

            artifacts.forEach(a => {
                const item = document.createElement('div');
                item.className = 'task-step-item';
                item.innerHTML = `
                    <span>📄 ${escapeHTML(a.filename)}</span>
                    <button class="btn-sm" onclick="window.openArtifactPreview('${a.artifact_id}')">View</button>
                `;
                container.appendChild(item);
            });
        } catch (e) {
            console.debug('Error fetching tab artifacts:', e);
        }
    };

    window.fetchTabFiles = async function () {
        const container = document.getElementById('tabFilesList');
        if (!container || !currentProjectId) return;
        try {
            const res = await window.apiFetch(`${API_BASE}/api/projects/${currentProjectId}/files`);
            if (!res.ok) return;
            const data = await res.json();
            const files = data.files || [];

            container.innerHTML = '';
            if (files.length === 0) {
                container.innerHTML = '<div class="sidebar-empty-state">No files attached to current project.</div>';
                return;
            }

            files.forEach(f => {
                const item = document.createElement('div');
                item.className = 'task-step-item';
                item.innerHTML = `<span>📁 ${escapeHTML(f.filename)}</span><span class="os-badge">${f.status}</span>`;
                container.appendChild(item);
            });
        } catch (e) {
            console.debug('Error fetching tab files:', e);
        }
    };

    window.fetchMemories = async function () {
        const container = document.getElementById('tabMemoriesList');
        const grid = document.getElementById('memoriesGrid');
        try {
            const res = await window.apiFetch(`${API_BASE}/api/memory`);
            if (!res.ok) return;
            const data = await res.json();
            const memories = data.memories || [];

            if (container) {
                container.innerHTML = '';
                if (memories.length === 0) {
                    container.innerHTML = '<div class="sidebar-empty-state">No persistent memory entries recorded.</div>';
                } else {
                    memories.slice(0, 8).forEach(m => {
                        const item = document.createElement('div');
                        item.className = 'task-step-item';
                        item.innerHTML = `<span>🧠 <strong>${escapeHTML(m.name)}</strong>: ${escapeHTML(m.content || m.description)}</span>`;
                        container.appendChild(item);
                    });
                }
            }

            if (grid) {
                grid.innerHTML = '';
                memories.forEach(m => {
                    const card = document.createElement('div');
                    card.className = 'connector-card';
                    card.innerHTML = `
                        <h3 style="color:#fff; font-family:var(--font-heading); margin-bottom:6px;">🧠 ${escapeHTML(m.name)}</h3>
                        <p style="color:var(--text-secondary); font-size:0.82rem; margin-bottom:8px;">${escapeHTML(m.content || m.description)}</p>
                        <span class="os-badge">${m.scope || 'user'}</span>
                    `;
                    grid.appendChild(card);
                });
            }
        } catch (e) {
            console.debug('Error fetching memories:', e);
        }
    };

    // ── CAREER OS STUDIO ──
    window.loadCareerProfile = async function () {
        const snapshot = document.getElementById('careerResumeSnapshot');
        if (!snapshot) return;
        try {
            const res = await window.apiFetch(`${API_BASE}/api/career/profile`);
            if (!res.ok) throw new Error(`Profile request failed (${res.status})`);
            const data = await res.json();
            const profile = data.profile || {};
            const validation = data.validation || {};
            const contact = profile.contact || {};
            const preferences = profile.preferences || {};
            const skills = (profile.skills || []).reduce((total, group) => total + (group.skills || []).length, 0);

            const setText = (id, value) => {
                const el = document.getElementById(id);
                if (el) el.textContent = value || '—';
            };
            setText('careerSnapshotName', contact.full_name || 'Career Profile');
            setText('careerSnapshotSummary', profile.summary || 'Resume-backed profile ready for tailoring and ATS analysis.');
            setText('careerSnapshotExperience', (profile.experience || []).length);
            setText('careerSnapshotProjects', (profile.projects || []).length);
            setText('careerSnapshotSkills', skills);

            const meta = document.getElementById('careerSnapshotMeta');
            if (meta) {
                const roles = (preferences.target_roles || []).slice(0, 4);
                const chips = [contact.location, contact.email, ...roles].filter(Boolean);
                meta.innerHTML = chips.map(item => `<span>${escapeHTML(item)}</span>`).join('');
            }
            const badge = document.getElementById('careerProfileCompletenessBadge');
            const score = validation.completeness_score ?? validation.score;
            if (badge && score !== undefined) {
                badge.classList.add('resume-synced');
                setText('careerCompletenessScore', `${score}%`);
            }
            const json = document.getElementById('canonicalProfileJson');
            if (json) json.textContent = JSON.stringify(profile, null, 2);
        } catch (error) {
            console.debug('Career profile load error:', error);
            const summary = document.getElementById('careerSnapshotSummary');
            if (summary) summary.textContent = 'Resume profile is available locally; refresh the workspace connection to load live validation.';
        }
    };

    window.switchCareerTab = function (tabId) {
        document.querySelectorAll('.career-subtab').forEach(t => t.style.display = 'none');
        document.querySelectorAll('#careerTabPills .filter-pill').forEach(p => p.classList.remove('active'));

        const target = document.getElementById(tabId);
        if (target) target.style.display = 'block';

        const pills = document.querySelectorAll('#careerTabPills .filter-pill');
        pills.forEach(p => {
            if (p.getAttribute('onclick') && p.getAttribute('onclick').includes(tabId)) {
                p.classList.add('active');
            }
        });

        if (tabId === 'pipelineTab') window.loadCareerApplications();
        if (tabId === 'jobsTab') window.executeJobSearch();
        if (tabId === 'profileTab') window.loadCareerProfile();
    };

    window.executeJobSearch = async function () {
        const list = document.getElementById('careerJobsList');
        if (!list) return;
        const q = (document.getElementById('careerJobSearchInput')?.value || 'AI Engineer').trim();
        list.innerHTML = '<div class="sidebar-empty-state">Searching verified jobs across Ashby, Lever, Greenhouse...</div>';

        try {
            const res = await window.apiFetch(`${API_BASE}/api/career/jobs/search?query=${encodeURIComponent(q)}`);
            if (!res.ok) return;
            const data = await res.json();
            const jobs = data.matches || [];

            list.innerHTML = '';
            if (jobs.length === 0) {
                list.innerHTML = '<div class="sidebar-empty-state">No job openings found matching query.</div>';
                return;
            }

            jobs.slice(0, 12).forEach(j => {
                const card = document.createElement('div');
                card.className = 'connector-card';
                card.innerHTML = `
                    <h3 style="color:#fff; font-family:var(--font-heading); margin-bottom:4px;">${escapeHTML(j.title)}</h3>
                    <div style="color:var(--accent-cyan); font-weight:600; font-size:0.85rem; margin-bottom:8px;">${escapeHTML(j.company)}</div>
                    <div style="font-family:var(--font-code); font-size:0.7rem; color:var(--text-muted); margin-bottom:12px;">${escapeHTML(j.location || 'Remote')}</div>
                `;
                list.appendChild(card);
            });
        } catch (e) {
            list.innerHTML = '<div class="sidebar-empty-state">Error querying job finder.</div>';
        }
    };

    window.generateResumeArtifacts = async function () {
        const role = (document.getElementById('resumeTargetRoleInput')?.value || 'AI Architect').trim();
        const theme = document.getElementById('resumeTemplateSelector')?.value || 'ats_classic';
        window.showToast('Rendering Resume', `Generating 10-Theme Artifacts for '${role}'...`, 'info');

        try {
            const res = await window.apiFetch(`${API_BASE}/api/career/resumes/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_role: role, template_id: theme }),
            });
            if (res.ok) {
                window.showToast('Resume Exported', 'DOCX, PDF & Markdown generated.', 'success');
                window.fetchArtifacts();
            }
        } catch (e) {
            window.showToast('Export Error', String(e), 'error');
        }
    };

    window.runAtsAudit = async function () {
        const role = (document.getElementById('resumeTargetRoleInput')?.value || 'AI Architect').trim();
        try {
            const res = await window.apiFetch(`${API_BASE}/api/career/ats/score`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_role: role }),
            });
            if (res.ok) {
                const d = await res.json();
                const score = d.overall_score ?? 0;
                const scoreEl = document.getElementById('atsOverallScoreDisplay');
                if (scoreEl) scoreEl.textContent = `${score}%`;
                window.showToast('ATS Audit', `Compatibility score: ${score}%`, 'success');
            }
        } catch (e) {
            console.debug('ATS audit error:', e);
        }
    };

    window.loadCareerApplications = async function () {
        const grid = document.getElementById('pipelineApplicationsGrid');
        if (!grid) return;
        try {
            const res = await window.apiFetch(`${API_BASE}/api/career/applications`);
            if (!res.ok) return;
            const data = await res.json();
            const apps = data.applications || [];

            grid.innerHTML = '';
            if (apps.length === 0) {
                grid.innerHTML = '<div class="sidebar-empty-state">No CRM application records found.</div>';
                return;
            }

            apps.forEach(a => {
                const card = document.createElement('div');
                card.className = 'connector-card';
                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <h3 style="color:#fff; font-family:var(--font-heading);">${escapeHTML(a.company || a.company_name)}</h3>
                        <span class="os-badge">${a.status || a.application_status}</span>
                    </div>
                    <div style="color:var(--text-secondary); font-size:0.82rem;">${escapeHTML(a.job_title)}</div>
                `;
                grid.appendChild(card);
            });
        } catch (e) {
            console.debug('Error loading CRM:', e);
        }
    };

    window.syncExcelTracker = async function () {
        window.showToast('Syncing Excel', 'Projecting SQLite DB to BR_JARVIS_Career_Tracker.xlsx...', 'info');
        try {
            const res = await window.apiFetch(`${API_BASE}/api/career/spreadsheet/sync`, { method: 'POST' });
            if (res.ok) {
                window.showToast('Excel Synced', '10-Sheet Workbook projected.', 'success');
            }
        } catch (e) {
            window.showToast('Sync Error', String(e), 'error');
        }
    };

    function fetchConnectorStatus() {
        window.apiFetch(`${API_BASE}/api/connectors`)
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (!data || !data.connectors) return;
                const panel = document.getElementById('connectorPanel');
                if (!panel) return;
                panel.innerHTML = '';
                data.connectors.forEach(c => {
                    const badge = document.createElement('div');
                    badge.className = `connector-badge ${c.configured ? 'active' : ''}`;
                    badge.innerHTML = `<span>${c.icon || '🔌'}</span><span>${escapeHTML(c.name)}</span>`;
                    badge.onclick = () => window.switchView('connectorsView');
                    panel.appendChild(badge);
                });
            })
                        .catch(err => {
                const panel = document.getElementById('connectorPanel');
                if (panel) panel.innerHTML = `<div class="sidebar-empty-state">Connector status unavailable: ${escapeHTML(String(err))}</div>`;
            });
    }

    window.fetchConnectors = function () {
        const grid = document.getElementById('connectorsGrid');
        if (!grid) return;
        window.apiFetch(`${API_BASE}/api/connectors`)
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (!data || !data.connectors) return;
                grid.innerHTML = '';
                data.connectors.forEach(c => {
                    const card = document.createElement('div');
                    card.className = 'connector-card';
                    card.innerHTML = `
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <h3 style="color:#fff; font-family:var(--font-heading);">${c.icon || '🔌'} ${escapeHTML(c.name)}</h3>
                            <span class="os-badge" style="color:${c.configured ? 'var(--accent-green)' : 'var(--text-muted)'};">${c.configured ? 'CONNECTED' : 'STANDBY'}</span>
                        </div>
                        <p style="color:var(--text-secondary); font-size:0.82rem;">${escapeHTML(c.description || 'Modular connector plugin.')}</p>
                    `;
                    grid.appendChild(card);
                });
            })
                        .catch(err => {
                grid.innerHTML = `<div class="sidebar-empty-state">Connector data unavailable: ${escapeHTML(String(err))}</div>`;
            });
    };

    window.fetchContacts = function () {
        const grid = document.getElementById('contactsGrid');
        if (!grid) return;
        window.apiFetch(`${API_BASE}/api/contacts`)
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (!data || !data.contacts) return;
                grid.innerHTML = '';
                data.contacts.forEach(c => {
                    const card = document.createElement('div');
                    card.className = 'connector-card';
                    card.innerHTML = `
                        <h3 style="color:#fff; font-family:var(--font-heading); margin-bottom:4px;">👤 ${escapeHTML(c.name)}</h3>
                        <div style="color:var(--accent-cyan); font-size:0.8rem; font-family:var(--font-code);">${escapeHTML(c.phone_number || c.email || '')}</div>
                    `;
                    grid.appendChild(card);
                });
            })
                        .catch(err => {
                grid.innerHTML = `<div class="sidebar-empty-state">Contact data unavailable: ${escapeHTML(String(err))}</div>`;
            });
    };

    window.useSkillInChat = function (command) {
        window.switchView('chatView');
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.value = `${command} `;
            chatInput.focus();
        }
    };

    let _allLoadedSkills = [];

    function renderSkillsGrid(skills) {
        const grid = document.getElementById('skillsGrid');
        if (!grid) return;
        grid.innerHTML = '';
        if (!skills || skills.length === 0) {
            grid.innerHTML = '<div class="sidebar-empty-state">No matching skills found.</div>';
            return;
        }

        skills.forEach(s => {
            const card = document.createElement('div');
            card.className = 'connector-card';
            const cmd = s.command || (s.triggers && s.triggers.length ? s.triggers[0] : `/${s.name}`);
            const triggersStr = (s.triggers && s.triggers.length) ? s.triggers.join(', ') : cmd;
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <h3 style="color:#fff; font-family:var(--font-heading); font-size:0.95rem;">⚡ ${escapeHTML(s.name || s.id)}</h3>
                    <span class="os-badge">${escapeHTML(cmd)}</span>
                </div>
                <p style="color:var(--text-secondary); font-size:0.8rem; margin-bottom:10px; line-height:1.4;">${escapeHTML(s.description || 'Built-in automation capability.')}</p>
                <div style="font-family:var(--font-code); font-size:0.68rem; color:var(--text-muted); margin-bottom:12px;">Triggers: ${escapeHTML(triggersStr)}</div>
                <button class="btn btn-secondary" onclick="window.useSkillInChat('${escapeHTML(cmd)}')">Run in Chat ▸</button>
            `;
            grid.appendChild(card);
        });
    }

    window.fetchSkills = function () {
        const grid = document.getElementById('skillsGrid');
        if (!grid) return;
        grid.innerHTML = '<div class="sidebar-empty-state">Loading skills catalog...</div>';
        window.apiFetch(`${API_BASE}/api/skills`)
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (!data) {
                    grid.innerHTML = '<div class="sidebar-empty-state">No skills available.</div>';
                    return;
                }
                _allLoadedSkills = Array.isArray(data) ? data : (data.skills || []);
                renderSkillsGrid(_allLoadedSkills);
            })
            .catch(err => {
                grid.innerHTML = `<div class="sidebar-empty-state">Error loading skills: ${escapeHTML(String(err))}</div>`;
            });
    };

    // Wire live skill search filter
    document.addEventListener('DOMContentLoaded', () => {
        const skillSearchInput = document.getElementById('skillSearchInput');
        if (skillSearchInput) {
            skillSearchInput.addEventListener('input', debounce(() => {
                const q = (skillSearchInput.value || '').trim().toLowerCase();
                if (!q) {
                    renderSkillsGrid(_allLoadedSkills);
                } else {
                    const filtered = _allLoadedSkills.filter(s => {
                        const name = (s.name || '').toLowerCase();
                        const desc = (s.description || '').toLowerCase();
                        const cmd = (s.command || '').toLowerCase();
                        const trigs = (s.triggers || []).join(' ').toLowerCase();
                        return name.includes(q) || desc.includes(q) || cmd.includes(q) || trigs.includes(q);
                    });
                    renderSkillsGrid(filtered);
                }
            }, 150));
        }
    });

})(window, document);
