# Deployment Guide - Permanent Link Access

## Quick Start (Local Access)

### Option 1: Use the Batch File (Windows)
1. Double-click `START_ATTENDANCE_APP.bat` in the project root
2. The server will start and browser will open automatically
3. Access at: http://127.0.0.1:5000

### Option 2: Manual Start
```bash
cd server
python app.py
```
Then open: http://127.0.0.1:5000

---

## Deploy Online (Permanent Public Link)

### Option A: Deploy to Render (Free & Easy)

1. **Create a Render Account**
   - Go to https://render.com
   - Sign up for free

2. **Push Code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

3. **Deploy on Render**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - Name: attendance-ml-app
     - Root Directory: server
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn app:app`
   - Click "Create Web Service"

4. **Your Permanent Link**
   - You'll get: `https://attendance-ml-app.onrender.com`
   - Share this link with anyone!

### Option B: Deploy to Railway (Free)

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Deploy**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Python and deploys
   - Settings:
     - Root Directory: server
     - Start Command: `gunicorn app:app`

3. **Your Permanent Link**
   - You'll get: `https://your-app.railway.app`

### Option C: Deploy to PythonAnywhere (Free)

1. **Create Account**
   - Go to https://www.pythonanywhere.com
   - Sign up for free account

2. **Upload Code**
   - Use "Files" tab to upload your project
   - Or use Git to clone your repository

3. **Configure Web App**
   - Go to "Web" tab
   - Click "Add a new web app"
   - Choose Flask
   - Set working directory to your project
   - Configure WSGI file to point to your app

4. **Your Permanent Link**
   - You'll get: `https://yourusername.pythonanywhere.com`

---

## Environment Variables for Production

Create a `.env` file in server folder:

```env
SECRET_KEY=your-super-secret-production-key-change-this
DATABASE_URI=sqlite:///instance/attendance.db
FLASK_ENV=production
```

---

## Local Network Access (Access from other devices on same WiFi)

1. **Find your local IP address**
   ```bash
   ipconfig  # Windows
   # Look for IPv4 Address (e.g., 192.168.1.100)
   ```

2. **Modify app.py** (temporarily)
   ```python
   if __name__ == '__main__':
       app = create_app()
       app.run(debug=True, host='0.0.0.0', port=5000)
   ```

3. **Access from other devices**
   - On same WiFi: http://192.168.1.100:5000
   - Replace with your actual IP address

---

## Recommended: Deploy to Render

**Why Render?**
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Easy deployment from GitHub
- ✅ Auto-deploys on code changes
- ✅ Permanent public URL

**Steps:**
1. Push code to GitHub
2. Connect to Render
3. Deploy in 5 minutes
4. Get permanent link: `https://your-app.onrender.com`

---

## Security Notes for Production

Before deploying online:

1. **Change SECRET_KEY**
   ```python
   SECRET_KEY=generate-a-strong-random-key-here
   ```

2. **Use Production Database**
   - Consider PostgreSQL instead of SQLite
   - Render provides free PostgreSQL

3. **Disable Debug Mode**
   ```python
   app.run(debug=False)
   ```

4. **Add Authentication**
   - Already implemented with Flask-Login
   - Ensure strong passwords

---

## Quick Comparison

| Method | Permanent Link | Free | Setup Time | Best For |
|--------|---------------|------|------------|----------|
| Batch File | ❌ Local only | ✅ | 1 min | Personal use |
| Render | ✅ Yes | ✅ | 10 min | Public access |
| Railway | ✅ Yes | ✅ | 5 min | Quick deploy |
| PythonAnywhere | ✅ Yes | ✅ | 15 min | Python apps |
| Local Network | ⚠️ WiFi only | ✅ | 2 min | Same network |

---

## Support

For deployment issues:
- Render: https://render.com/docs
- Railway: https://docs.railway.app
- PythonAnywhere: https://help.pythonanywhere.com

---

## Current Status

✅ Project is ready to deploy
✅ All dependencies listed in requirements.txt
✅ Procfile created for deployment
✅ Database configured
✅ Authentication working

**Next Step:** Choose a deployment method above and follow the steps!
