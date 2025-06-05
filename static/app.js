let currentQrCode = null;
let totalSeconds = 0;
let timerInterval = null;
let scanInterval = null;

const video = document.getElementById('video');
const notification = document.getElementById('notification');

function showNotification(message, isError = false) {
    notification.textContent = message;
    notification.classList.remove('hidden');
    notification.style.color = isError ? '#ff5252' : '#4caf50';
    setTimeout(() => notification.classList.add('hidden'), 4000);
}

function updateResult(message) {
    document.getElementById('result').textContent = message;
}

function updateTimestamp(content) {
    document.getElementById('timestamp').textContent = content;
}

function updateTimerDisplay() {
    let h = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
    let m = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
    let s = String(totalSeconds % 60).padStart(2, '0');
    document.getElementById('timer').textContent = `Chronomètre : ${h}:${m}:${s}`;
}

function scanCameraFrame() {
    if (video.videoWidth === 0 || video.videoHeight === 0) return;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const imageData = canvas.toDataURL('image/png');

    fetch('/scan_base64', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData }),
    })
    .then(res => res.json())
    .then(result => {
        if (result.message && result.message !== currentQrCode) {
            currentQrCode = result.message;
            updateResult("✅ " + currentQrCode);
            showNotification("QR Code détecté !");
            const ts = new Date().toLocaleString('fr-FR', { timeZone: 'Europe/Paris' });
            updateTimestamp("Horodatage : " + ts);
        } else if (result.error) {
            updateResult("❌ " + result.error);
            showNotification(result.error, true);
        }
    })
    .catch(() => showNotification("Erreur de traitement", true));
}

document.getElementById('start-camera').addEventListener('click', () => {
    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
        .then(stream => {
            video.srcObject = stream;
            video.classList.remove('hidden');
            showNotification("Caméra activée");
            video.addEventListener('loadedmetadata', () => {
                if (!scanInterval) scanInterval = setInterval(scanCameraFrame, 2000);
            });
        })
        .catch(() => showNotification("Impossible d’accéder à la caméra", true));
});

document.getElementById('upload-form').addEventListener('submit', function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('qr-image');
    const file = fileInput.files[0];
    if (!file) {
        showNotification("Aucune image sélectionnée", true);
        return;
    }

    const reader = new FileReader();
    reader.onloadend = function () {
        fetch('/scan_base64', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: reader.result }),
        })
        .then(res => res.json())
        .then(result => {
            if (result.message) {
                currentQrCode = result.message;
                updateResult("✅ " + currentQrCode);
                showNotification("QR Code détecté !");
                const ts = new Date().toLocaleString('fr-FR', { timeZone: 'Europe/Paris' });
                updateTimestamp("Horodatage : " + ts);
            } else if (result.error) {
                updateResult("❌ " + result.error);
                showNotification(result.error, true);
            }
        })
        .catch(() => showNotification("Erreur de traitement", true));
    };
    reader.readAsDataURL(file);
});

document.getElementById('start-timer').addEventListener('click', () => {
    if (!currentQrCode) {
        showNotification("Veuillez d’abord scanner un QR Code", true);
        return;
    }
    if (!timerInterval) {
        timerInterval = setInterval(() => {
            totalSeconds++;
            updateTimerDisplay();
        }, 1000);
    }
});

document.getElementById('pause-timer').addEventListener('click', () => {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    } else {
        timerInterval = setInterval(() => {
            totalSeconds++;
            updateTimerDisplay();
        }, 1000);
    }
});

document.getElementById('stop-timer').addEventListener('click', () => {
    clearInterval(timerInterval);
    timerInterval = null;
    totalSeconds = 0;
    updateTimerDisplay();
    updateTimestamp("Horodatage : Non défini");
    currentQrCode = null;
});