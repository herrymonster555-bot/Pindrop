const input = document.getElementById("pinUrl");
const pasteBtn = document.getElementById("pasteBtn");
const downloadBtn = document.getElementById("downloadBtn");
const actualDownloadBtn = document.getElementById("actualDownloadBtn");
const statusBox = document.getElementById("status");
const resultCard = document.getElementById("result");
const previewImage = document.getElementById("previewImage");
const resultTitle = document.getElementById("resultTitle");
const resultMeta = document.getElementById("resultMeta");
let currentUrl = "";
let busy = false;

document.getElementById("year").textContent = new Date().getFullYear();

function setStatus(message, type = "loading") {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`;
  statusBox.hidden = !message;
}
function setBusy(value) {
  busy = value;
  downloadBtn.disabled = value;
  downloadBtn.innerHTML = value ? '<span class="spinner"></span> Processing…' : '<span class="download-symbol">↓</span> Download';
}
function cleanResult() {
  resultCard.hidden = true;
  previewImage.hidden = true;
  previewImage.removeAttribute("src");
}
async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return await response.json();
  return { ok: false, error: "Unexpected server response. Check that the backend is running." };
}
async function resolvePin() {
  if (busy) return;
  const url = input.value.trim();
  if (!url) {
    cleanResult();
    setStatus("Paste a Pinterest Pin link to get started.", "error");
    input.focus();
    return;
  }
  currentUrl = url;
  cleanResult();
  setBusy(true);
  setStatus("Checking the Pin and looking for supported media…", "loading");
  try {
    const response = await fetch("/api/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });
    const data = await parseResponse(response);
    if (!response.ok || !data.ok) throw new Error(data.error || "Could not resolve this Pin.");
    resultTitle.textContent = data.title || "Pinterest media";
    resultMeta.textContent = data.duration ? `Video · ${Math.round(data.duration)} seconds` : "Media found · Preview details may vary";
    if (data.thumbnail) {
      previewImage.src = data.thumbnail;
      previewImage.hidden = false;
      previewImage.onerror = () => { previewImage.hidden = true; };
    }
    resultCard.hidden = false;
    setStatus("Media found. Use the button below to download it.", "success");
  } catch (error) {
    setStatus(error.message || "Something went wrong. Try another public Pin.", "error");
  } finally {
    setBusy(false);
  }
}
downloadBtn.addEventListener("click", resolvePin);
input.addEventListener("keydown", event => { if (event.key === "Enter") resolvePin(); });
pasteBtn.addEventListener("click", async () => {
  try {
    if (!navigator.clipboard || !navigator.clipboard.readText) throw new Error();
    input.value = await navigator.clipboard.readText();
    input.focus();
    setStatus("Link pasted. Click Download to continue.", "success");
  } catch {
    input.focus();
    setStatus("Clipboard access was blocked. Paste the link using Ctrl+V.", "error");
  }
});
actualDownloadBtn.addEventListener("click", async () => {
  if (!currentUrl || busy) return;
  actualDownloadBtn.disabled = true;
  actualDownloadBtn.textContent = "Preparing download…";
  setStatus("Preparing your file. Please keep this tab open.", "loading");
  try {
    const response = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: currentUrl })
    });
    const type = response.headers.get("content-type") || "";
    if (!response.ok || type.includes("application/json")) {
      const data = type.includes("application/json") ? await response.json() : null;
      throw new Error(data?.error || "Download failed. Try another public Pin.");
    }
    const blob = await response.blob();
    const disposition = response.headers.get("content-disposition") || "";
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : "pinterest-video.mp4";
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objectUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 15000);
    setStatus("Download started. Please respect the creator's rights.", "success");
  } catch (error) {
    setStatus(error.message || "Download failed. Please try another Pin.", "error");
  } finally {
    actualDownloadBtn.disabled = false;
    actualDownloadBtn.innerHTML = 'Download file <span>↓</span>';
  }
});
const menuToggle = document.getElementById("menuToggle");
menuToggle.addEventListener("click", () => {
  const nav = document.querySelector(".desktop-nav");
  const open = nav.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", String(open));
});
document.querySelectorAll(".desktop-nav a").forEach(a => a.addEventListener("click", () => {
  document.querySelector(".desktop-nav").classList.remove("open");
  menuToggle.setAttribute("aria-expanded", "false");
}));
