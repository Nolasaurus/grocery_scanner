const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const overlay = document.getElementById('overlay');
const captureButton = document.getElementById('captureButton');
const prompt = document.getElementById('prompt');
const thumbnails = document.getElementById('thumbnails');
const successMessage = document.getElementById('successMessage');
const manualEntry = document.getElementById('manualEntry');
const manualBarcodeInput = document.getElementById('manualBarcodeInput');
const freezeFrame = document.getElementById('freezeFrame');

// NEW: grab the button row (the div that contains Capture/Cancel)
const buttonsRow = document.querySelector('.buttons');

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

// Keep exactly one thumbnail per step; retakes replace existing
const thumbnailImgs = {
  barcode: null,
  nutrition: null,
  label: null
};

// Draw overlay guide rectangle on barcode step
function drawOverlay() {
  // If not on step 1, or if we're frozen, clear overlay
  if (
    currentStep !== 1 ||
    (freezeFrame && freezeFrame.style.display === 'block')
  ) {
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

// Freeze/unfreeze helpers
function freezeToImage(base64Image) {
  if (!freezeFrame) return;

  freezeFrame.src = base64Image;
  freezeFrame.style.display = 'block';

  video.style.display = 'none';
  overlay.style.display = 'none';
}

function unfreezeToLiveVideo() {
  if (!freezeFrame) return;

  freezeFrame.src = '';
  freezeFrame.style.display = 'none';

  video.style.display = 'block';
  overlay.style.display = 'block';

  drawOverlay();
}

// UI mode helpers
function showManualEntryReplacingControls() {
  // Replace thumbnails + buttons with manual entry
  if (thumbnails) thumbnails.style.display = 'none';
  if (buttonsRow) buttonsRow.style.display = 'none';

  manualEntry.style.display = 'block';
  manualBarcodeInput.focus();
}

function restoreNormalControls() {
  manualEntry.style.display = 'none';
  manualBarcodeInput.value = '';

  if (thumbnails) thumbnails.style.display = 'flex'; // matches your CSS layout
  if (buttonsRow) buttonsRow.style.display = 'block';
}

// Progress UI
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
  drawOverlay();
}

// Replace-or-insert thumbnail for a step
function upsertThumbnail(imageKey, base64Image) {
  if (thumbnailImgs[imageKey]) {
    thumbnailImgs[imageKey].src = base64Image;
    return;
  }

  const img = document.createElement('img');
  img.src = base64Image;
  img.className = 'thumbnail';
  thumbnails.appendChild(img);
  thumbnailImgs[imageKey] = img;
}

// Manual entry actions (wired to HTML buttons)
function hideManualEntry() {
  // Retake Photo button calls this
  // - remove manual entry panel
  // - return to live camera on step 1
  manualBarcodeData = null;

  restoreNormalControls();
  unfreezeToLiveVideo();

  currentStep = 1;
  updateProgress();

  captureButton.disabled = false;
}

function submitManualBarcode() {
  const barcodeValue = manualBarcodeInput.value.trim();
  if (!barcodeValue) {
    alert('Please enter a barcode number');
    return;
  }

  manualBarcodeData = barcodeValue;

  // Move to next step
  restoreNormalControls();
  currentStep++;
  updateProgress();

  // Resume live camera for steps 2/3
  unfreezeToLiveVideo();

  captureButton.disabled = false;
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

// Capture flow
captureButton.addEventListener('click', async () => {
  captureButton.disabled = true;

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const context = canvas.getContext('2d');
  context.drawImage(video, 0, 0);

  const base64Image = canvas.toDataURL('image/jpeg', 0.95);
  const imageKey = imageKeys[currentStep];

  capturedImages[imageKey] = base64Image;
  upsertThumbnail(imageKey, base64Image);

  if (currentStep === 1) {
    // Freeze captured barcode image full-size
    freezeToImage(base64Image);

    // Replace bottom controls with manual entry
    showManualEntryReplacingControls();

    // Do NOT advance step until manual barcode is submitted
    captureButton.disabled = false;
    return;
  }

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
    // Hide scanning UI during submission
    video.style.display = 'none';
    if (freezeFrame) freezeFrame.style.display = 'none';
    overlay.style.display = 'none';

    if (buttonsRow) buttonsRow.style.display = 'none';
    if (thumbnails) thumbnails.style.display = 'none';
    manualEntry.style.display = 'none';

    prompt.textContent = 'Submitting...';
    prompt.className = 'submitting';

    const payload = {
      ...capturedImages,
      manual_barcode: manualBarcodeData
    };

    const response = await fetch('/submit_product', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const result = await response.json();

    if (result.success) {
      document.querySelector('.container').style.display = 'none';
      successMessage.style.display = 'block';
      setTimeout(() => {
        window.location.href = '/';
      }, 2000);
      return;
    }

    alert('Error: ' + result.error);
    // restore UI on failure
    prompt.className = 'prompt';
    prompt.textContent = prompts[currentStep];

    if (currentStep === 1 && capturedImages.barcode) {
      // return to frozen + manual entry (since step 1 requires manual)
      freezeToImage(capturedImages.barcode);
      showManualEntryReplacingControls();
    } else {
      restoreNormalControls();
      video.style.display = 'block';
      overlay.style.display = 'block';
      drawOverlay();
      if (buttonsRow) buttonsRow.style.display = 'block';
      if (thumbnails) thumbnails.style.display = 'flex';
      captureButton.disabled = false;
    }
  } catch (err) {
    console.error('Error submitting product:', err);
    alert('Error submitting product: ' + err.message);

    // restore UI on exception
    prompt.className = 'prompt';
    prompt.textContent = prompts[currentStep];

    if (currentStep === 1 && capturedImages.barcode) {
      freezeToImage(capturedImages.barcode);
      showManualEntryReplacingControls();
    } else {
      restoreNormalControls();
      video.style.display = 'block';
      overlay.style.display = 'block';
      drawOverlay();
      if (buttonsRow) buttonsRow.style.display = 'block';
      if (thumbnails) thumbnails.style.display = 'flex';
      captureButton.disabled = false;
    }
  }
}
