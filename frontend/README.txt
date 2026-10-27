CAREGAP-AI FRONTEND DROP-IN FILES
=================================
1. Ensure Vite React project exists at D:\Caregap AI\frontend and dependencies installed:
   npm install react-router-dom axios recharts lucide-react tailwindcss @tailwindcss/vite
2. Copy vite.config.js to frontend\vite.config.js
3. Copy src\App.jsx, src\api.js, src\index.css, src\main.jsx into frontend\src\
4. Start backend in another terminal:
   cd /d "D:\Caregap AI"
   .venv\Scripts\activate
   python -m uvicorn backend.app.main:app --reload --port 8000
5. Start frontend:
   cd /d "D:\Caregap AI\frontend"
   npm run dev
6. Open http://localhost:5173

This UI uses a Vite /api proxy to 127.0.0.1:8000, so no backend CORS changes are needed in local development.
Existing hospital accounts and organizations are required. Registration/organization creation are accessible via Swagger /docs.
The AI demo is trained on synthetic data and is not clinically validated.
The frontend stores the bearer token in sessionStorage for this demo; production auth requires hardened session handling.

If login fails with 422, the client retries as form-urlencoded username/password.
If organizations have a different response shape than an array/items/organizations, adjust extractItems() in src/api.js.
