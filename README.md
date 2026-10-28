<div align="center">

# PinDrop

### Save the Pins that inspire you.

A clean, simple web app for downloading publicly accessible Pinterest videos when available.

<p>
  <a href="https://pindrop-0nnk.onrender.com"><img src="https://img.shields.io/badge/🌐_Live_Website-Open_PinDrop-e52d45?style=for-the-badge" alt="Open PinDrop live website"></a>
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-Web%20App-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/yt--dlp-Media%20Extraction-34A853?style=for-the-badge" alt="yt-dlp">
  <img src="https://img.shields.io/badge/License-Not%20Specified-gray?style=for-the-badge" alt="License not specified">
</p>

**Paste a public Pin link. Download the media when supported. No Pinterest login is requested by PinDrop.**

[**🚀 Open PinDrop Website**](https://pindrop-0nnk.onrender.com)

</div>

---

## ✨ Features

- 🔗 Accepts Pinterest links from `pinterest.com` and `pin.it`.
- 🎬 Uses `yt-dlp` to resolve and download media supported by the extractor.
- 📁 Creates a readable filename from the Pin title.
- 📱 Responsive, lightweight web interface.
- 🧹 Removes temporary downloaded files after the response closes.
- 🩺 Includes a simple health endpoint at `/api/health`.

## 🖥️ Tech stack

- Python
- Flask
- yt-dlp
- HTML, CSS and JavaScript
- Gunicorn for production serving

## 🚀 Run locally

1. Clone this repository:

   ```bash
   git clone YOUR_REPOSITORY_URL
   cd pindrop
   ```

   Copy the HTTPS clone URL from your GitHub repository's **Code** button and replace `YOUR_REPOSITORY_URL`.

2. Create and activate a virtual environment:

   **Windows**
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

   **macOS / Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Install FFmpeg and make sure the `ffmpeg` executable is available on your system `PATH` if the selected media format requires merging or post-processing.

5. Start the app:

   ```bash
   python app.py
   ```

6. Open `http://127.0.0.1:5000` in your browser.

## ☁️ Deployment

This project includes a `Procfile` for platforms that support Gunicorn:

```text
web: gunicorn --bind 0.0.0.0:$PORT app:app
```

Set up the service to install dependencies from `requirements.txt`. Confirm the host provides FFmpeg if your chosen formats need it. Free hosting providers may sleep after inactivity, limit runtime, or restrict media downloads.

## 🔌 API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Displays the PinDrop website |
| `GET` | `/api/health` | Simple health check |
| `POST` | `/api/resolve` | Resolves supported Pin information |
| `POST` | `/api/download` | Downloads supported media as an attachment |

Example request body for the POST endpoints:

```json
{
  "url": "https://pin.it/your-public-pin"
}
```

Only use public media you own or have permission to download. Private, deleted, image-only, region-restricted, or unsupported Pins may fail. Availability depends on Pinterest and the `yt-dlp` extractor, and can change over time.

## 🗂️ Project structure

```text
pindrop/
├── app.py
├── requirements.txt
├── Procfile
├── Dockerfile
├── render.yaml
├── templates/
├── static/
│   ├── app.js
│   └── style.css
├── assets/
│   └── pindrop-banner.png
└── README.md
```

## 🛡️ Responsible use

PinDrop is an independent utility and is not affiliated with Pinterest. Respect creators' rights, Pinterest's terms, and applicable laws. Do not use this project to access private content or download media without permission.

## 👋 About

Built as a lightweight project to make saving publicly accessible Pins straightforward.

<div align="center">

**PinDrop · Save what inspires you.**

[🌐 Visit PinDrop](https://pindrop-0nnk.onrender.com)

</div>
