const menuBtn = document.getElementById('menuBtn');
const menuModal = document.getElementById('menuModal');
const menuIcon = document.getElementById('menuIcon');
const closeIcon = document.getElementById('closeIcon');

menuBtn.onclick = function(e) {
    e.preventDefault();
    if (menuModal.style.display === 'flex') {
        menuModal.style.display = 'none';
        menuIcon.style.display = '';
        closeIcon.style.display = 'none';
    } else {
        menuModal.style.display = 'flex';
        menuIcon.style.display = 'none';
        closeIcon.style.display = '';
    }
};

// モーダルの外側クリックで閉じる
menuModal.onclick = function(e) {
    if (e.target === this) {
        menuModal.style.display = 'none';
        menuIcon.style.display = '';
        closeIcon.style.display = 'none';
    }
};