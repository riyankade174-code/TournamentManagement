const express = require("express");
const bcrypt = require("bcryptjs");
const db = require("../db");

const router = express.Router();

router.post("/login", (req, res) => {
  const { email, password } = req.body || {};
  if (!email || !password) {
    return res.status(400).json({ error: "Email and password are required." });
  }
  const admin = db.prepare("SELECT * FROM admin WHERE email = ?").get(email);
  if (!admin || !bcrypt.compareSync(password, admin.password)) {
    return res.status(401).json({ error: "Incorrect email or password." });
  }
  req.session.adminId = admin.admin_id;
  res.json({ admin_id: admin.admin_id, name: admin.name, email: admin.email });
});

router.post("/logout", (req, res) => {
  req.session.destroy(() => res.json({ ok: true }));
});

router.get("/me", (req, res) => {
  if (!req.session.adminId) return res.status(401).json({ error: "Not logged in." });
  const admin = db
    .prepare("SELECT admin_id, name, email FROM admin WHERE admin_id = ?")
    .get(req.session.adminId);
  res.json(admin);
});

module.exports = router;
