document.addEventListener('DOMContentLoaded', () => {
    // Terapkan efek fade-in pada daftar pelanggaran saat halaman dimuat
    const violationList = document.querySelector('.violation-list');
    if (violationList) {
        violationList.classList.add('fade-in');
    }

    // --- Inisialisasi Date Picker BARU ---
    const datePickerInput = document.getElementById('tanggal_kejadian');
    if (datePickerInput) {
        flatpickr(datePickerInput, {
            // Menggunakan lokalisasi Bahasa Indonesia
            "locale": "id",
            // Format tanggal yang diinginkan: 20 Mei 1992
            dateFormat: "d F Y",
            // Set tanggal default ke hari ini
            defaultDate: "today",
            // Menonaktifkan tanggal di masa depan
            maxDate: "today"
        });
    }


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
            const details = this.closest('.violation-item').querySelector('.violation-details').innerHTML;
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
        fullscreenModal.addEventListener('click', function(e) {
            if (e.target === fullscreenModal) {
                fullscreenModal.style.display = 'none';
            }
        });
    }

    // --- Logika untuk Pengalih Tampilan (View Switcher) ---
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
    const paginationNav = document.querySelector('.pagination-nav');

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
            if(paginationNav){
                paginationNav.style.display = searchTerm ? 'none' : '';
            }
        });
    }

    // --- Logika untuk Konfirmasi Hapus ---
    const deleteModal = document.getElementById('deleteConfirmModal');
    const studentNameToDelete = document.getElementById('studentNameToDelete');
    const confirmInput = document.getElementById('deleteConfirmInput');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const cancelBtn = document.getElementById('cancelDeleteBtn');
    let violationIdToDelete = null;

    function openDeleteModal(id, studentName) {
        violationIdToDelete = id;
        studentNameToDelete.textContent = studentName;
        confirmInput.value = '';
        confirmBtn.disabled = true;
        deleteModal.style.display = 'block';
        confirmInput.focus();
    }

    function closeDeleteModal() {
        deleteModal.style.display = 'none';
    }

    document.querySelectorAll('.delete-icon-btn').forEach(button => {
        button.addEventListener('click', function() {
            const violationItem = this.closest('.violation-item');
            const id = violationItem.dataset.id;
            const name = violationItem.querySelector('.student-name').textContent;
            openDeleteModal(id, name);
        });
    });

    if (confirmInput) {
        confirmInput.addEventListener('input', function() {
            confirmBtn.disabled = this.value.toUpperCase() !== 'SETUJU';
        });
    }

    if (cancelBtn) cancelBtn.addEventListener('click', closeDeleteModal);

    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (!violationIdToDelete) return;

            fetch(`/delete/${violationIdToDelete}`, {
                    method: 'POST',
                })
                .then(response => {
                    if (response.ok) {
                        window.location.reload();
                    } else {
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
    
    if (deleteModal) {
        deleteModal.addEventListener('click', function(e) {
            if (e.target === deleteModal) {
                closeDeleteModal();
            }
        });
    }
});