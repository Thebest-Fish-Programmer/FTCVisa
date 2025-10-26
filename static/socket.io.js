/* socket.io.js — small loader that tries to use the server-provided
   /socket.io/socket.io.js path (Flask-SocketIO serves this), with CDN fallback.
   Usage in HTML: <script src="/socket.io/socket.io.js"></script>
   But if you prefer a file to drop in static/, include this file instead.
*/
(function () {
    if (window.io && typeof window.io === 'function') return;

    var primary = '/socket.io/socket.io.js'; // when server serves it (recommended)
    var fallback = 'https://cdn.jsdelivr.net/npm/socket.io-client@4.7.2/dist/socket.io.min.js';

    function load(src, cb) {
        var s = document.createElement('script');
        s.src = src;
        s.async = true;
        s.onload = function () { cb(null); };
        s.onerror = function () { cb(new Error('failed to load ' + src)); };
        document.head.appendChild(s);
    }

    load(primary, function (err) {
        if (!err && window.io) {
            console.log('Loaded socket.io client from server path:', primary);
            return;
        }
        // try fallback CDN
        load(fallback, function (err2) {
            if (err2) {
                console.error('Failed to load socket.io client from server and CDN', err2);
            } else {
                console.log('Loaded socket.io client from CDN');
            }
        });
    });
})();
