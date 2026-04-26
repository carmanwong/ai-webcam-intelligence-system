const http = require("http");
const fs = require("fs");
const path = require("path");

const CLIPS_DIR = process.env.HMT_CLIPS_DIR || "/tmp/hmt/clips";
const PORT = Number.parseInt(process.env.HMT_GALLERY_PORT || "4320", 10);
const ACTIVE_CLIP_HIDE_MS = Number.parseInt(process.env.HMT_ACTIVE_CLIP_HIDE_MS || "15000", 10) || 15000;

function shouldHideActiveClip(stats) {
  return Date.now() - stats.mtimeMs < ACTIVE_CLIP_HIDE_MS;
}

function serveVideo(req, res, filePath) {
  if (!fs.existsSync(filePath)) {
    res.writeHead(404);
    res.end("Video not found");
    return;
  }

  const stats = fs.statSync(filePath);
  const totalSize = stats.size;
  const range = req.headers.range;
  const baseHeaders = {
    "Content-Type": "video/mp4",
    "Accept-Ranges": "bytes",
    "Content-Length": totalSize
  };

  if (req.method === "HEAD" && !range) {
    res.writeHead(200, baseHeaders);
    res.end();
    return;
  }

  if (!range) {
    res.writeHead(200, baseHeaders);
    fs.createReadStream(filePath).pipe(res);
    return;
  }

  const matched = range.match(/bytes=(\d*)-(\d*)/u);
  if (!matched) {
    res.writeHead(416, { "Content-Range": `bytes */${totalSize}` });
    res.end();
    return;
  }

  let start = matched[1] ? Number.parseInt(matched[1], 10) : 0;
  let end = matched[2] ? Number.parseInt(matched[2], 10) : totalSize - 1;

  if (!Number.isFinite(start) || start < 0) start = 0;
  if (!Number.isFinite(end) || end >= totalSize) end = totalSize - 1;
  if (start > end || start >= totalSize) {
    res.writeHead(416, { "Content-Range": `bytes */${totalSize}` });
    res.end();
    return;
  }

  const chunkSize = end - start + 1;
  const headers = {
    "Content-Type": "video/mp4",
    "Accept-Ranges": "bytes",
    "Content-Length": chunkSize,
    "Content-Range": `bytes ${start}-${end}/${totalSize}`
  };

  res.writeHead(206, headers);
  if (req.method === "HEAD") {
    res.end();
    return;
  }
  fs.createReadStream(filePath, { start, end }).pipe(res);
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  
  if (url.pathname === "/api/videos") {
    try {
      const requestedType = String(url.searchParams.get("type") || "continuous").trim().toLowerCase();
      const files = fs.readdirSync(CLIPS_DIR)
        .filter(f => f.endsWith(".mp4"))
        .filter((fileName) => {
          const isMotionFile = fileName.startsWith("MOTION_");
          if (requestedType === "motion") return isMotionFile;
          return !isMotionFile;
        })
        .map((fileName) => {
          const stats = fs.statSync(path.join(CLIPS_DIR, fileName));
          return { fileName, stats };
        })
        .filter(({ stats }) => !shouldHideActiveClip(stats))
        .map(({ fileName, stats }) => {
          return { name: fileName, time: stats.mtime, size: (stats.size / 1024 / 1024).toFixed(2) + "MB" };
        })
        .sort((a, b) => b.time - a.time);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(files));
    } catch (e) {
      res.writeHead(500); res.end(e.message);
    }
    return;
  }

  if (url.pathname.startsWith("/stream/")) {
    const filename = decodeURIComponent(url.pathname.replace("/stream/", ""));
    const filePath = path.join(CLIPS_DIR, filename);
    serveVideo(req, res, filePath);
    return;
  }

  let filePath = path.join(__dirname, url.pathname === "/" ? "index.html" : url.pathname);
  if (fs.existsSync(filePath)) {
    const ext = path.extname(filePath);
    const types = { ".html": "text/html", ".css": "text/css", ".js": "application/javascript" };
    res.writeHead(200, { "Content-Type": types[ext] || "text/plain" });
    fs.createReadStream(filePath).pipe(res);
  } else { res.writeHead(404); res.end("Not Found"); }
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`🎬 HMT Gallery FIXED on port ${PORT} (clips: ${CLIPS_DIR})`);
});
