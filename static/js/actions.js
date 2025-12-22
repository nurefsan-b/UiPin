
//pin silme fonksiyonu
//async function deletePin(pinId) {
//    if(!confirm("Bu pini silmek istediğine emin misin?")) return;
//    try {
//        const res = await fetch(`/pins/${pinId}`, { method: 'DELETE' }); // Düzeltildi
//        if(res.ok) {
//            // Kartı ekrandan sil
//            const card = document.getElementById(`pin-card-${pinId}`);
//            if(card) {
//                card.remove();
//                applyMasonry(); // Düzeni tazele
//            } else {
//                location.reload();
//            }
//        } else {
//            alert("Silinemedi!");
//        }
//    } catch(e) { alert("Hata oluştu."); }
//}

// Pin beğenme fonksiyonu
async function likePin(event, pinId) {
    event.stopPropagation();
    try {
        const res = await fetch(`/pins/${pinId}/like`, { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            const countSpan = document.getElementById(`like-count-${pinId}`);
            if(countSpan) countSpan.innerText = data.likes;
            
            const btn = event.currentTarget;
            const icon = btn.querySelector('i');
            
            if (data.liked) {
                icon.style.color = '#e60023'; 
                icon.classList.remove('far'); icon.classList.add('fas');
            } else {
                icon.style.color = ''; 
                icon.classList.remove('fas'); icon.classList.add('far');
            }
        }
    } catch (err) { console.error(err); }
}

// Yorum gönderme fonksiyonu
async function postComment(event, pinId) {
    event.stopPropagation();
    const input = document.getElementById(`comment-input-${pinId}`);
    const content = input.value;
    if (!content) return;
    
    const formData = new FormData();
    formData.append('content', content);
    try {
        const res = await fetch(`/pins/${pinId}/comment`, { method: 'POST', body: formData });
        if (res.ok) window.location.reload(); 
    } catch (err) { console.error(err); }
}

// Kaydetme modalını açma fonksiyonu
async function saveToBoard(boardId) {
    if (!currentPinToSave) return;
    const formData = new FormData();
    formData.append('pin_id', currentPinToSave);
    formData.append('board_id', boardId);

    try {
        const res = await fetch('/pins/save_to_board', { method: 'POST', body: formData });
        if (res.ok) {
            alert(`Başarıyla kaydedildi!`); 
            closeSaveModal();
        } else {
            alert("Kaydedilemedi.");
        }
    } catch (err) {
        console.error(err);
        alert("Sunucu hatası.");
    }
}

// Kaydetme modalını açma fonksiyonu
let currentPinToSave = null;

async function openSaveModal(pinId) {
    currentPinToSave = pinId;
    const modal = document.getElementById('select-board-modal');
    const container = document.getElementById('board-list-container');
    
    modal.style.display = 'flex';
    container.innerHTML = '<p style="text-align: center; color: #888;">Panolar yükleniyor...</p>';

    try {
        const res = await fetch('/boards/api/user_boards');
        if (!res.ok) throw new Error("Panolar alınamadı");
        
        const boards = await res.json();
        container.innerHTML = '';
        
        if (boards.length === 0) {
            container.innerHTML = '<p style="text-align: center;">Hiç panonuz yok.</p>';
        }

        boards.forEach(board => {
            const item = document.createElement('div');
            item.className = 'board-select-item';
            item.onclick = () => saveToBoard(board.id);
            const coverUrl = board.cover ? `/static/${board.cover}` : '/static/images/default_board.jpg';
            item.innerHTML = `
                <img src="${coverUrl}" class="board-mini-cover">
                <span class="board-select-name">${board.title}</span>
                <button class="btn-save-mini">Kaydet</button>
            `;
            container.appendChild(item);
        });

    } catch (err) {
        console.error(err);
        container.innerHTML = '<p style="color:red; text-align: center;">Hata oluştu.</p>';
    }
}
// Kaydetme modalını kapatma fonksiyonu
function closeSaveModal() {
    document.getElementById('select-board-modal').style.display = 'none';
    currentPinToSave = null;
}

//report gönderme fonksiyonu
async function submitReport(event) {
    event.preventDefault(); // Sayfanın yenilenmesini engelle
    
    const form = document.getElementById('report-form');
    const formData = new FormData(form);
    const pinId = document.getElementById('report-pin-id').value;
    
    try {
        const res = await fetch(`/pins/${pinId}/report`, {
            method: 'POST',
            body: formData
        });
        
        const data = await res.json();
        alert(data.message); // Örn: "Raporunuz iletildi"
        
        closeReportModal();
        form.reset(); // Formu temizle
        
    } catch (e) {
        console.error(e);
        alert("Rapor gönderilirken bir hata oluştu.");
    }
}

// Rapor modalını açma fonksiyonu
function openReportModal(pinId) {
    // 1. Hidden input'a pin ID'yi yaz
    const input = document.getElementById('report-pin-id');
    if (input) {
        input.value = pinId;
    } else {
        console.error("HATA: report-pin-id inputu bulunamadı! Base.html'de modal ekli mi?");
        return;
    }
    
    // 2. Modalı göster
    const modal = document.getElementById('report-modal');
    if (modal) {
        modal.style.display = 'flex';
    } else {
        console.error("HATA: report-modal bulunamadı!");
    }
}

function closeReportModal() {
    const modal = document.getElementById('report-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Raporu çözme fonksiyonu (admin paneli için)
 async function resolveReport(reportId, action) {
            if(action === 'delete_pin' && !confirm("Bu pini silmek istediğine emin misin?")) return;
            
            const formData = new FormData();
            formData.append('action', action);
            
            const res = await fetch(`/admin/reports/${reportId}/resolve`, {
                method: 'POST',
                body: formData
            });
            
            if(res.ok) window.location.reload();
            else alert("İşlem başarısız.");
        }

// Öğeyi silme fonksiyonu (admin paneli için)
 async function deleteItem(url) {
            if(!confirm("Emin misiniz? Bu işlem geri alınamaz.")) return;
            
            try {
                const res = await fetch(url, {method: 'POST'});
                if(res.ok) {
                    window.location.reload();
                } else {
                    alert("İşlem başarısız oldu.");
                }
            } catch (error) {
                console.error("Hata:", error);
                alert("Sunucu hatası.");
            }
        }


// LOGIN/REGISTER işlemleri için yardımcı fonksiyonlar
function parseErrorMessage(result, defaultMsg) {
            if (typeof result.detail === 'string') return result.detail;
            if (Array.isArray(result.detail) && result.detail.length > 0) return result.detail[0].msg;
            if (result.detail && typeof result.detail === 'object') return "Girdiğiniz bilgileri kontrol ediniz.";
            return defaultMsg;
        }

        function showLogin() {
            document.getElementById('register-container').classList.add('hidden');
            document.getElementById('login-container').classList.remove('hidden');
        }
        function showRegister() {
            document.getElementById('login-container').classList.add('hidden');
            document.getElementById('register-container').classList.remove('hidden');
        }

        // LOGIN İŞLEMİ
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const errorDiv = document.getElementById('loginErrorMsg');
            errorDiv.style.display = 'none';

            try {
                // Not: Endpoint'in Python'daki router prefix'ine göre '/users/login' veya '/login' olabilir.
                // Senin dosya yapında genelde '/users/login' kullanılır.
                const response = await fetch('/users/login', { method: 'POST', body: formData });
                if (response.ok) {
                    window.location.href = "/profile"; 
                } else {
                    const result = await response.json();
                    errorDiv.querySelector('span').textContent = parseErrorMessage(result, "Giriş başarısız.");
                    errorDiv.style.display = 'flex';
                }
            } catch (err) {
                errorDiv.querySelector('span').textContent = "Sunucu hatası.";
                errorDiv.style.display = 'flex';
            }
        });

        // REGISTER İŞLEMİ
        document.getElementById('registerForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const errorDiv = document.getElementById('registerErrorMsg');
            errorDiv.style.display = 'none';

            try {
                const response = await fetch('/users/register', { method: 'POST', body: formData });
                if (response.ok) {
                    this.reset();
                    showLogin();
                    document.getElementById('loginSuccessMsg').style.display = 'flex';
                } else {
                    const result = await response.json();
                    errorDiv.querySelector('span').textContent = parseErrorMessage(result, "Kayıt başarısız.");
                    errorDiv.style.display = 'flex';
                }
            } catch (err) {
                errorDiv.querySelector('span').textContent = "Sunucu hatası.";
                errorDiv.style.display = 'flex';
            }
        });


// Pin silme fonksiyonu (profil paneli için)
async function deletePin(id) {
        if(!confirm('Bu pini silmek istediğine emin misin?')) return;
        try {
            const response = await fetch('/pins/' + id, { method: 'DELETE' });
            if (response.ok) {
                const card = document.getElementById('pin-card-' + id);
                if (card) card.remove();
            } else {
                alert("Silinemedi. Yetkiniz olmayabilir.");
            }
        } catch(e) {
            alert("Bir hata oluştu.");
        }
    }

/*function switchProfile(tabName) {
        document.getElementById('menuEdit').classList.remove('active');
        document.getElementById('menuPins').classList.remove('active');
        document.getElementById('editProfileSection').style.display = 'none';
        document.getElementById('myPinsSection').style.display = 'none';

        if (tabName === 'edit') {
            document.getElementById('menuEdit').classList.add('active');
            document.getElementById('editProfileSection').style.display = 'block';
        } else {
            document.getElementById('menuPins').classList.add('active');
            document.getElementById('myPinsSection').style.display = 'block';
            loadMyPins();
        }
    }*/


// Profil resmini önizleme fonksiyonu
    function previewImage(input) {
        if (input.files && input.files[0]) {
            var reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('avatarPreviewImg').src = e.target.result;
            }
            reader.readAsDataURL(input.files[0]);
        }
    }

    async function loadMyPins() {
        const container = document.getElementById('myPinsContainer');
        if(container.children.length > 0) return; 

        container.innerHTML = '<p style="color:#888;">Yükleniyor...</p>';

        try {
            const response = await fetch('/pins/api/my-pins');
            const pins = await response.json();
            container.innerHTML = ''; 

            if (pins.length === 0) {
                container.innerHTML = '<p style="color:#888;">Henüz hiç pin yüklemediniz.</p>';
                return;
            }

            pins.forEach(pin => {
                let imgPath = pin.image_path; 
                if (imgPath && !imgPath.startsWith('/static') && !imgPath.startsWith('http')) {
                    imgPath = '/static/' + imgPath;
                }

                container.innerHTML += `
                    <div class="pin-card" id="pin-card-${pin.id}">  <img src="${imgPath}" alt="Pin Görseli">
                        <div class="pin-actions">
                            <span style="color:#888; font-size:12px;">${pin.title || 'İsimsiz'}</span>
                            <button onclick="deletePin(${pin.id})" class="btn-delete-pin">Sil</button>
                        </div>
                    </div>
                `;
            });
        } catch (e) {
            console.error(e);
            container.innerHTML = '<p style="color:#ff4444;">Pinler yüklenirken bir sorun oluştu.</p>';
        }
    }

     // 1. Profil Sekmeleri (Pinler / Panolar)
    function switchProfileTab(evt, tabName) {
        var i, tabcontent, tablinks;
        
        tabcontent = document.getElementsByClassName("tab-content");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
        }
        
        tablinks = document.getElementsByClassName("tab-btn");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        
        document.getElementById(tabName).style.display = "block";
        evt.currentTarget.className += " active";
        
        // Masonry düzenini yeniden uygula
        setTimeout(applyMasonry, 100);
    }

    // 2. Mesajlaşmayı Başlatan Fonksiyon
    function startDirectChat(event, userId, username, avatarUrl) {
        // Tıklama olayının yukarı (sayfaya) yayılmasını engelle
        // Bu sayede "sayfaya tıklayınca menüyü kapat" kodu çalışmaz
        event.stopPropagation();

        console.log("💬 Sohbet Başlatılıyor:", userId, username);

        // A. Mesaj Panelini Bul
        const panel = document.getElementById('messages-panel');
        
        if (panel) {
            // B. Paneli Görünür Yap (Slide Efekti)
            panel.classList.add('active');
            
            
            if (typeof openChatWindow === 'function') {
                openChatWindow(userId, username, avatarUrl);
            } else {
                console.error("HATA: masonry.js yüklenmemiş veya openChatWindow bulunamadı.");
                alert("Sohbet sistemi şu an kullanılamıyor.");
            }
        } else {
            console.error("HATA: messages-panel bulunamadı! base.html kontrol edilmeli.");
        }
    }