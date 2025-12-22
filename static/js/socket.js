//User ID'sini alma fonksiyonu
function getUserId() {
    let attr = document.body.getAttribute('data-current-user-id');
    
    if (!attr) {
        const hiddenDiv = document.getElementById('current-user-data');
        if (hiddenDiv) attr = hiddenDiv.getAttribute('data-user-id');
    }

    const parsed = parseInt(attr);
    
    if (!attr || attr === "None" || attr === "null" || isNaN(parsed) || parsed === 0) {
        return null; 
    }
    return parsed;
}

const current_user_id = getUserId();
console.log("✅ Sistem Aktif ID:", current_user_id);

let currentChatUserId = null; 
let ws = null;

const ws_protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const ws_url = current_user_id ? `${ws_protocol}//${window.location.host}/messages/ws/${current_user_id}` : null;


// WebSocket bağlantısını başlatma fonksiyonu
function initWebSocket() {
    if (!current_user_id || (ws && ws.readyState === WebSocket.OPEN)) return;

    console.log("🔌 WS Bağlanıyor:", ws_url);
    ws = new WebSocket(ws_url);
    
    ws.onopen = function(e) {
        console.log("🟢 [WS Open] Bağlantı kuruldu.");
    };

    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'new_message') {
                if (parseInt(data.sender_id) !== current_user_id) { 
                    if (currentChatUserId && parseInt(data.sender_id) === parseInt(currentChatUserId)) {
                        appendMessage(data.content, 'theirs'); 
                    } else {
                        console.log("📩 Yeni mesaj geldi.");
                    }
                }
            }
            
            if (data.type === 'new_notification') {
                console.log("🔔 Yeni bildirim!");
                showNotificationBadge(); 
            }

        } catch (e) {
            console.warn("WS Veri Hatası: " + e);
        }
    };

    ws.onclose = function(event) {
        console.log(`🔴 [WS Close] Bağlantı kapandı. Kod: ${event.code}`);
        ws = null;
        setTimeout(initWebSocket, 3000);
    };
}

// Mesaj gönderme fonksiyonu
function sendMessage() {
    const input = document.getElementById('message-input');
    if (!input) return;

    const content = input.value.trim();
    
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        initWebSocket();
        return;
    }
    
    if (!content || !currentChatUserId) return;
    
    const messagePayload = {
        receiver_id: parseInt(currentChatUserId),
        content: content
    };
    
    try {
        ws.send(JSON.stringify(messagePayload)); 
        appendMessage(content, 'mine'); 
        input.value = ''; 
    } catch (e) {
        console.error("Mesaj gönderilemedi:", e);
    }
}

// Mesaj balonunu ekleme fonksiyonu
function appendMessage(content, type) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-bubble message-${type}`;
    messageDiv.textContent = content;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight; 
}

// Sohbet geçmişini yükleme fonksiyonu
async function loadChatHistory(targetUserId) {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '<p style="text-align:center; padding: 20px;">Geçmiş yükleniyor...</p>';
    
    if (!current_user_id) return;

    try {
        const response = await fetch(`/messages/history/${targetUserId}?current_user_id=${current_user_id}`);
        if (!response.ok) throw new Error("Geçmiş yüklenemedi.");
        
        const history = await response.json();
        chatMessages.innerHTML = '';
        
        history.forEach(msg => {
            const type = msg.is_mine ? 'mine' : 'theirs'; 
            appendMessage(msg.content, type); 
        });

    } catch (e) {
        console.error(e);
        chatMessages.innerHTML = '<p style="color:red; text-align:center;">Mesaj geçmişi yüklenemedi.</p>';
    }
}

// Mesaj kullanıcı listesini yükleme fonksiyonu
const loadMessageUsers = async () => {
    const contentDiv = document.querySelector('#messages-panel .message-user-list-content');
    const searchInput = document.getElementById('message-search');
    
    if (searchInput && searchInput.value.trim() !== '') return;
    if (!contentDiv) return;
    
    contentDiv.innerHTML = '<p style="text-align:center; margin-top:20px; color:#666;">Kişiler yükleniyor...</p>';
    
    if (!current_user_id) {
        contentDiv.innerHTML = '<p style="text-align:center; padding:20px;">Lütfen giriş yapın.</p>';
        return;
    }

    try {
        const response = await fetch(`/messages/users/list?current_user_id=${current_user_id}`); 
        if(!response.ok) throw new Error("Veri alınamadı");

        const users = await response.json();
        const filteredUsers = users.filter(user => parseInt(user.id) !== current_user_id);
        
        if (filteredUsers.length === 0) {
            contentDiv.innerHTML = '<p style="text-align:center; padding: 20px;">Henüz sohbet yok.</p>';
            return;
        }
        
        contentDiv.innerHTML = filteredUsers.map(user => createListItem(user)).join('');

    } catch (error) {
        contentDiv.innerHTML = `<p style="color:red; text-align:center;">Liste hatası.</p>`;
    }
};

// Sohbet penceresini açma fonksiyonu
function openChatWindow(targetUserId, username, avatarUrl = null) {
    const messagesPanel = document.getElementById('messages-panel');
    const chatWindow = document.getElementById('chat-window');
    const chatUserName = document.getElementById('chat-user-name');
    const chatUserAvatar = document.getElementById('chat-user-avatar');
    
    currentChatUserId = targetUserId;
    
    chatUserName.textContent = username; 
    chatUserAvatar.src = avatarUrl || getUserAvatar(null);
    
    messagesPanel.classList.add('chat-active');
    chatWindow.style.display = 'flex';
    
    loadChatHistory(targetUserId);
    
    setTimeout(() => {
        const input = document.getElementById('message-input');
        if (input) input.focus();
    }, 100);
}

// Bildirim panelini yükleme fonksiyonu
async function loadNotifications() {
    const container = document.querySelector('#notification-panel .notification-content');
    if (!container) return;
    try {
        const res = await fetch('/notifications/');
        const notifs = await res.json();
        
        if (notifs.length === 0) {
            container.innerHTML = '<p>Bildirim yok.</p>';
            return;
        }

        container.innerHTML = notifs.map(n => {
            let text = '';
            let isDeleted = false;
            
            if (n.verb === 'liked') {
                text = 'pinini beğendi.';
            } else if (n.verb === 'commented') {
                text = 'yorum yaptı.';
            } else if (n.verb && n.verb.startsWith('deleted_')) {
                const reasonKey = n.verb.split('_')[1]; 
                const reasonsTR = {
                    'spam': 'Spam veya Yanıltıcı İçerik',
                    'harmful': 'Zararlı İçerik',
                    'copyright': 'Telif Hakkı İhlali',
                    'violence': 'Şiddet veya Nefret Söylemi',
                    'inappropriate': 'Uygunsuz İçerik',
                    'other': 'Topluluk Kuralları İhlali',
                    'admin': 'Yönetici tarafından kaldırıldı'
                };
                const reasonText = reasonsTR[reasonKey] || 'Kurallar İhlali';
                text = `<span style="color:red;">pininizi kaldırdı.</span><br><span style="font-size:11px; color:#aaa;">Sebep: ${reasonText}</span>`;
                isDeleted = true;
            } else {
                text = 'bir işlem yaptı.';
            }

            // Tıklanma olayı (Silindiyse tıklanmasın)
            const clickAction = (n.pin_id && !isDeleted) ? `onclick="window.location.href='/?target_pin=${n.pin_id}'"` : '';
            const cursorStyle = (n.pin_id && !isDeleted) ? 'cursor:pointer;' : 'cursor:default;';

            return `
            <div class="notification-item" ${clickAction} style="display:flex; align-items:center; padding:15px; border-bottom:1px solid #333; ${cursorStyle}">
                <img src="/static/${n.actor_avatar || '/images/default_avatar.jpg'}" style="width:40px; height:40px; border-radius:50%; margin-right:10px; object-fit:cover;">
                <div>
                    <p style="margin:0; font-size:14px; color:white;">
                        <strong>${n.actor_username}</strong> ${text}
                    </p>
                    <p style="margin:0; font-size:11px; color:#888;">${new Date(n.created_at).toLocaleString()}</p>
                </div>
            </div>`;
        }).join('');
        
        const badge = document.getElementById('notification-icon').querySelector('.badge-dot');
        if(badge) badge.remove();
    } catch (e) { container.innerHTML = '<p>Hata.</p>'; }
}

// Kullanıcı avatar yolunu alma fonksiyonu
function getUserAvatar(userOrUrl) {
    let path = null;
    if (userOrUrl && typeof userOrUrl === 'string' && userOrUrl.trim() !== '') {
        path = userOrUrl;
    } else if (userOrUrl && typeof userOrUrl === 'object' && userOrUrl.profile_picture) {
        path = userOrUrl.profile_picture;
    }

    if (!path) return '/static/images/default_avatar.jpg';

    if (!path.startsWith('/static') && !path.startsWith('http')) {
        return `/static/${path}`;
    }
    return path;
}

// Kullanıcı liste öğesi oluşturma fonksiyonu
function createListItem(user, isSearch = false) {
    if (parseInt(user.id) === current_user_id) return ''; 

    const avatarUrl = getUserAvatar(user);

    return `
        <a href="javascript:void(0)" class="user-list-item" data-user-id="${user.id}" 
           onclick="openChatWindow(${user.id}, '${user.username}', '${avatarUrl}')">
            <img src="${avatarUrl}" class="user-avatar">
            <div class="user-info">
                <p class="user-name" style="font-weight: bold;">${user.username}</p>
            </div>
        </a>
    `;
}

// Kullanıcı arama işleme fonksiyonu
const handleUserSearch = async (event) => {
    const query = event.target.value.trim();
    const contentDiv = document.querySelector('#messages-panel .message-user-list-content');
    if (!contentDiv) return;

    if (query.length < 2) {
        loadMessageUsers();
        return;
    }

    contentDiv.innerHTML = '<p style="text-align:center; padding: 20px;">Aranıyor...</p>';

    try {
        const response = await fetch(`/messages/users/search?q=${encodeURIComponent(query)}`);
        const users = await response.json();
        const filteredUsers = users.filter(u => parseInt(u.id) !== current_user_id);

        if (filteredUsers.length === 0) {
            contentDiv.innerHTML = '<p style="text-align:center; padding: 20px;">Kullanıcı bulunamadı.</p>';
            return;
        }

        contentDiv.innerHTML = filteredUsers.map(user => createListItem(user, true)).join('');

    } catch (error) {
        contentDiv.innerHTML = '<p style="color: red; text-align:center; padding: 20px;">Hata oluştu.</p>';
    }
};

// Bildirim rozetini gösterme fonksiyonu
function showNotificationBadge() {
    const icon = document.getElementById('notification-icon');
    if(icon) {
        if(!icon.querySelector('.badge-dot')) {
            const badge = document.createElement('div');
            badge.className = 'badge-dot';
            badge.style.cssText = "position:absolute; top:5px; right:5px; width:10px; height:10px; background:red; border-radius:50%; border:2px solid white;";
            icon.style.position = "relative";
            icon.appendChild(badge);
        }
    }
}
