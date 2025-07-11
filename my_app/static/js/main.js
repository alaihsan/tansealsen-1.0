document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('fullscreenModal');
    const modalImage = document.getElementById('fullImage');
    const closeButton = document.querySelector('.close-button');
    const downloadButton = document.getElementById('downloadButton');
    const imageThumbnails = document.querySelectorAll('.image-thumbnail');

    // Fungsi untuk membuka modal
    imageThumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', function(event) {
            event.preventDefault(); // Mencegah perilaku default tautan
            const fullImageUrl = this.getAttribute('data-full-image');
            modal.style.display = 'block';
            modalImage.src = fullImageUrl;
            downloadButton.href = fullImageUrl; // Set link download
            
            // Opsional: Set caption dari alt text gambar thumbnail
            const altText = this.querySelector('img').alt;
            document.getElementById('caption').innerText = altText;
        });
    });

    // Fungsi untuk menutup modal
    closeButton.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    // Menutup modal jika mengklik di luar gambar
    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});