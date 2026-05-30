# Testing Deployment Guide: Complete End-to-End Steps

Complete step-by-step guide to deploy HealthSaathi for testing with team members. This covers Render backend deployment + Flutter APK distribution.

**Total Time: 30 minutes**

---

## Phase 1: Prerequisites (5 minutes)

### Checklist Before Starting:

- [ ] Backend code pushed to GitHub (with .env in .gitignore)
- [ ] Neon database connection verified locally
- [ ] Backend runs successfully locally: `python run.py`
- [ ] Flutter app builds locally: `flutter run`
- [ ] Team members ready to test (have their phones)

### Required Accounts:

- [ ] GitHub account (for Render to access code)
- [ ] Render.com account (free, takes 2 minutes)
- [ ] Google Drive account (for sharing APK)

---

## Phase 2: Deploy Backend to Render (10 minutes)

### Step 1: Prepare Environment Variables

**On your computer:**

```bash
# Generate a strong SECRET_KEY for production
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copy the output** - you'll paste it to Render.

**Example output:**
```
2xJ8_K9pL5qM3nR8sT2vW1xY4zAbCdEfGhIjKlMn
```

### Step 2: Create GitHub Repository (if not done)

```bash
cd d:\My\ Workspace\Capstone\project\backend

# Initialize git and push to GitHub
git init
git add .
git commit -m "HealthSaathi backend for testing deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/healthsaathi-backend.git
git push -u origin main
```

**Replace:**
- `YOUR_USERNAME` with your GitHub username
- Create the repo on GitHub first if needed

### Step 3: Deploy to Render

1. **Go to:** https://render.com
2. **Sign up** (free account, 2 minutes)
3. **Click:** "New +" → "Web Service"
4. **Connect GitHub:**
   - Click "Connect GitHub account"
   - Select your `healthsaathi-backend` repository
   - Click "Connect"

5. **Configure Service:**
   - **Name:** `healthsaathi-backend`
   - **Environment:** Select "Python 3"
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run.py`
   - **Instance Type:** Free (sufficient for testing)

6. **Add Environment Variables:**
   - Click "Environment" tab
   - Add these variables:

```
DATABASE_URL: postgresql://user:password@your-neon-host:5432/your-db
  (Copy from your .env file)

SECRET_KEY: 2xJ8_K9pL5qM3nR8sT2vW1xY4zAbCdEfGhIjKlMn
  (Paste the generated SECRET_KEY from Step 1)

DEBUG: false

APP_ENV: production
```

7. **Deploy:**
   - Click "Create Web Service"
   - Wait 3-5 minutes for deployment
   - You'll see: "Your service is live" with a URL

**Your backend URL will be:**
```
https://healthsaathi-backend.render.com
```

### Step 4: Verify Backend is Running

```bash
# Test the backend
curl https://healthsaathi-backend.render.com/api/docs

# Should respond with Swagger UI
```

Or open in browser: `https://healthsaathi-backend.render.com/api/docs`

**Status: ✅ Backend is live!**

---

## Phase 3: Configure & Build Flutter APK (10 minutes)

### Step 1: Update Backend URL in Flutter

**File:** `d:\My Workspace\Capstone\project\mobile\lib\config\app_config.dart`

(Or find where your API base URL is configured)

```dart
// BEFORE (local):
static const String apiBaseUrl = 'http://localhost:8000';

// AFTER (production):
static const String apiBaseUrl = 'https://healthsaathi-backend.render.com';
```

**Save the file.**

### Step 2: Verify Flutter Configuration

```bash
cd d:\My\ Workspace\Capstone\project\mobile

# Check Flutter is installed
flutter --version

# Get dependencies
flutter pub get
```

### Step 3: Build Release APK

```bash
# Build the release APK
flutter build apk --release

# Command output will show:
# Building APK...
# Built build/app/outputs/flutter-apk/app-release.apk (XX MB)
```

**The APK is created at:**
```
build/app/outputs/flutter-apk/app-release.apk
```

### Step 4: Verify APK Size

```bash
# Check APK file size
dir "build\app\outputs\flutter-apk\app-release.apk"

# Typical size: 50-80 MB
# This includes all code, assets, dependencies
```

**Status: ✅ APK is ready!**

---

## Phase 4: Share APK with Team (5 minutes)

### Option A: Google Drive (Recommended)

1. **Upload APK:**
   - Go to Google Drive: https://drive.google.com
   - Click "New" → "File upload"
   - Select: `build/app/outputs/flutter-apk/app-release.apk`
   - Upload

2. **Get shareable link:**
   - Right-click the uploaded APK
   - Click "Share"
   - Change to "Anyone with the link" can view
   - Copy the link

3. **Share with team:**
```
Download HealthSaathi APK:
[Paste Google Drive link here]

Installation instructions below 👇
```

### Option B: GitHub Releases

```bash
cd d:\My\ Workspace\Capstone\project\backend

# Tag your release
git tag -a v1.0-testing -m "Testing deployment"
git push origin v1.0-testing

# Go to GitHub repo → Releases
# Create release → Upload app-release.apk
# Users download from releases page
```

### Option C: Direct File Transfer

- Email the APK (if team is small, ~60MB max email size)
- Use WhatsApp/Telegram file sharing
- USB drive for in-person handoff

---

## Phase 5: Team Member Installation (3 minutes per user)

### Send This Guide to Team:

```
═══════════════════════════════════════════════════
     HEALTHSAATHI APP - Installation Guide
═══════════════════════════════════════════════════

STEP 1: Download the APK
  1. Click the link provided above
  2. Download the file (50-80 MB)

STEP 2: Enable Unknown Sources (First time only)
  1. Go to Settings
  2. Look for "Security" or "App & notifications"
  3. Find "Unknown sources" or "Install from unknown sources"
  4. Toggle it ON
  5. (Note: This is safe, your phone will verify the app)

STEP 3: Install the App
  1. Open Downloads folder in Files/File Manager
  2. Find: app-release.apk
  3. Tap the APK file
  4. Tap "Install" when prompted
  5. Wait 30 seconds for installation

STEP 4: Open the App
  1. You'll see "HealthSaathi" app in your apps
  2. Tap to open
  3. Login with your credentials

TROUBLESHOOTING:

If you see "Installation blocked":
  - Tap "More details"
  - Tap "Install anyway"
  - This is because it's not from Google Play (which is fine for testing)

If "Unknown sources" toggle is missing:
  - Try Settings → Apps & notifications → Advanced
  - Or Settings → Privacy & security
  - Different phones have different menu structures

If app won't start after install:
  - Force close: Settings → Apps → HealthSaathi → Force stop
  - Try opening again

If login doesn't work:
  - Check your internet connection
  - Make sure you're using correct credentials
  - Contact the developer

═══════════════════════════════════════════════════
```

---

## Phase 6: Testing Checklist

### Before Users Start Testing:

- [ ] Backend is live on Render
- [ ] Backend URL in Flutter config is: `https://healthsaathi-backend.render.com`
- [ ] APK is built and signed
- [ ] APK shared with team members
- [ ] Installation instructions sent

### Team Members Should Test:

- [ ] App downloads and installs successfully
- [ ] App opens without crashing
- [ ] Login works with test credentials
- [ ] Can view appointments
- [ ] Can book appointments
- [ ] Queue updates in real-time (WebSocket)
- [ ] Medical records display
- [ ] User profile loads
- [ ] Logout works

### Test Credentials (If Available):

```
Username: test.user@example.com
Password: [from your test data]

(Or use any user created in database setup)
```

---

## Phase 7: Troubleshooting & Monitoring

### Backend Issues:

**Backend not responding:**
```bash
# Check Render logs:
# Go to Render.com → healthsaathi-backend service
# View logs, look for errors

# Common issues:
1. DATABASE_URL incorrect
   → Verify in Render environment variables
   
2. SECRET_KEY missing
   → Add to Render environment variables
   
3. Requirements not installed
   → Check build logs in Render console
```

**Database connection fails:**
```bash
# Verify Neon database is accessible:
# Test from your local machine
python backend/test_db_connection.py

# If fails locally, fix locally first
# Then redeploy to Render (push to GitHub)
```

### Flutter App Issues:

**App crashes on startup:**
- Check Render backend is live
- Verify API URL is correct in Flutter
- Check backend logs for errors

**Login doesn't work:**
- Backend database might not have users
- Run: `python backend/load_test_data.py`
- Redeploy backend on Render
- Tell users to update APK

**Real-time queue not updating:**
- Check WebSocket support enabled on Render ✅ (included)
- Backend might not be responding
- Restart the app

### Quick Fixes:

```bash
# 1. If something is wrong, redeploy backend:
cd backend
git add .
git commit -m "Fix issue"
git push  # This auto-redeploys on Render

# 2. If Flutter needs changes:
flutter build apk --release
# Update APK on Google Drive
# Users download and reinstall new APK

# 3. To see backend logs:
# Render.com → healthsaathi-backend → Logs tab
```

---

## Complete Timeline Summary

```
START → 5 min (Prerequisites)
     → 10 min (Render deployment)
     → 10 min (Flutter config & build)
     → 5 min (Share APK)
     → 3 min per user (Installation)
DONE ✅

Team can start testing within 30 minutes total!
```

---

## Quick Reference: URLs & Commands

### Render Dashboard:
```
https://render.com
Backend service: healthsaathi-backend
Status: Should say "Live"
```

### Backend Endpoints:

```
API Docs:     https://healthsaathi-backend.render.com/api/docs
API Health:   https://healthsaathi-backend.render.com/api/health
WebSocket QS: wss://healthsaathi-backend.render.com/ws/queue
```

### Flutter Build:
```bash
flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk
```

### Test Backend Connection (Local):
```bash
cd backend
python -c "from app.db.database import engine; engine.connect(); print('✅ Connected')"
```

---

## Success Indicators ✅

**Backend Deployment:**
- [ ] Render shows "Your service is live"
- [ ] Can access https://healthsaathi-backend.render.com/api/docs
- [ ] No errors in Render logs

**Flutter App:**
- [ ] APK builds without errors
- [ ] APK file exists in `build/app/outputs/flutter-apk/`
- [ ] APK is > 40MB (contains all code)

**Team Testing:**
- [ ] Users can download APK
- [ ] Users can install APK
- [ ] Users can login
- [ ] Users can use all features
- [ ] No console errors

**Final Result:**
```
Your complete infrastructure is live:
✅ Backend → Render.com (https://healthsaathi-backend.render.com)
✅ Database → Neon (managed cloud)
✅ Mobile → Users' Android phones (via APK)
✅ Cost → $0/month completely free
```

---

## Next Steps After Testing

1. **Collect Feedback:** Ask users what works/what needs fixing
2. **Make Changes:** Update code, push to GitHub
3. **Redeploy:** Changes auto-deploy on Render
4. **Update APK:** Build new flutter apk, share updated APK
5. **Iterate:** Repeat until ready for production

---

## Support & Documentation

**If something goes wrong:**
- Check logs: Render dashboard → Logs
- Check Flutter errors: Run `flutter run` locally to see detailed errors
- Verify database: `python backend/test_db_connection.py`
- Review: `2_BACKEND_SETUP.md` and `3_DATABASE_SETUP.md`

**For more info on:**
- **Backend setup:** See `2_BACKEND_SETUP.md`
- **Database:** See `3_DATABASE_SETUP.md`
- **API endpoints:** See `4_API_DOCUMENTATION.md`
- **Flutter:** See `6_MOBILE_APP.md`

---

**Last Updated:** April 18, 2026
**Status:** Ready for testing deployment
