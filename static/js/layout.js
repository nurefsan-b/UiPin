
//masonry düzeni uygulama fonksiyonu
function applyMasonry() {
    const grid = document.querySelector('.pin-grid');
    if (!grid) return;
    const cards = Array.from(grid.querySelectorAll('.pin-card'));
    if (cards.length === 0) return;

    const style = getComputedStyle(grid);
    let columnCount = parseInt(style.getPropertyValue('--column-count')); 
    if (isNaN(columnCount) || columnCount < 1) columnCount = 4;

    const columnGap = 10;
    const containerWidth = grid.clientWidth;
    
    const cardWidth = (containerWidth - (columnCount - 1) * columnGap) / columnCount;
    const columnHeights = Array(columnCount).fill(0);
    
    cards.forEach(card => {
        card.style.width = `${cardWidth}px`;
        const minHeight = Math.min(...columnHeights);
        const minIndex = columnHeights.indexOf(minHeight);

        card.style.position = 'absolute';
        card.style.top = `${minHeight}px`;
        card.style.left = `${minIndex * (cardWidth + columnGap)}px`;
        
        columnHeights[minIndex] += card.offsetHeight + columnGap; 
    });
    
    grid.style.height = `${Math.max(...columnHeights)}px`;
}

// Sekme değiştirme fonksiyonu
function switchTab(event, tabId) {
    event.stopPropagation();
    const cardBack = event.target.closest('.pin-back');
    if (!cardBack) return;
    
    cardBack.querySelectorAll('.code-tab').forEach(t => t.classList.remove('active'));
    cardBack.querySelectorAll('.code-pane').forEach(p => p.classList.remove('active'));
    
    event.target.classList.add('active');
    const pane = cardBack.querySelector(`#${tabId}`);
    if (pane) pane.classList.add('active');
}

// Kartı döndürme fonksiyonu
function rotateCardBack(event, btn) {
    event.stopPropagation();
    const card = btn.closest('.pin-card');
    card.classList.remove('flipped');
    
    card.classList.remove('comments-open');
    const comments = card.querySelector('.comments-section');
    if(comments) comments.style.display = 'none';
    
    window.dispatchEvent(new Event('resize'));
}

// Yorum bölümünü açma/kapatma fonksiyonu
function toggleComments(event, pinId) {
    event.stopPropagation();
    const section = document.getElementById(`comments-section-${pinId}`);
    const card = section.closest('.pin-card');
    
    if (section.style.display === 'none') {
        section.style.display = 'flex';
        card.classList.add('comments-open'); 
    } else {
        section.style.display = 'none';
        card.classList.remove('comments-open'); 
    }
    applyMasonry();
}

// Profil sekmeleri arasında geçiş yapma fonksiyonu
function switchProfile(tabName) {
    var editSection = document.getElementById('editProfileSection');
    var pinsSection = document.getElementById('myPinsSection');
    
    if (editSection) editSection.style.display = 'none';
    if (pinsSection) pinsSection.style.display = 'none';

    var menuEdit = document.getElementById('menuEdit');
    var menuPins = document.getElementById('menuPins');

    if (menuEdit) menuEdit.classList.remove('active');
    if (menuPins) menuPins.classList.remove('active');

    if (tabName === 'edit') {
        if (editSection) editSection.style.display = 'block';
        if (menuEdit) menuEdit.classList.add('active');
    } 
    else if (tabName === 'pins') {
        if (pinsSection) pinsSection.style.display = 'block';
        if (menuPins) menuPins.classList.add('active');
        // Pinleri yükle (profile.html içinde loadMyPins tanımlı olmalı)
        if (typeof loadMyPins === 'function') {
            loadMyPins();
        }
    }
}

// Debounce fonksiyonu
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

//RUNPREVIEW

function runPreview(event, pinId) {
    event.stopPropagation(); 

    const cardBack = event.target.closest('.pin-back');
    cardBack.querySelectorAll('.code-tab').forEach(t => t.classList.remove('active'));
    cardBack.querySelectorAll('.code-pane').forEach(p => p.classList.remove('active'));

    event.target.classList.add('active');
    const previewPane = document.getElementById(`preview-pane-${pinId}`);
    if(previewPane) previewPane.classList.add('active');

    let htmlCode = "";
    let cssCode = "";
    let jsCode = "";
    let pythonCode = ""; 
    let sqlCode = "";    
    let hasBackendCode = false;

    const panes = cardBack.querySelectorAll('.code-pane[data-lang]');
    
    panes.forEach(pane => {
        const lang = pane.getAttribute('data-lang').toLowerCase();
        const code = pane.querySelector('pre code').innerText;

        if (lang === 'html') htmlCode = code;
        else if (lang === 'css') cssCode = code;
        else if (lang === 'javascript' || lang === 'js') jsCode = code;
        else if (lang === 'python') { pythonCode = code; hasBackendCode = true; }
        else if (lang === 'sql') { sqlCode = code; hasBackendCode = true; }
    });

    
    let finalSource = "";

    if (hasBackendCode && !htmlCode && !jsCode) {
        
        let terminalContent = "";
        if(pythonCode) terminalContent += `<div class="cmd"><span class="prompt">root@uipin:~/python#</span> cat script.py\n${pythonCode}</div>`;
        if(sqlCode) terminalContent += `<div class="cmd"><span class="prompt">root@uipin:~/sql#</span> cat query.sql\n${sqlCode}</div>`;

        finalSource = `
            <html>
            <head>
                <style>
                    body { background-color: #1e1e1e; color: #0f0; font-family: 'Courier New', monospace; padding: 20px; margin: 0; }
                    .terminal-box { border: 1px solid #333; padding: 20px; border-radius: 8px; background: #000; box-shadow: 0 0 20px rgba(0,255,0,0.1); }
                    .cmd { white-space: pre-wrap; margin-bottom: 20px; line-height: 1.4; }
                    .prompt { color: #e60023; font-weight: bold; margin-right: 10px; }
                    h3 { color: #fff; border-bottom: 1px solid #333; padding-bottom: 10px; }
                </style>
            </head>
            <body>
                <div class="terminal-box">
                    <h3>Backend Code Preview (Read-Only)</h3>
                    ${terminalContent}
                    <div class="cmd" style="color: #888; margin-top: 20px;">
                        // Not: Python ve SQL tarayıcıda doğrudan çalıştırılamaz.<br>
                        // Bu kodlar sunucu tarafında çalışmak üzere tasarlanmıştır.
                    </div>
                </div>
            </body>
            </html>
        `;
    } else {
        // --- SENARYO 2: Normal Web Önizlemesi (HTML/CSS/JS) ---
        finalSource = `
            <html>
                <head>
                    <style>
                        body { font-family: sans-serif; padding: 20px; margin: 0; }
                        ${cssCode}
                    </style>
                </head>
                <body>
                    ${htmlCode}
                    <script>
                        try {
                            ${jsCode}
                        } catch(e) { console.error(e); }
                    <\/script>
                </body>
            </html>
        `;
    }

    const iframe = document.getElementById(`iframe-${pinId}`);
    if(iframe) {
        iframe.srcdoc = finalSource;
    }
}

