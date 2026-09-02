const path = require("path");
const express = require("express");
const session = require("express-session");

require("./db"); // ensures schema + default admin exist before routes load

const app = express();

app.use(express.json());
app.use(
  session({
    secret: "tms-dev-secret-change-me",
    resave: false,
    saveUninitialized: false,
    cookie: { maxAge: 1000 * 60 * 60 * 8 }, // 8 hours
  })
);

app.use("/api/auth", require("./routes/auth"));
app.use("/api/tournaments", require("./routes/tournaments"));
app.use("/api/teams", require("./routes/teams"));
app.use("/api/players", require("./routes/players"));
app.use("/api/matches", require("./routes/matches"));
app.use("/api/results", require("./routes/results"));
app.use("/api/points", require("./routes/points"));

app.use(express.static(path.join(__dirname, "public")));

app.get("/admin", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "admin.html"));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Tournament Management System running at http://localhost:${PORT}`);
});
