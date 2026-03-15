/**
 * ComfyUI Gallery Overlay
 * Adds lightbox/gallery functionality to generated images
 */

(function() {
    // Remove existing overlay if it exists (fixes caching issues after script updates)
    const existingOverlay = document.getElementById('comfy-gallery-overlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }

    // Create gallery overlay HTML
    const overlayHtml = `
        <div id="comfy-gallery-overlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.9); z-index: 9999; justify-content: center; align-items: center;">
            <div style="position: relative; max-width: 90%; max-height: 90%;">
                <img id="comfy-gallery-image" style="max-width: 100%; max-height: 90vh; border-radius: 8px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);" />
            </div>
            <button id="comfy-gallery-close" style="position: absolute; top: -40px; right: 0; background: transparent; border: none; color: white; font-size: 32px; cursor: pointer; padding: 0; line-height: 1;">&times;</button>

            <button id="comfy-gallery-prev" style="position: absolute; top: 50%; left: -60px; transform: translateY(-50%); background: rgba(255, 255, 255, 0.2); border: none; color: white; font-size: 48px; cursor: pointer; padding: 20px; border-radius: 50%; transition: background 0.3s;" onmouseover="this.style.background='rgba(255, 255, 255, 0.4)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'">&#8592;</button>
            <button id="comfy-gallery-next" style="position: absolute; top: 50%; right: -60px; transform: translateY(-50%); background: rgba(255, 255, 255, 0.2); border: none; color: white; font-size: 48px; cursor: pointer; padding: 20px; border-radius: 50%; transition: background 0.3s;" onmouseover="this.style.background='rgba(255, 255, 255, 0.4)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'">&#8594;</button>
            <div id="comfy-gallery-info" style="position: absolute; bottom: -30px; left: 50%; transform: translateX(-50%); color: white; font-size: 12px; text-align: center;"></div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', overlayHtml);

    const overlay = document.getElementById('comfy-gallery-overlay');
    const galleryImage = document.getElementById('comfy-gallery-image');
    const closeBtn = document.getElementById('comfy-gallery-close');

    const prevBtn = document.getElementById('comfy-gallery-prev');
    const nextBtn = document.getElementById('comfy-gallery-next');
    const infoDiv = document.getElementById('comfy-gallery-info');

    let imageList = [];
    let currentIndex = 0;

    // Initialize image list from all comfy-generated-image elements
    function initImageList() {
        const images = document.querySelectorAll('.comfy-generated-image[data-index]');
        imageList = Array.from(images).map(img => ({
            src: img.src,
            filename: img.dataset.filename || 'image.png',
            index: parseInt(img.dataset.index) || 0
        }));
        imageList.sort((a, b) => a.index - b.index);
    }

    // Show overlay with specific image
    function showOverlay(index) {
        if (imageList.length === 0) {
            initImageList();
        }
        
        if (imageList.length === 0) return;
        
        currentIndex = index;
        const image = imageList[currentIndex];
        
        galleryImage.src = image.src;
        galleryImage.alt = image.filename;
        
        // Update info
        infoDiv.textContent = `${currentIndex + 1} / ${imageList.length} - ${image.filename}`;
        
        // Update button states
        prevBtn.style.display = currentIndex > 0 ? 'block' : 'none';
        nextBtn.style.display = currentIndex < imageList.length - 1 ? 'block' : 'none';
        
        // Show overlay
        overlay.style.display = 'flex';
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    // Close overlay
    function closeOverlay() {
        overlay.style.display = 'none';
        document.body.style.overflow = '';
    }

    // Next image
    function nextImage() {
        if (currentIndex < imageList.length - 1) {
            showOverlay(currentIndex + 1);
        }
    }

    // Previous image
    function prevImage() {
        if (currentIndex > 0) {
            showOverlay(currentIndex - 1);
        }
    }


    // Event listeners
    closeBtn.addEventListener('click', closeOverlay);

    prevBtn.addEventListener('click', prevImage);
    nextBtn.addEventListener('click', nextImage);
    
    // Click outside to close
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeOverlay();
        }
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (!overlay.style.display || overlay.style.display === 'none') return;
        
        // Prevent default behavior to stop event propagation
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        
        if (e.key === 'Escape') {
            closeOverlay();
        } else if (e.key === 'ArrowLeft') {
            prevImage();
        } else if (e.key === 'ArrowRight') {
            nextImage();
        }
    }, { capture: true });

    // Add click handler using event delegation
    document.body.addEventListener('click', (e) => {
        const img = e.target.closest('.comfy-generated-image');
        if (img) {
            initImageList();
            const imgIndex = imageList.findIndex(i => i.src === img.src);
            if (imgIndex !== -1) {
                showOverlay(imgIndex);
            }
        }
    });

    console.log('ComfyUI Gallery Overlay initialized');
})();