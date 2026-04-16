const qrReader = document.getElementById("qr-reader");
const video = document.getElementById("camera-preview");
const assetIdInput = document.getElementById("asset_id");
const statusBox = document.getElementById("scanner-status");
const startButton = document.getElementById("start-scan");
const stopButton = document.getElementById("stop-scan");

let stream = null;
let animationFrameId = null;
let detector = null;
let html5QrScanner = null;
let activeScannerMode = null;

function setStatus(message) {
    if (statusBox) {
        statusBox.textContent = message;
    }
}

async function stopCamera() {
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }

    if (activeScannerMode === "html5" && html5QrScanner) {
        try {
            await html5QrScanner.stop();
        } catch (error) {
            // Ignore stop errors when the camera was never fully started.
        }

        try {
            await html5QrScanner.clear();
        } catch (error) {
            // Ignore clear errors and continue resetting the page state.
        }
    }

    if (video) {
        video.pause();
        video.srcObject = null;
    }

    if (stream) {
        stream.getTracks().forEach((track) => track.stop());
        stream = null;
    }

    if (qrReader) {
        qrReader.innerHTML = "";
    }

    html5QrScanner = null;
    detector = null;
    activeScannerMode = null;
    setStatus("Camera stopped.");
}

async function scanFrame() {
    if (!video || !detector || video.readyState < 2) {
        animationFrameId = requestAnimationFrame(scanFrame);
        return;
    }

    try {
        const barcodes = await detector.detect(video);
        if (barcodes.length > 0) {
            const qrValue = (barcodes[0].rawValue || "").trim();
            if (qrValue) {
                assetIdInput.value = qrValue.toUpperCase();
                setStatus(`QR code found: ${assetIdInput.value}`);
                await stopCamera();
                return;
            }
        }
    } catch (error) {
        setStatus("The browser could not read the camera stream.");
        await stopCamera();
        return;
    }

    animationFrameId = requestAnimationFrame(scanFrame);
}

async function startBarcodeDetectorCamera() {
    try {
        activeScannerMode = "barcode-detector";
        detector = new BarcodeDetector({ formats: ["qr_code"] });
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: "environment" },
            },
            audio: false,
        });

        video.srcObject = stream;
        await video.play();
        setStatus("Point the camera at a QR code.");
        animationFrameId = requestAnimationFrame(scanFrame);
    } catch (error) {
        setStatus("Camera access failed. Allow camera permission or enter the asset ID manually.");
    }
}

async function startHtml5QrCamera() {
    if (!qrReader || typeof Html5Qrcode === "undefined") {
        return false;
    }

    try {
        activeScannerMode = "html5";
        html5QrScanner = new Html5Qrcode("qr-reader");
        await html5QrScanner.start(
            { facingMode: "environment" },
            {
                fps: 10,
                qrbox: { width: 240, height: 240 },
                aspectRatio: 1.2,
            },
            async (decodedText) => {
                const qrValue = (decodedText || "").trim().toUpperCase();
                if (!qrValue) {
                    return;
                }

                assetIdInput.value = qrValue;
                setStatus(`QR code found: ${qrValue}`);
                await stopCamera();
            },
            () => {}
        );

        setStatus("Point the camera at a QR code.");
        return true;
    } catch (error) {
        if (qrReader) {
            qrReader.innerHTML = "";
        }
        html5QrScanner = null;
        activeScannerMode = null;
        return false;
    }
}

async function startCamera() {
    if (activeScannerMode) {
        await stopCamera();
    }

    const startedWithHtml5 = await startHtml5QrCamera();
    if (startedWithHtml5) {
        return;
    }

    if ("BarcodeDetector" in window) {
        await startBarcodeDetectorCamera();
        return;
    }

    setStatus("Camera scanning is not available in this browser right now. Enter the asset ID manually.");
}

if (startButton) {
    startButton.addEventListener("click", startCamera);
}

if (stopButton) {
    stopButton.addEventListener("click", () => {
        stopCamera();
    });
}

window.addEventListener("beforeunload", () => {
    stopCamera();
});
