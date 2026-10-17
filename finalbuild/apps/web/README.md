# AI Car Scanner Web PWA

A responsive, mobile-first browser companion for AI Car Scanner. It supports a local vehicle garage, diagnostic-code notes, English/Armenian UI, API reachability checks, and installability on iPhone through Safari.

## Deploy on Render (free static site)

A root-level `render.yaml` is included. From an iPhone:

1. Open https://dashboard.render.com and sign in.
2. Choose **New → Blueprint**.
3. Connect the private GitHub repository `Grigor1995/AI-CAR-SCANER` (authorize Render to access this repo if asked).
4. Select the `main` branch and create/deploy the Blueprint.
5. Wait for Render to finish, then open the generated `*.onrender.com` URL.

If you use **New → Static Site** instead, choose branch `main`, leave the build command as `echo "Static PWA - no build step required"`, and set the publish directory to `finalbuild/apps/web`.

## Add to iPhone Home Screen

1. Open the deployed site in **Safari** (not an in-app browser).
2. Tap **Share** → **Add to Home Screen**.
3. Enable **Open as Web App** if that option appears, then tap **Add**.

## Important limitations

- Vehicle and DTC notes are saved in browser storage on this device; they are not synced to the backend.
- The web app does not currently connect to an OBD adapter or read live vehicle data/codes.
- The backend check only tests whether the configured API's OpenAPI endpoint can be reached from the browser. CORS/network settings may prevent the browser check even when the server itself is running.
- Do not enter passwords, API keys, or other secrets in this UI.
