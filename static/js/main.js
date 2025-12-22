document.addEventListener('DOMContentLoaded', () => {
    console.log("Masonry JS Yüklendi. Kullanıcı ID:", current_user_id);
    
    initWebSocket(); 
    loadMessageUsers(); 
    applyMasonry();
    window.addEventListener('resize', applyMasonry);
    setTimeout(applyMasonry, 1000);

    // Sidebar & Menüler
    const exploreContainer = document.getElementById('explore-dropdown-container');
    const exploreMenu = document.getElementById('explore-menu');
    let exploreTimeout;
    const createContainer = document.getElementById('create-dropdown-container');
    const createMenu = document.getElementById('create-menu');
    const boardLink = document.getElementById('open-create-board-modal');
    const boardModal = document.getElementById('create-board-modal-global');
    const closeBoardBtn = document.getElementById('close-board-modal-global');
    let createTimeout;

    const closeAllMenus = () => {
        if (exploreMenu) exploreMenu.style.display = 'none';
        if (createMenu) createMenu.style.display = 'none';
        clearTimeout(exploreTimeout);
        clearTimeout(createTimeout);
        
        const notifPanel = document.getElementById('notification-panel');
        if (notifPanel) notifPanel.classList.remove('active');
        
        const messagesPanel = document.getElementById('messages-panel');
        if (messagesPanel) {
            messagesPanel.classList.remove('active');
            messagesPanel.classList.remove('chat-active');
            const chatWindow = document.getElementById('chat-window');
            if (chatWindow) chatWindow.style.display = 'none';
        }
    };
    if (boardLink && boardModal) {
        boardLink.addEventListener('click', (e) => {
            e.preventDefault();
            if(createMenu) createMenu.style.display = 'none'; 
            boardModal.style.display = 'flex';
        });
        if(closeBoardBtn) {
            closeBoardBtn.addEventListener('click', () => { boardModal.style.display = 'none'; });
        }
        boardModal.addEventListener('click', (e) => {
            if (e.target === boardModal) { boardModal.style.display = 'none'; }
        });
    }
    if (exploreContainer && exploreMenu) {
        exploreMenu.style.display = 'none';
        exploreContainer.addEventListener('mouseenter', () => { closeAllMenus(); exploreMenu.style.display = 'block'; });
        exploreContainer.addEventListener('mouseleave', () => { exploreTimeout = setTimeout(() => { exploreMenu.style.display = 'none'; }, 100); });
    }
    if (createContainer && createMenu) {
        createMenu.style.display = 'none';
        createContainer.addEventListener('mouseenter', () => { closeAllMenus(); createMenu.style.display = 'block'; });
        createContainer.addEventListener('mouseleave', () => { createTimeout = setTimeout(() => { createMenu.style.display = 'none'; }, 100); });
    }

    // Paneller
    const notificationIcon = document.getElementById('notification-icon');
    const notificationPanel = document.getElementById('notification-panel');
    const closeNotificationButton = document.getElementById('close-notifications');
    const messageIcon = document.getElementById('messages-icon');
    const messagesPanel = document.getElementById('messages-panel');
    const closeMessagesButton = document.getElementById('close-messages');
    const backToListBtn = document.getElementById('back-to-list-btn');
    const chatWindow = document.getElementById('chat-window');

    if (notificationIcon && notificationPanel) {
        notificationIcon.addEventListener('click', (e) => {
            e.preventDefault();
            const isActive = notificationPanel.classList.contains('active');
            closeAllMenus();
            if (!isActive) {
                notificationPanel.classList.add('active');
                loadNotifications();
            }
        });
        if (closeNotificationButton) closeNotificationButton.addEventListener('click', () => notificationPanel.classList.remove('active'));
    }

    if (messageIcon && messagesPanel) {
        messageIcon.addEventListener('click', (e) => {
            e.preventDefault();
            const isActive = messagesPanel.classList.contains('active');
            closeAllMenus();
            if (!isActive) {
                messagesPanel.classList.add('active');
                messagesPanel.classList.remove('chat-active'); 
                if (chatWindow) chatWindow.style.display = 'none'; 
                loadMessageUsers(); 
            }
        });
        if (closeMessagesButton) closeMessagesButton.addEventListener('click', () => closeAllMenus());
    }
    
    if (backToListBtn && messagesPanel && chatWindow) {
        backToListBtn.addEventListener('click', () => {
            messagesPanel.classList.remove('chat-active');
            chatWindow.style.display = 'none';
            currentChatUserId = null; 
            const searchInput = document.getElementById('message-search');
            if (searchInput) searchInput.value = '';
            loadMessageUsers();
        });
    }

    // Arama Kutusu
    const searchInput = document.getElementById('message-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleUserSearch, 300));
        searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') e.preventDefault(); });
    }

    // Global Arama
    // GELİŞMİŞ ELASTICSEARCH ARAMASI 
    const globalSearchInput = document.getElementById('global-search-input');

    if (globalSearchInput) {
        globalSearchInput.addEventListener('input', debounce(async function(e) {
            const query = e.target.value.trim();
            const container = document.querySelector('.pin-grid') || document.getElementById('myPinsContainer');
            
            if (query.length === 0) {
                window.location.reload(); 
                return;
            }

            try {
                const res = await fetch(`/pins/search?q=${encodeURIComponent(query)}`);
                const results = await res.json();

                container.innerHTML = '';

                if (results.length === 0) {
                    container.innerHTML = '<p style="text-align:center; width:100%; color:#888;">Sonuç bulunamadı.</p>';
                    container.style.height = 'auto';
                    return;
                }

                results.forEach(pin => {
                    let imgPath = pin.image_path;
                    if (!imgPath.startsWith('/static') && !imgPath.startsWith('http')) {
                        imgPath = '/static/' + imgPath;
                    }

                    const div = document.createElement('div');
                    div.className = 'pin-card';
                    div.innerHTML = `
                        <div class="pin-inner" onclick="this.parentElement.classList.toggle('flipped')">
                            <div class="pin-front">
                                <img src="${imgPath}" class="pin-image">
                                <div class="pin-overlay">
                                    <div class="pin-title-info">${pin.title}</div>
                                </div>
                            </div>
                        </div>
                    `;
                    container.appendChild(div);
                });
                
                setTimeout(applyMasonry, 100);

            } catch (err) {
                console.error("Arama hatası:", err);
            }
        }, 300)); 
    }

    // Pin Oluşturma
    const openPinBtn = document.getElementById('open-create-pin-modal');
    const createPinModal = document.getElementById('create-pin-modal');
    const closePinBtn = document.getElementById('close-modal-btn');
    const createPinForm = document.getElementById('create-pin-form');
    const addCodeBtn = document.getElementById('add-code-btn');
    const codeContainer = document.getElementById('code-inputs-container');
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.getElementById('pin-file-input');
    const previewImage = document.getElementById('preview-image');
    const uploadPlaceholder = document.getElementById('upload-placeholder');

    if (openPinBtn && createPinModal) {
        openPinBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (createMenu) createMenu.style.display = 'none'; 
            createPinModal.style.display = 'flex';
        });
        closePinBtn.addEventListener('click', () => createPinModal.style.display = 'none');

        if (uploadArea && fileInput) {
            uploadArea.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', function() {
                const file = this.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        if (previewImage) { previewImage.src = e.target.result; previewImage.style.display = 'block'; }
                        if (uploadPlaceholder) uploadPlaceholder.style.display = 'none';
                    }
                    reader.readAsDataURL(file);
                }
            });
        }

        if (addCodeBtn && codeContainer) {
            addCodeBtn.addEventListener('click', (e) => {
                e.preventDefault(); 
                const div = document.createElement('div');
                div.className = "snippet-row";
                div.style.marginBottom = "10px";
                div.style.borderBottom = "1px solid #eee";
                div.style.paddingBottom = "5px";
                div.innerHTML = `
                    <div class="snippet-row-header" style="display:flex; justify-content:space-between; margin-bottom:5px;">
                        <select class="snippet-lang" style="padding:5px; border:1px solid #ddd; border-radius:4px;">
                            <option value="html">HTML</option>
                            <option value="css">CSS</option>
                            <option value="javascript">JavaScript</option>
                            <option value="python">Python</option>
                            <option value="sql">SQL</option>
                        </select>
                        <button type="button" onclick="this.parentElement.parentElement.remove()" style="color:red; border:none; background:none; cursor:pointer;">Sil &times;</button>
                    </div>
                    <textarea class="snippet-code" placeholder="Kod..." style="width:100%; height:80px; font-family:monospace; padding:5px; border:1px solid #ddd;"></textarea>
                `;
                codeContainer.appendChild(div);
            });
        }

        if (createPinForm) {
            createPinForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const snippets = [];
                if (codeContainer) {
                    const rows = codeContainer.querySelectorAll('.snippet-row');
                    rows.forEach(div => {
                        const langSelect = div.querySelector('.snippet-lang');
                        const codeText = div.querySelector('.snippet-code');
                        if (langSelect && codeText && codeText.value.trim()) {
                            snippets.push({ lang: langSelect.value, code: codeText.value });
                        }
                    });
                }
                const hiddenInput = document.getElementById('snippets-json-field');
                if (hiddenInput) hiddenInput.value = JSON.stringify(snippets);

                const formData = new FormData(createPinForm);
                try {
                    const res = await fetch('/pins/', { method: 'POST', body: formData });
                    if (res.ok) { alert('Pin başarıyla oluşturuldu!'); window.location.reload(); } 
                    else { const err = await res.json(); alert('Hata: ' + (err.detail || 'Bilinmeyen hata')); }
                } catch (err) { console.error(err); alert('Sunucu hatası.'); }
            });
        }
    }

    // Mesaj Gönderme
    const msgInput = document.getElementById('message-input');
    if (msgInput) {
        msgInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); sendMessage(); }
        });
    }
    const sendBtn = document.querySelector('.chat-input-area button');
    if (sendBtn) {
        sendBtn.addEventListener('click', (e) => { e.preventDefault(); sendMessage(); });
    }

    // Dışarı tıklama kontrolü
    document.addEventListener('click', (e) => {
        if (notificationPanel && notificationPanel.classList.contains('active')) {
            if (!notificationPanel.contains(e.target) && !notificationIcon.contains(e.target)) {
                notificationPanel.classList.remove('active');
            }
        }
        if (messagesPanel && messagesPanel.classList.contains('active')) {
            if (!messagesPanel.contains(e.target) && !messageIcon.contains(e.target) && !chatWindow.contains(e.target)) {
                closeAllMenus();
            }
        }
    });

    //BİLDİRİMDEN GELEN PİNİ AÇMA
    const urlParams = new URLSearchParams(window.location.search);
    const targetPinId = urlParams.get('target_pin');

    if (targetPinId) {
        console.log("🎯 Hedef Pin ID:", targetPinId);
        setTimeout(() => {
            const targetCard = document.getElementById(`pin-card-${targetPinId}`);
            if (targetCard) {
                targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                targetCard.classList.add('flipped');
                targetCard.style.transition = "box-shadow 0.5s";
                targetCard.style.boxShadow = "0 0 20px #e60023";
                setTimeout(() => { targetCard.style.boxShadow = "none"; }, 2000);
            }
        }, 1500); 
    }
});