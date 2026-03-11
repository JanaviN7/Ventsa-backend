# Vendora 🛍️
### Simple Billing. Smart Business.

> A full-stack mobile-first POS system built for Indian retail vendors — from street shops to growing stores.
<img width="192" height="192" alt="pwa-192x192" src="https://github.com/user-attachments/assets/33133b9c-6d0c-4dce-9929-57b1140aaff4" />

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

> <img width="661" height="455" alt="image" src="https://github.com/user-attachments/assets/db174f6c-e809-4a5e-a9a6-b1b60d80db4c" />
> <img width="661" height="499" alt="image" src="https://github.com/user-attachments/assets/d0bbf2b5-2a25-4378-bb70-7f1cdc754008" />
> <img width="224" height="526" alt="image" src="https://github.com/user-attachments/assets/687bd80f-37f5-433b-83b5-115450ba4191" />
> <img width="226" height="529" alt="image" src="https://github.com/user-attachments/assets/92de32f2-e108-464f-9832-2374e5002b16" />
> <img width="225" height="528" alt="image" src="https://github.com/user-attachments/assets/9d58692a-7c9d-4ec0-b65d-465ca7355abe" />
> <img width="220" height="522" alt="image" src="https://github.com/user-attachments/assets/b9474efb-4d28-4b9a-8d85-201848c0401d" />
> <img width="226" height="522" alt="image" src="https://github.com/user-attachments/assets/23028897-1538-4d5d-8632-62d92982d46d" />




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

