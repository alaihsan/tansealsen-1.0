document.addEventListener('DOMContentLoaded', () => {
    // --- Logika untuk Modal Gambar Fullscreen ---
    const imageThumbnails = document.querySelectorAll('.image-thumbnail');
    const modal = document.getElementById('fullscreenModal');
    const modalImg = document.getElementById('fullImage');
    const captionText = document.getElementById('caption');
    const downloadButton = document.getElementById('downloadButton');
    const closeBtn = document.querySelector('.close-button');

    imageThumbnails.forEach(thumb => {
        thumb.addEventListener('click', function(e) {
            e.preventDefault();
            modal.style.display = 'block';
            const fullImageUrl = this.getAttribute('data-full-image');
            modalImg.src = fullImageUrl;
            // Dapatkan detail dari item untuk caption
            const details = this.nextElementSibling.innerHTML;
            captionText.innerHTML = details;
            // Siapkan link download
            downloadButton.href = fullImageUrl;
            // Beri nama file download dari URL
            downloadButton.download = fullImageUrl.split('/').pop();
        });
    });

    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        }
    }

    if (modal) {
        modal.onclick = function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        }
    }

    // --- Logika Baru untuk Pengalih Tampilan (View Switcher) ---
    const violationList = document.querySelector('.violation-list');
    const viewCardBtn = document.getElementById('view-card-btn');
    const viewListBtn = document.getElementById('view-list-btn');
    const transitionTime = 400; // Sesuaikan dengan durasi transisi di CSS (dalam ms)

    // Fungsi untuk mengganti mode
    function switchView(newView) {
        // Jika sudah dalam mode yang dipilih, jangan lakukan apa-apa
        if (violationList.classList.contains(newView + '-view')) {
            return;
        }

        // 1. Tambahkan class untuk memulai efek fade-out
        violationList.classList.add('fading');

        // 2. Tunggu transisi fade-out selesai
        setTimeout(() => {
            // 3. Ganti class utama (card-view / list-view)
            if (newView === 'card') {
                violationList.classList.remove('list-view');
                violationList.classList.add('card-view');
                // Update tombol aktif
                viewCardBtn.classList.add('active');
                viewListBtn.classList.remove('active');
            } else {
                violationList.classList.remove('card-view');
                violationList.classList.add('list-view');
                // Update tombol aktif
                viewListBtn.classList.add('active');
                viewCardBtn.classList.remove('active');
            }

            // 4. Hapus class fading untuk memicu efek fade-in
            violationList.classList.remove('fading');
        }, transitionTime);
    }

    // Tambahkan event listener ke tombol
    if (viewCardBtn) {
        viewCardBtn.addEventListener('click', () => switchView('card'));
    }
    if (viewListBtn) {
        viewListBtn.addEventListener('click', () => switchView('list'));
    }
});