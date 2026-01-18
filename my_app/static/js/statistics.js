document.addEventListener('DOMContentLoaded', () => {

    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const dateRangePicker = document.getElementById('date_range_picker');

    // Inisialisasi Flatpickr
    if (dateRangePicker && startDateInput && endDateInput) {
        const fp = flatpickr(dateRangePicker, {
            mode: "range",
            dateFormat: "Y-m-d",
            altInput: true,
            altFormat: "d F Y",
            locale: "id",
            defaultDate: (startDateInput.value && endDateInput.value) ? [startDateInput.value, endDateInput.value] : [],
            onClose: function(selectedDates) {
                // Saat rentang tanggal dipilih, isi input tersembunyi
                if (selectedDates.length === 2) {
                    startDateInput.value = selectedDates[0].toISOString().split('T')[0];
                    endDateInput.value = selectedDates[1].toISOString().split('T')[0];
                }
            }
        });
    }
});

/**
 * Memulai proses export PDF dengan filter yang sedang aktif.
 */
function exportPDF() {
    showNotification('Mempersiapkan PDF...', 'info');

    // Dapatkan parameter filter dari URL saat ini
    const currentParams = window.location.search;
    
    // Arahkan ke endpoint export dengan parameter yang sama
    window.location.href = '/export_violations_pdf' + currentParams;

    // Tampilkan notifikasi setelah beberapa saat (karena tidak ada cara pasti untuk tahu kapan unduhan dimulai)
    setTimeout(() => {
        showNotification('Unduhan PDF akan segera dimulai.', 'success');
    }, 1500);
}

/**
 * Menampilkan notifikasi toast di pojok kanan atas.
 * @param {string} message Pesan yang akan ditampilkan.
 * @param {string} type Tipe notifikasi ('success', 'danger', 'info', 'warning').
 */
function showNotification(message, type = 'info') {
    // Hapus notifikasi yang sudah ada
    const existingToast = document.querySelector('.notification-toast');
    if (existingToast) {
        existingToast.remove();
    }

    // Buat elemen notifikasi
    const toast = document.createElement('div');
    toast.className = `notification-toast ${type}`;
    toast.innerHTML = `
        <div class="flex items-center space-x-3">
            <i class="fas ${getNotificationIcon(type)} text-xl"></i>
            <span class="font-medium">${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    // Tampilkan notifikasi
    setTimeout(() => {
        toast.classList.add('show');
    }, 10); // delay kecil untuk memastikan transisi CSS berjalan

    // Sembunyikan dan hapus notifikasi setelah 4 detik
    setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => toast.remove());
    }, 4000);
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'danger': 'fa-exclamation-triangle',
        'info': 'fa-info-circle',
        'warning': 'fa-exclamation-circle'
    };
    return icons[type] || icons.info;
}
