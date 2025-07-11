document.addEventListener('DOMContentLoaded', () => {
    // --- Logika untuk Modal Gambar Fullscreen ---
    const imageThumbnails = document.querySelectorAll('.image-thumbnail');
    const fullscreenModal = document.getElementById('fullscreenModal');
    const modalImg = document.getElementById('fullImage');
    const captionText = document.getElementById('caption');
    const downloadButton = document.getElementById('downloadButton');
    const closeBtn = document.querySelector('.close-button');

    imageThumbnails.forEach(thumb => {
        thumb.addEventListener('click', function(e) {
            e.preventDefault();
            fullscreenModal.style.display = 'block';
            const fullImageUrl = this.getAttribute('data-full-image');
            modalImg.src = fullImageUrl;
            const details = this.nextElementSibling.innerHTML;
            captionText.innerHTML = details;
            downloadButton.href = fullImageUrl;
            downloadButton.download = fullImageUrl.split('/').pop();
        });
    });

    if (closeBtn) {
        closeBtn.onclick = function() {
            fullscreenModal.style.display = 'none';
        }
    }

    if (fullscreenModal) {
        // Menutup modal jika klik di luar gambar
        fullscreenModal.addEventListener('click', function(e) {
            if (e.target === fullscreenModal) {
                fullscreenModal.style.display = 'none';
            }
        });
    }

    // --- Logika untuk Pengalih Tampilan (View Switcher) ---
    const violationList = document.querySelector('.violation-list');
    const viewCardBtn = document.getElementById('view-card-btn');
    const viewListBtn = document.getElementById('view-list-btn');
    const transitionTime = 400;

    function switchView(newView) {
        if (!violationList || violationList.classList.contains(newView + '-view')) return;
        violationList.classList.add('fading');
        setTimeout(() => {
            violationList.classList.remove('list-view', 'card-view');
            violationList.classList.add(newView + '-view');
            if (viewCardBtn) viewCardBtn.classList.toggle('active', newView === 'card');
            if (viewListBtn) viewListBtn.classList.toggle('active', newView === 'list');
            violationList.classList.remove('fading');
        }, transitionTime);
    }

    if (viewCardBtn) viewCardBtn.addEventListener('click', () => switchView('card'));
    if (viewListBtn) viewListBtn.addEventListener('click', () => switchView('list'));

    // --- Logika untuk Filter Pencarian ---
    const searchInput = document.getElementById('searchInput');
    const noResultsMessage = document.getElementById('no-results-message');

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            const items = document.querySelectorAll('.violation-item');
            let visibleCount = 0;

            items.forEach(item => {
                const studentNameElement = item.querySelector('.student-name');
                const studentClassElement = item.querySelector('.violation-details p:nth-child(2)');
                const studentName = studentNameElement ? studentNameElement.textContent.toLowerCase() : '';
                const studentClass = studentClassElement ? studentClassElement.textContent.toLowerCase() : '';
                const isMatch = studentName.includes(searchTerm) || studentClass.includes(searchTerm);
                
                item.style.display = isMatch ? '' : 'none';
                if (isMatch) visibleCount++;
            });

            if (noResultsMessage) {
                noResultsMessage.style.display = (visibleCount === 0 && items.length > 0) ? 'block' : 'none';
            }
        });
    }

    // --- Logika BARU untuk Konfirmasi Hapus ---
    const deleteModal = document.getElementById('deleteConfirmModal');
    const studentNameToDelete = document.getElementById('studentNameToDelete');
    const confirmInput = document.getElementById('deleteConfirmInput');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const cancelBtn = document.getElementById('cancelDeleteBtn');
    let violationIdToDelete = null;

    // Fungsi untuk membuka modal
    function openDeleteModal(id, studentName) {
        violationIdToDelete = id;
        studentNameToDelete.textContent = studentName;
        confirmInput.value = ''; // Kosongkan input
        confirmBtn.disabled = true; // Pastikan tombol hapus nonaktif
        deleteModal.style.display = 'block';
        confirmInput.focus();
    }

    // Fungsi untuk menutup modal
    function closeDeleteModal() {
        deleteModal.style.display = 'none';
    }

    // Event listener untuk semua tombol hapus di kartu
    document.querySelectorAll('.delete-icon-btn').forEach(button => {
        button.addEventListener('click', function() {
            const violationItem = this.closest('.violation-item');
            const id = violationItem.dataset.id;
            const name = violationItem.querySelector('.student-name').textContent;
            openDeleteModal(id, name);
        });
    });

    // Cek input konfirmasi
    if (confirmInput) {
        confirmInput.addEventListener('input', function() {
            // Aktifkan tombol jika input sesuai (case-insensitive)
            confirmBtn.disabled = this.value.toUpperCase() !== 'SETUJU';
        });
    }

    // Event listener untuk tombol Batal
    if (cancelBtn) cancelBtn.addEventListener('click', closeDeleteModal);

    // Event listener untuk tombol Konfirmasi Hapus
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (!violationIdToDelete) return;

            // Kirim request DELETE ke server menggunakan Fetch API
            fetch(`/delete/${violationIdToDelete}`, {
                method: 'POST', // Form di Flask biasanya menggunakan POST untuk delete
            })
            .then(response => {
                if (response.ok) {
                    // Jika berhasil, refresh halaman untuk melihat perubahan
                    window.location.reload();
                } else {
                    // Jika gagal, tampilkan pesan error
                    alert('Gagal menghapus data. Silakan coba lagi.');
                    closeDeleteModal();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Terjadi kesalahan koneksi.');
                closeDeleteModal();
            });
        });
    }
    
    // Menutup modal jika klik di luar dialog
    if (deleteModal) {
        deleteModal.addEventListener('click', function(e) {
            if (e.target === deleteModal) {
                closeDeleteModal();
            }
        });
    }
});