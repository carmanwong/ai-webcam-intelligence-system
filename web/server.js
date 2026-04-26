const http = require("http");
const fs = require("fs");
const path = require("path");

const CLIPS_DIR = "/home/ubuntu/clips";
const PORT = 4319;

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  
  if (url.pathname === "/api/videos") {
    try {
      const files = fs.readdirSync(CLIPS_DIR)
        .filter(f => f.endsWith(".mp4"))
        .map(f => {
          const stats = fs.statSync(path.join(CLIPS_DIR, f));
          return { name: f, time: stats.mtime, size: (stats.size / 1024 / 1024).toFixed(2) + "MB" };
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
    if (fs.existsSync(filePath)) {
      res.writeHead(200, { "Content-Type": "video/mp4" });
      fs.createReadStream(filePath).pipe(res);
    } else {
      res.writeHead(404); res.end("Video not found");
    }
    return;
  }

  let filePath = path.join(__dirname, url.pathname === "/" ? "index.html" : url.pathname);
  if (fs.existsSync(filePath)) {
    const ext = path.extname(filePath);
    const types = { ".html": "text/html", ".css": "text/css", ".js": "application/javascript" };
    res.writeHead(200, { "Content-Type": types[ext] || "text/plain" });
    fs.createReadStream(filePath).pipe(res);
  } else {
    res.writeHead(404); res.end("Not Found");
  }
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`🎬 HMT Gallery running on port ${PORT}`);
});
