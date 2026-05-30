# HealthSaathi — Running the App

## Prerequisites (one-time installs)
- Docker Desktop installed and running
- Flutter SDK installed
- Android phone with USB debugging enabled
- ADB (comes with Android SDK / Flutter)

---

## Every Time You Want to Run the App

Follow these steps in order.

---

### Step 1 — Disable Cloudflare WARP
> Skip this if WARP is already off or not installed.

Find the **WARP icon** in the system tray (bottom-right taskbar) → click it → **Disconnect**.

If you don't do this, Docker will fail to pull images from the internet.

---

### Step 2 — Start Docker Desktop
Open **Docker Desktop** and wait until the status shows **"Engine running"** (whale icon in taskbar turns solid).

---

### Step 3 — Start the Backend + Database

Open a terminal and run:
```
cd "d:\My Workspace\capstone work\Capstone\project\deployment\docker"
docker-compose -f docker-compose.dev.yml up --build
```

Wait until you see this line in the logs:
```
Application startup complete.
```

> First run takes 2-3 minutes to download images and install packages.
> Subsequent runs are much faster (under 30 seconds).

**Leave this terminal open** — closing it stops the backend.

---

### Step 4 — Fix Missing DB Columns (FIRST TIME ONLY)

Only needed the very first time you start the containers. Open a **new terminal** and run:
```
docker exec -it healthsaathi-db-dev psql -U postgres -d healthsaathi_dev -c "ALTER TABLE patients ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP; ALTER TABLE doctors ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP; ALTER TABLE audit_chain ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP; ALTER TABLE anomaly_alerts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
```

You should see `ALTER TABLE` printed four times. Done — never needed again unless you wipe the Docker volumes.

---

### Step 5 — Verify Backend is Working

Open this in your browser: `http://localhost:8000/docs`

You should see the FastAPI Swagger UI. If you see it, the backend is healthy.

---

### Step 6 — Connect Your Phone

1. Plug your phone into the PC via USB
2. When the phone asks **"Allow USB debugging?"** → tap **Allow**
3. In a new terminal, verify the phone is detected:
   ```
   flutter devices
   ```
   You should see **CPH2381** listed.

---

### Step 7 — Set Up ADB Port Forwarding

This makes `localhost:8000` on your phone tunnel to the backend running on your PC.

```
adb reverse tcp:8000 tcp:8000
```

> You need to re-run this every time you reconnect the phone via USB.

---

### Step 8 — Run the Flutter App

```
cd "d:\My Workspace\capstone work\Capstone\project\mobile"
flutter run
```

The app will build and install on your phone automatically. First build takes ~1 minute.

---

## Test Credentials

All passwords are `password123`.

| Role    | Email                            |
|---------|----------------------------------|
| Admin   | admin@healthsaathi.com           |
| Doctor  | rajesh.kumar@healthsaathi.com    |
| Nurse   | anjali@healthsaathi.com          |
| Patient | rahul.verma@example.com          |

---

## Stopping Everything

1. In the Docker terminal → press `Ctrl+C`
2. Then run:
   ```
   docker-compose -f docker-compose.dev.yml down
   ```
3. In the Flutter terminal → press `q`

---

## Common Errors

| Error | Fix |
|-------|-----|
| `failed to resolve source metadata for docker.io` | Disable Cloudflare WARP (Step 1) |
| `column patients.updated_at does not exist` | Run the ALTER TABLE command in Step 4 |
| `WebSocketException: 403` | Re-run `adb reverse tcp:8000 tcp:8000` (Step 7) |
| `No devices found` | Reconnect USB cable and re-enable USB debugging on phone |
| App shows "Unauthorized" after login | Backend is not running — check Step 3 |
