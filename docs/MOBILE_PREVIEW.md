# WZOS mobile preview

Open http://127.0.0.1:8083/__simulator while the local server is running.

## Start / stop on Windows
From the owned integration-release checkout, run:

```powershell
& .\scripts\start_mobile_preview.ps1
```

This starts the server in a hidden background process, checks readiness and saves process/log details in ignored `.local-data/mobile-simulator/server-8083.json`. It reuses an already-ready simulator and refuses to stop unrelated listeners. It needs to be started again after Windows restarts.

To stop this simulator safely:

```powershell
& .\scripts\start_mobile_preview.ps1 -Stop
```

Use `-Port 8081` if 8083 is occupied by another known application, and change the URL accordingly. The stop action verifies the saved process belongs to this launcher. No Windows startup task or background monitor is installed.

For foreground troubleshooting:

```powershell
& "C:/Users/MolecularDev/Documents/ChatGPT/Enterprise Gemma v2/.venv/Scripts/python.exe" scripts/run_mobile_preview.py --port 8083
```

## Controls
- Android, large Android, compact phone, iPhone-sized layout and tablet presets.
- Custom CSS width/height, Rotate and Fit to window.
- Disabling Fit displays the app at full scale; scroll the preview to inspect it.
- Resizing and rotating preserve the loaded app. Reload app intentionally reloads WZOS.
- Use Test identity inside WZOS to switch Core/Enterprise and admin/member synthetic users.
- This is the actual local app in an iframe with real responsive breakpoints. It does not emulate Safari, Android, device sensors, a mobile keyboard or installation. These still require real-device checks.

## Isolation
This standalone developer server binds only 127.0.0.1 and rejects non-loopback clients and external Host names. The factory creates synthetic SQLite records in ignored .local-data/mobile-simulator, using the existing preview account modes. It refuses cloud runtime markers. No production credentials or hosted database are needed.
The harness alone changes the local app root's frame policy to same-origin so it can appear inside the simulator. All other application routes retain their original frame policy. The simulator itself refuses framing. The production application factory and security middleware are unchanged. Never deploy this launcher.

## October 18 validation
Four ASGI boundary/asset/cloud-refusal tests and two screen-control tests PASS. Browser verified actual WZOS iframe loading and portrait/landscape rotation. The preview exposed an existing dashboard CSS specificity problem; the more-specific guided-content grid rule now selects one column on phones. Final screenshot/mobile click automation was blocked by repeated browser-control timeouts. Do not claim those final checks passed.
The live site has not changed. No PostgreSQL schema, IAM, provider or native-app provisioning changes.

## Background-launch repair
The original execution session ended and the preview was unavailable. Added start_mobile_preview.ps1 and restarted a hidden background server. The launcher completed with SIMULATOR_READY; a separate command confirmed HTTP200 from /__simulator and /, with SAMEORIGIN framing on the app. Browser-control URL security policy blocked the visual check; no alternate browser surface or screenshot workaround was used. User must refresh the existing tab to confirm visual loading. Production unchanged.
