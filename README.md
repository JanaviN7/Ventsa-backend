# Vendora 🛍️
### Simple Billing. Smart Business.

> A full-stack mobile-first POS system built for Indian retail vendors — from street shops to growing stores.

![Vendora Banner](public/pwa-512x512.png)

---

## 🚀 Live Demo
🔗 [vendora.lovable.app](https://vendora.lovable.app) 

**Demo Account:**
- Email: `demo@vendora.in`
- Use OTP login — any OTP works on demo

---

## 📱 What is Vendora?

Vendora is a **mobile-first POS and business management app** designed for Indian kirana stores, boutiques, and retail vendors. It replaces paper billing, manual stock tracking, and spreadsheet headaches with a clean, fast, modern app.

---

## ✨ Features

### 🧾 Billing & POS
- Barcode scan or search by product name
- Cart with quantity management
- Cash / UPI / card payment modes
- Instant receipt generation

### 📦 Inventory Management
- Real-time stock tracking
- Inventory logs with IST timestamps
- Analytics — top sellers, dead stock, revenue by category
- Cost price tracking for profit margin calculation

### 👥 Staff Management
- Multi-staff login with store code
- Role-based access (Admin / Cashier)
- Staff-wise sales performance reports

### 📊 Reports & Analytics
- Daily, weekly, monthly sales reports
- Staff leaderboard
- Revenue trends with charts
- Customer ledger (credit/debit tracking)

### 💳 Subscription System
- Free plan — 50 products, 1 staff
- Basic plan — ₹299/mo or ₹2,499/yr
- Razorpay payment integration (ready)
- Plan enforcement with upgrade prompts

### 📲 PWA — Installable App
- Works on Android & iOS like a native app
- Offline-ready with service worker caching
- Install prompt on mobile browsers

---

## 🛠️ Tech Stack

### Frontend
| Tech | Usage |
|------|-------|
| React + TypeScript | UI framework |
| Vite + PWA Plugin | Build tool + installable app |
| Tailwind CSS | Styling |
| Shadcn/UI | Component library |
| Recharts | Analytics charts |
| React Router | Navigation |
| Zustand | State management |

### Backend
| Tech | Usage |
|------|-------|
| FastAPI (Python) | REST API |
| Supabase | PostgreSQL database + auth |
| JWT | Authentication |
| Razorpay | Payment gateway (integration ready) |
| Uvicorn | ASGI server |

---

## 🏗️ Project Structure

```
vendora/
├── frontend/          # React + TypeScript (Lovable)
│   ├── src/
│   │   ├── pages/     # Dashboard, POS, Inventory, Reports...
│   │   ├── components/
│   │   ├── contexts/  # AuthContext
│   │   └── lib/       # api.ts, jwt.ts
│   └── public/        # PWA icons, manifest
│
└── backend/           # FastAPI
    ├── routes_auth.py
    ├── routes_products.py
    ├── routes_sales.py
    ├── routes_staff.py
    ├── routes_inventory.py
    ├── routes_subscription.py
    ├── routes_reports.py
    └── supabase_client.py
```

---

## ⚙️ Setup & Run

### Backend
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/vendora.git
cd vendora/backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Fill in: SUPABASE_URL, SUPABASE_KEY, JWT_SECRET, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

# Run
uvicorn main:app --reload
```

### Frontend
```bash
cd vendora/frontend
npm install
npm run dev
```

---

## 🗄️ Database Schema (Supabase)

Key tables:
- `stores` — store accounts
- `products` — inventory with cost price
- `sales` + `sale_items` — billing records
- `inventory_logs` — stock movement history
- `staff` — staff accounts with roles
- `customers` + `ledger_entries` — customer credit tracking
- `subscriptions` — plan management

---

## 🔑 Environment Variables

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
JWT_SECRET=your_jwt_secret
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

---

## 📸 Screenshots

>

---

## 🗺️ Roadmap

- [ ] Deploy backend to Railway
- [ ] WhatsApp invoice sharing
- [ ] GST invoice generation
- [ ] Multi-store support
- [ ] Android APK via Capacitor

---

## 👩‍💻 Built By

**Janavi Nathwani** — [@your_github](https://github.com/JanaviN7)

Built with ❤️ for Indian retail vendors.

