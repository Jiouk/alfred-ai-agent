# 🚀 Deployment Guide - AI Agent SaaS Platform
## Render.com (Ευκολότερο & Δωρεάν)

---

## 📋 Prerequisites

Πριν ξεκινήσεις, χρειάζεσαι:

1. **GitHub Account** (https://github.com/signup)
2. **Render Account** (https://render.com - Sign up with GitHub)
3. **Κώδικας στο GitHub** (θα σου πω πως)

---

## Βήμα 1: Push τον κώδικα στο GitHub (5 λεπτά)

### 1.1 Φτιάξε νέο repository
```bash
# Μπες στο project folder
cd /Users/jarvis/.openclaw/workspace/agents/fullstack-dev/projects/ai-agent-saas

# Αρχικοποίησε git (αν δεν έχει γίνει)
git init

# Πρόσθεσε όλα τα files
git add .

# Commit
git commit -m "Initial commit - AI Agent SaaS Platform MVP"
```

### 1.2 Φτιάξε repo στο GitHub
1. Πήγαινε https://github.com/new
2. Όνομα: `ai-agent-saas`
3. Public ή Private (όπως θες)
4. **Μην** προσθέσεις README/.gitignore (τα έχουμε ήδη)
5. Create repository

### 1.3 Push τον κώδικα
```bash
# Αντικατέστησε YOUR_USERNAME με το δικό σου
git remote add origin https://github.com/YOUR_USERNAME/ai-agent-saas.git

# Push
git branch -M main
git push -u origin main
```

✅ **Ο κώδικας είναι πλέον στο GitHub!**

---

## Βήμα 2: Σύνδεση με Render (3 λεπτά)

### 2.1 Εγγραφή
1. Πήγαινε https://dashboard.render.com
2. Click **"Get Started"** ή **"Sign Up"**
3. Choose **"Sign up with GitHub"**
4. Authorize το Render να έχει access στα repos σου

### 2.2 New Web Service
1. Στο dashboard, click **"New +"** → **"Web Service"**
2. Βρες το `ai-agent-saas` repo σου
3. Click **"Connect"**

---

## Βήμα 3: Configuration (2 λεπτά)

### 3.1 Βασικά settings
| Setting | Value |
|---------|-------|
| **Name** | `ai-agent-saas` (ή ότι θες) |
| **Region** | Frankfurt (EU) |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | `Free` |

### 3.2 Environment Variables
Πρόσθεσε αυτά (κάνε click **"Add Environment Variable"** για κάθε ένα):

```
FERNET_KEY=your-fernet-key-here
ADMIN_API_KEY=your-admin-key-here
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./ai_agent_saas.db
OPENCLAW_API_URL=http://localhost:11434
ENVIRONMENT=production
DEBUG=false
```

**⚠️ Σημαντικό:** Άλλαξε τα keys! Μην χρησιμοποιήσεις αυτά που σου έδωσα. Φτιάξε τυχαία:
```bash
# Για macOS - τρέξε αυτό στο terminal:
openssl rand -hex 32
```

### 3.3 Create Web Service
Click **"Create Web Service"**

---

## Βήμα 4: Περίμενε το deploy (2-5 λεπτά)

Θα δεις logs στο Render dashboard:
```
==> Building service...
==> Running build command...
==> Deploying...
==> Your service is live 🎉
```

✅ **Το app είναι live!**

---

## Βήμα 5: Test το deployment

### 5.1 Βρες το URL
Στο Render dashboard, θα δεις κάτι σαν:
```
https://ai-agent-saas-xxx.onrender.com
```

### 5.2 Test στο browser
```
https://ai-agent-saas-xxx.onrender.com/docs
```

Θα δεις το **FastAPI Swagger UI** — σημαίνει ότι δουλεύει! 🎉

### 5.3 Test API
```bash
# Health check
curl https://ai-agent-saas-xxx.onrender.com/health

# Θα δεις: {"status":"ok"}
```

---

## 📊 Σύνολο: ~10-15 λεπτά

---

## 🔧 Troubleshooting

### ❌ "Build failed"
**Λύση:** Έλεγξε τα logs στο Render. Συνήθως είναι:
- Λάθος στο requirements.txt → κάνε push ξανά
- Python version → άλλαξε σε Python 3.11

### ❌ "Application error"
**Λύση:** Έλεγξε environment variables. Πρέπει να έχεις:
- `FERNET_KEY` (32 bytes hex)
- `ADMIN_API_KEY`
- `SECRET_KEY`

### ❌ Το URL δεν ανοίγει
**Λύση:** Το free tier "κοιμάται" μετά 15 λεπτά αδράνειας. Περίμενε 30 δευτερόλεπτα να ξυπνήσει.

---

## 🔄 Updates

Όταν κάνεις αλλαγές στον κώδικα:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

Το Render **αυτόματα** κάνει redeploy! 🚀

---

## 🎉 Congratulations!

Το AI Agent SaaS Platform είναι πλέον live και προσβάσιμο από οπουδήποτε!

**Next steps:**
- 🔗 Σύνδεσε custom domain (προαιρετικό)
- 💳 Πρόσθεσε Stripe keys για real payments
- 🤖 Σύνδεσε Telegram bot

---

**Χρειάζεσαι βοήθεια με κάποιο βήμα;** 
