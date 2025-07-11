document.addEventListener('DOMContentLoaded', () => {
    // Terapkan efek fade-in pada daftar pelanggaran saat halaman dimuat
    const violationList = document.querySelector('.violation-list');
    if (violationList) {
        violationList.classList.add('fade-in');
    }

    // --- Logika Date Picker ---
    const datePickerInput = document.getElementById('tanggal_kejadian');
    if (datePickerInput) {
        flatpickr(datePickerInput, { "locale": "id", dateFormat: "d F Y", defaultDate: "today", maxDate: "today" });
    }

    // --- Logika Modal Gambar Fullscreen ---
    const imageThumbnails = document.querySelectorAll('.image-thumbnail');
    const fullscreenModal = document.getElementById('fullscreenModal');
    if (fullscreenModal) {
        const modalImg = document.getElementById('fullImage');
        const captionText = document.getElementById('caption');
        const downloadButton = document.getElementById('downloadButton');
        const closeBtn = fullscreenModal.querySelector('.close-button');

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
        if (closeBtn) { closeBtn.onclick = () => fullscreenModal.style.display = 'none'; }
        fullscreenModal.addEventListener('click', (e) => { if (e.target === fullscreenModal) fullscreenModal.style.display = 'none'; });
    }

    // --- Logika Pengalih Tampilan ---
    const viewCardBtn = document.getElementById('view-card-btn');
    const viewListBtn = document.getElementById('view-list-btn');
    if (viewCardBtn && viewListBtn && violationList) {
        const transitionTime = 400;
        const switchView = (newView) => {
            if (violationList.classList.contains(newView + '-view')) return;
            violationList.classList.add('fading');
            setTimeout(() => {
                violationList.classList.remove('list-view', 'card-view');
                violationList.classList.add(newView + '-view');
                viewCardBtn.classList.toggle('active', newView === 'card');
                viewListBtn.classList.toggle('active', newView === 'list');
                violationList.classList.remove('fading');
            }, transitionTime);
        };
        viewCardBtn.addEventListener('click', () => switchView('card'));
        viewListBtn.addEventListener('click', () => switchView('list'));
    }
    
    // --- Logika Filter Pencarian ---
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        const noResultsMessage = document.getElementById('no-results-message');
        const paginationNav = document.querySelector('.pagination-nav');
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            const items = document.querySelectorAll('.violation-item');
            let visibleCount = 0;
            items.forEach(item => {
                const studentName = (item.querySelector('.student-name')?.textContent || '').toLowerCase();
                const studentClass = (item.querySelector('.violation-details p:nth-child(2)')?.textContent || '').toLowerCase();
                const isMatch = studentName.includes(searchTerm) || studentClass.includes(searchTerm);
                item.style.display = isMatch ? '' : 'none';
                if (isMatch) visibleCount++;
            });
            if (noResultsMessage) noResultsMessage.style.display = (visibleCount === 0 && items.length > 0) ? 'block' : 'none';
            if (paginationNav) paginationNav.style.display = searchTerm ? 'none' : '';
        });
    }

    // --- Logika Konfirmasi Hapus ---
    const deleteModal = document.getElementById('deleteConfirmModal');
    if (deleteModal) {
        const studentNameToDelete = document.getElementById('studentNameToDelete');
        const confirmInput = document.getElementById('deleteConfirmInput');
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        const cancelBtn = document.getElementById('cancelDeleteBtn');
        let violationIdToDelete = null;

        const openDeleteModal = (id, studentName) => {
            violationIdToDelete = id;
            studentNameToDelete.textContent = studentName;
            confirmInput.value = '';
            confirmBtn.disabled = true;
            deleteModal.style.display = 'block';
            confirmInput.focus();
        };
        const closeDeleteModal = () => deleteModal.style.display = 'none';

        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', function() {
                const violationItem = this.closest('.violation-item');
                const id = violationItem.dataset.id;
                const name = violationItem.querySelector('.student-name').textContent;
                openDeleteModal(id, name);
            });
        });
        
        confirmInput.addEventListener('input', () => { confirmBtn.disabled = confirmInput.value.toUpperCase() !== 'SETUJU'; });
        cancelBtn.addEventListener('click', closeDeleteModal);
        confirmBtn.addEventListener('click', () => {
            if (violationIdToDelete) {
                fetch(`/delete/${violationIdToDelete}`, { method: 'POST' })
                .then(response => response.ok ? window.location.reload() : alert('Gagal menghapus data.'))
                .catch(err => { console.error(err); alert('Terjadi kesalahan koneksi.'); })
                .finally(closeDeleteModal);
            }
        });
        deleteModal.addEventListener('click', (e) => { if (e.target === deleteModal) closeDeleteModal(); });
    }

    // --- Logika BARU untuk Cetak Kartu ---
    document.querySelectorAll('.print-btn').forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.violation-item');
            const clone = card.cloneNode(true); // Duplikat kartu

            // Hapus tombol aksi dari kloningan agar tidak ikut tercetak
            clone.querySelector('.card-actions').remove();

            // Buat kontainer sementara untuk dicetak
            const printContainer = document.createElement('div');
            printContainer.classList.add('print-area');
            
            // Tambahkan judul dan gambar
            const header = document.createElement('div');
            header.classList.add('print-header');
            header.innerHTML = '<h3>Detail Pelanggaran Siswa</h3>';
            printContainer.appendChild(header);
            
            // Cek jika ada gambar, tambahkan ke area cetak
            const image = card.querySelector('img');
            if (image) {
                const printImage = document.createElement('img');
                printImage.src = image.src;
                printImage.classList.add('print-img');
                printContainer.appendChild(printImage);
            }

            // Tambahkan detail pelanggaran
            printContainer.appendChild(clone.querySelector('.violation-details'));
            
            // Sembunyikan semua elemen di body dan tampilkan hanya area cetak
            document.body.appendChild(printContainer);
            window.print(); // Panggil dialog cetak browser
            document.body.removeChild(printContainer); // Hapus area cetak setelah selesai
        });
    });
});