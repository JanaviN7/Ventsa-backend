# Ventsa 🛍️
### Simple Billing. Smart Business.

> A full-stack mobile-first POS and business management SaaS built for Indian retail vendors — kirana stores, boutiques, and small shops.


<img width="1024" height="1024" alt="pwa-192x192" src="https://github.com/user-attachments/assets/fe4c0fb7-7311-4599-9f18-62d3fe643843" />

🔗 **Live App:** [ventsa.lovable.app](https://ventsa.lovable.app)

---

## 📱 What is Ventsa?

Ventsa is a **mobile-first POS and business management app** designed for Indian kirana stores, boutiques, and retail vendors. It replaces paper billing, manual stock tracking, and spreadsheet headaches with a clean, fast, modern app that works right from your phone.

---

## ✨ Features

### 🧾 Billing & POS
- Barcode scan or search by product name
- Cart with quantity management
- Per-item discount % + total bill discount
- Cash / UPI / Card split payment modes
- PDF A4 invoice + 80mm thermal receipt generation

### 📦 Inventory Management
- Real-time stock tracking
- Inventory logs with IST timestamps
- Analytics — top sellers, dead stock, revenue by category
- Cost price tracking for profit margin calculation
- Soft delete for products

### 👥 Staff Management
- Multi-staff login with store code
- Role-based access (Admin / Cashier)
- Staff-wise sales performance leaderboard

### 📊 Reports & Analytics
- Daily, weekly, monthly sales reports
- Revenue trends with charts
- Customer ledger — credit/dues tracking per customer

### 💳 Subscription System
- **Free Plan** — 50 products, 1 staff member
- **Basic Plan** — ₹299/mo or ₹2,499/yr — unlimited products, staff, ledger, reports, invoices
- Razorpay payment gateway (live, verified)
- Plan enforcement on every API route

### 📲 PWA — Installable App
- Works on Android & iOS like a native app
- Install prompt on mobile browsers
- OTP-based authentication via email (Brevo)

---

## 🛠️ Tech Stack

### Frontend
| Tech | Usage |
|------|-------|
| React + TypeScript | UI framework |
| Vite + PWA Plugin | Build tool + installable app |
| Tailwind CSS + Shadcn/UI | Styling + components |
| Recharts | Analytics charts |
| React Router | Navigation |

### Backend
| Tech | Usage |
|------|-------|
| FastAPI (Python) | REST API |
| Supabase (PostgreSQL) | Database |
| JWT | Authentication |
| Razorpay | Payment gateway |
| Brevo | Transactional OTP emails |
| Docker + Railway | Containerization + deployment |

---

## 🏗️ Project Structure

```
ventsa/
├── frontend/               # React + TypeScript (Lovable)
│   ├── src/
│   │   ├── pages/          # Dashboard, POS, Inventory, Reports...
│   │   ├── components/
│   │   ├── contexts/       # AuthContext, SubscriptionContext
│   │   └── lib/            # api.ts, config.ts
│   └── public/             # PWA icons, manifest.json
│
└── backend/                # FastAPI (Railway)
    ├── main.py
    ├── config.py
    ├── routes_auth.py       # OTP email via Brevo
    ├── routes_products.py   # Inventory + barcode scan
    ├── routes_sales.py      # Billing + split payments
    ├── routes_staff.py      # Staff management
    ├── routes_inventory.py  # Analytics
    ├── routes_subscription.py  # Plan enforcement
    ├── routes_invoice.py    # PDF + thermal receipt
    ├── routes_reports.py    # Sales reports
    └── supabase_client.py
```

---

## ⚙️ Setup & Run

### Backend
```bash
git clone https://github.com/JanaviN7/Ventsa-backend.git
cd Ventsa-backend

pip install -r requirements.txt

cp .env.example .env
# Fill in your values — see Environment Variables below

uvicorn main:app --reload
```

### Frontend
```bash
git clone https://github.com/JanaviN7/ventsa-frontend.git
cd ventsa-frontend

npm install
npm run dev
```

---

## 🔑 Environment Variables

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
JWT_SECRET=your_jwt_secret
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
BREVO_API_KEY=...
BREVO_SENDER_EMAIL=hello.ventsa@gmail.com
```

---

## 🗄️ Database Schema (Supabase)

Key tables:
- `stores` — store accounts + store codes
- `store_users` — staff with roles (admin/cashier)
- `products` — inventory with cost price + barcode
- `sales` + `sale_items` — billing records with IST timestamps
- `inventory_logs` — stock movement history
- `customers` + `ledger_entries` — customer credit tracking
- `subscriptions` — plan management
- `otp_codes` — OTP-based auth
- `invoice_counters` — sequential invoice numbering

---

## 📸 Screenshots

> Dashboard · POS Billing · Analytics · Customer Ledger · Invoice

*(Add screenshots here)*

---

## 🗺️ Roadmap

- [x] OTP-based auth with JWT
- [x] POS billing with barcode scan
- [x] Split payments (Cash/UPI/Card)
- [x] Inventory analytics + profit margins
- [x] Customer ledger
- [x] PDF invoice + thermal receipt
- [x] Razorpay subscription gateway
- [x] Docker + Railway deployment
- [x] Brevo transactional email
- [ ] Barcode camera scan (frontend — @zxing/browser)
- [ ] WhatsApp invoice sharing
- [ ] GST invoice generation
- [ ] Voice billing (Pro plan)
- [ ] Multi-store support

---

## 👩‍💻 Built By

**Janavi Nathwani**
- 📧 janavi.nathwani9@gmail.com
- 🔗 [linkedin.com/in/Janavi-Nathwani](https://linkedin.com/in/Janavi-Nathwani)
- 🐙 [github.com/JanaviN7](https://github.com/JanaviN7)

Built with ❤️ for Indian retail vendors.
