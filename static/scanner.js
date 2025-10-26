/* scanner.js
   Usage: include this on your scanner.html:
     <script src="/socket.io.js"></script>   // or the loader file above
     <script src="/qrcode.min.js"></script>
     <script src="/scanner.js"></script>

   This script:
   - Starts the camera and uses BarcodeDetector if available
   - Parses QR content: accepts either a JSON payload { "session_id": "..." } or a raw token string
   - Reveals Approve button and sends POST /approve with { session_id }
*/

(function () {
    // Helper to set up UI elements expected by the HTML (ids used in earlier example)
    function $(id) { return document.getElementById(id); }

    // Expose here so other pages can reuse
    window.qrScanner = {
        start: startScanner
    };

    // State
    var sessionID = null;

    // parse QR content
    function parseQR(raw) {
        if (!raw) return null;
        raw = raw.trim();
        // Attempt to parse JSON first
        try {
            var j = JSON.parse(raw);
            if (j && j.session_id) return j.session_id;
        } catch (e) { /* not json */ }

        // If it's a URL, try to read ?session_id= or ?token=
        try {
            var u = new URL(raw);
            var s = u.searchParams.get('session_id') || u.searchParams.get('token');
            if (s) return s;
        } catch (e) { /* not a url */ }

        // fallback: treat raw as token string
        if (raw.length > 0) return raw;
        return null;
    }

    async function postApprove(sid) {
        try {
            var res = await fetch('/approve', {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({ session_id: sid })
            });
            var j = await res.json();
            return { ok: res.ok, data: j };
        } catch (e) {
            return { ok: false, error: e.message || String(e) };
        }
    }

    // UI helper to show token/approve area.
    function showTokenUI(sid) {
        sessionID = sid;
        var display = $('sessionDisplay');
        var btn = $('approveBtn');
        var result = $('result');
        if (display) display.textContent = 'Session: ' + sid;
        if (btn) btn.style.display = 'inline-block';
        if (result) result.textContent = '';
    }

    // wire approve button if present
    function wireApprove() {
        var btn = $('approveBtn');
        if (!btn) return;
        btn.addEventListener('click', async function () {
            if (!sessionID) return alert('No session selected');
            btn.disabled = true;
            var r = await postApprove(sessionID);
            if (r.ok) {
                if ($('result')) $('result').textContent = 'Approved — page should update.';
            } else {
                if ($('result')) $('result').textContent = 'Error: ' + (r.error || JSON.stringify(r.data));
            }
            btn.disabled = false;
        });
    }

    // BarcodeDetector-based scanning
    function startNativeDetector(videoEl, onDetected) {
        if (!('BarcodeDetector' in window)) return false;
        var formats = ['qr_code'];
        try {
            var detector = new BarcodeDetector({ formats: formats });
            (function scanLoop() {
                detector.detect(videoEl).then(function (barcodes) {
                    if (barcodes && barcodes.length) {
                        onDetected(barcodes[0].rawValue);
                        return;
                    }
                    requestAnimationFrame(scanLoop);
                }).catch(function () {
                    // if detection failed, try again
                    requestAnimationFrame(scanLoop);
                });
            })();
            return true;
        } catch (e) {
            console.warn('BarcodeDetector init failed', e);
            return false;
        }
    }

    // Fallback using canvas-frame scanning with a naive approach can be added here
    // but for local-friendly use we prefer BarcodeDetector or manual paste.

    // Start camera and scanning
    async function startScanner(opts) {
        opts = opts || {};
        var video = document.getElementById(opts.videoId || 'video');
        if (!video) {
            console.warn('startScanner: video element not found');
            return;
        }

        wireApprove();

        try {
            var stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            video.srcObject = stream;
            video.play();

            // Wait until video has some data
            await new Promise(function (resolve) {
                video.onloadedmetadata = function () { resolve(); };
            });

            // Try native BarcodeDetector
            var ok = startNativeDetector(video, function (raw) {
                var sid = parseQR(raw);
                if (sid) {
                    showTokenUI(sid);
                } else {
                    console.warn('QR scanned but no session parsed:', raw);
                }
            });

            if (!ok) {
                // No BarcodeDetector: instruct user to paste token or use manual input
                console.warn('BarcodeDetector not available — please paste token manually');
            }

        } catch (e) {
            console.error('camera start failed', e);
            alert('Camera error: ' + (e.message || e));
        }
    }

    // hook manual input and go button if present
    function wireManual() {
        var go = $('go');
        var manual = $('manual');
        if (!go || !manual) return;
        go.addEventListener('click', function () {
            var txt = manual.value && manual.value.trim();
            if (!txt) return;
            var sid = parseQR(txt);
            if (sid) showTokenUI(sid);
            else alert('Could not parse token');
        });
    }

    // auto-run wiring if DOM already loaded
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        wireManual();
        wireApprove();
    } else {
        document.addEventListener('DOMContentLoaded', function () {
            wireManual();
            wireApprove();
        });
    }

    // expose start function on window for manual control
    window.startQrScanner = startScanner;

})();
