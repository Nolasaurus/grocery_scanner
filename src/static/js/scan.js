const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const overlay = document.getElementById('overlay');
const captureButton = document.getElementById('captureButton');
const prompt = document.getElementById('prompt');
const thumbnails = document.getElementById('thumbnails');
const successMessage = document.getElementById('successMessage');
const manualEntry = document.getElementById('manualEntry');
const manualEntryLink = document.getElementById('manualEntryLink');
const manualBarcodeInput = document.getElementById('manualBarcodeInput');

let currentStep = 1;
let manualBarcodeData = null;
const capturedImages = {
    barcode: null,
    nutrition: null,
    label: null
};

const prompts = {
    1: 'Scan Barcode',
    2: 'Capture Nutrition Facts',
    3: 'Capture Box Label'
};

const imageKeys = {
    1: 'barcode',
    2: 'nutrition',
    3: 'label'
};

// Draw overlay guide rectangle on barcode step
function drawOverlay() {
    if (currentStep !== 1) {
        const ctx = overlay.getContext('2d');
        ctx.clearRect(0, 0, overlay.width, overlay.height);
        return;
    }
    
    const ctx = overlay.getContext('2d');
    overlay.width = video.videoWidth;
    overlay.height = video.videoHeight;
    
    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
    ctx.fillRect(0, 0, overlay.width, overlay.height);
    
    const rectWidth = overlay.width * 0.7;
    const rectHeight = overlay.height * 0.5;
    const rectX = (overlay.width - rectWidth) / 2;
    const rectY = (overlay.height - rectHeight) / 2;
    
    ctx.clearRect(rectX, rectY, rectWidth, rectHeight);
    ctx.strokeStyle = '#4CAF50';
    ctx.lineWidth = 3;
    ctx.strokeRect(rectX, rectY, rectWidth, rectHeight);
    ctx.fillStyle = '#4CAF50';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Place barcode here', overlay.width / 2, rectY - 15);
}

// Start camera
(async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'environment',
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            } 
        });
        
        video.srcObject = stream;
        video.addEventListener('loadedmetadata', () => {
            drawOverlay();
        });
        
        captureButton.disabled = false;
        updateProgress();
    } catch (err) {
        console.error('Error accessing camera:', err);
        alert('Error: Could not access camera. ' + err.message);
    }
})();

function updateProgress() {
    for (let i = 1; i <= 3; i++) {
        const dot = document.getElementById(`dot${i}`);
        if (i < currentStep) {
            dot.className = 'progress-dot completed';
        } else if (i === currentStep) {
            dot.className = 'progress-dot active';
        } else {
            dot.className = 'progress-dot';
        }
    }
    
    prompt.textContent = prompts[currentStep];
    
    if (currentStep === 1) {
        manualEntryLink.style.display = 'block';
    } else {
        manualEntryLink.style.display = 'none';
    }
    
    drawOverlay();
}

function addThumbnail(base64Image) {
    const img = document.createElement('img');
    img.src = base64Image;
    img.className = 'thumbnail';
    thumbnails.appendChild(img);
}

function showManualEntry() {
    manualEntry.style.display = 'block';
    captureButton.disabled = true;
    manualBarcodeInput.focus();
}

function hideManualEntry() {
    manualEntry.style.display = 'none';
    manualBarcodeInput.value = '';
    captureButton.disabled = false;
}

function submitManualBarcode() {
    const barcodeValue = manualBarcodeInput.value.trim();
    if (!barcodeValue) {
        alert('Please enter a barcode number');
        return;
    }
    
    manualBarcodeData = barcodeValue;
    hideManualEntry();
    prompt.textContent = `Barcode: ${barcodeValue} - Now capture the image`;
    prompt.style.color = '#FFA500';
}

captureButton.addEventListener('click', async () => {
    captureButton.disabled = true;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0);
    
    const base64Image = canvas.toDataURL('image/jpeg', 0.95);
    const imageKey = imageKeys[currentStep];
    capturedImages[imageKey] = base64Image;
    
    addThumbnail(base64Image);
    
    if (currentStep < 3) {
        currentStep++;
        updateProgress();
        captureButton.disabled = false;
    } else {
        await submitProduct();
    }
});

async function submitProduct() {
    try {
        video.style.display = 'none';
        captureButton.style.display = 'none';
        prompt.textContent = 'Submitting...';
        prompt.className = 'submitting';
        
        const payload = {
            ...capturedImages,
            manual_barcode: manualBarcodeData
        };
        
        const response = await fetch('/submit_product', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.querySelector('.container').style.display = 'none';
            successMessage.style.display = 'block';
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (err) {
        console.error('Error submitting product:', err);
        alert('Error submitting product: ' + err.message);
    }
}
