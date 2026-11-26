// Static server that behaves like GitHub Pages for this check: gzip for text, byte ranges for video.
const http = require('http'), fs = require('fs'), path = require('path'), zlib = require('zlib');
const root = process.argv[2], port = Number(process.argv[3] || 8766);
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.mp4': 'video/mp4', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ico': 'image/x-icon', '.txt': 'text/plain' };
const cache = {};
http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]); if (p.endsWith('/')) p += 'index.html';
  const f = path.join(root, path.normalize(p));
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('not found'); }
  const ext = path.extname(f), type = types[ext] || 'application/octet-stream';
  const stat = fs.statSync(f);
  const text = /html|javascript|css|json|svg|plain/.test(type);
  if (text && /gzip/.test(req.headers['accept-encoding'] || '')) {
    const key = f + ':' + stat.mtimeMs;  // a rebuilt file is compressed again
    const buf = cache[key] || (cache[key] = zlib.gzipSync(fs.readFileSync(f)));
    res.writeHead(200, { 'content-type': type, 'content-encoding': 'gzip', 'content-length': buf.length, 'cache-control': 'max-age=600' });
    return res.end(buf);
  }
  const range = req.headers.range && /bytes=(\d+)-(\d*)/.exec(req.headers.range);
  if (range) {
    const s = Number(range[1]), e = range[2] ? Number(range[2]) : stat.size - 1;
    res.writeHead(206, { 'content-type': type, 'content-range': `bytes ${s}-${e}/${stat.size}`, 'accept-ranges': 'bytes', 'content-length': e - s + 1 });
    return fs.createReadStream(f, { start: s, end: e }).pipe(res);
  }
  res.writeHead(200, { 'content-type': type, 'content-length': stat.size, 'accept-ranges': 'bytes', 'cache-control': 'max-age=600' });
  fs.createReadStream(f).pipe(res);
}).listen(port, () => console.log('serving', root, 'on', port));
