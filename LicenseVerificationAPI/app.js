/**
 * License Verification API
 * Express.js REST API for verifying driver's licenses against a MySQL database
 */

const express = require("express");
const mysql = require("mysql2/promise");
const fs = require("fs");
const path = require("path");
const multer = require("multer");
const cors = require("cors");
require("dotenv").config();

const pool = mysql.createPool({
  host: process.env.DB_HOST,
  port: Number(process.env.DB_PORT),
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  ssl: {
    ca: fs.readFileSync(
      path.resolve(process.env.DB_SSL_CA || "./ca.pem"),
      "utf-8",
    ),
    rejectUnauthorized: false,
  },
});

const app = express();

// Middleware
app.use(express.json());
app.use(cors());
app.use(express.static(path.join(__dirname, "public")));

// Multer configuration for image uploads
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
  fileFilter: (req, file, cb) => {
    const allowedMimes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error("Only image files are allowed (JPEG, PNG, GIF, WebP)"));
    }
  },
});

const DB_TABLE = process.env.DB_TABLE || "licenses";

/**
 * Create a database connection pool
 */

/**
 * Validate license number input
 */
function validateLicenseNumber(licenseNumber) {
  if (!licenseNumber || String(licenseNumber).trim() === "") {
    return { valid: false, error: "LicenseNumber is required" };
  }
  return { valid: true };
}

/**
 * Parse and validate expiry date (DD/MM/YYYY format)
 */
function parseExpiryDate(dateStr) {
  const dateRegex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
  const match = dateStr.trim().match(dateRegex);

  if (!match) {
    return {
      valid: false,
      error: `Invalid expiry date format. Expected DD/MM/YYYY, got: ${dateStr}`,
    };
  }

  const [, day, month, year] = match;
  const date = new Date(year, month - 1, day);

  if (
    date.getDate() !== parseInt(day) ||
    date.getMonth() !== parseInt(month) - 1
  ) {
    return { valid: false, error: `Invalid date values: ${dateStr}` };
  }

  return { valid: true, date };
}

/**
 * Check if license is expired
 */
function isLicenseExpired(expiryDate) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return expiryDate < today;
}

/**
 * Verify license from database using only LicenseNumber
 */
async function verifyLicenseFromDB(licenseNumber) {
  try {
    // Validate input
    const validation = validateLicenseNumber(licenseNumber);
    if (!validation.valid) {
      return {
        success: false,
        message: validation.error,
        license_valid: false,
        is_expired: null,
      };
    }

    // Query database to fetch all license details including image
    const connection = await pool.getConnection();

    const query = `
      SELECT LicenseNumber, Name, DOB, ExpiryDate, PhotoImage
      FROM ${DB_TABLE} 
      WHERE LicenseNumber = ?
    `;

    const [rows] = await connection.execute(query, [licenseNumber]);
    connection.release();

    // License not found
    if (rows.length === 0) {
      return {
        success: false,
        message: `License not found in database: ${licenseNumber}`,
        license_valid: false,
        is_expired: null,
      };
    }

    const dbLicense = rows[0];

    // Parse and validate expiry date from database
    const expiryParsed = parseExpiryDate(dbLicense.ExpiryDate);
    if (!expiryParsed.valid) {
      return {
        success: false,
        message: expiryParsed.error,
        license_valid: false,
        is_expired: null,
      };
    }

    const expiryDate = expiryParsed.date;
    const expired = isLicenseExpired(expiryDate);

    // Prepare base response
    const response = {
      success: false,
      message: "",
      license_valid: false,
      is_expired: expired,
    };

    // Check if expired
    if (expired) {
      response.success = false;
      response.message = `License expired on ${expiryDate.toLocaleDateString("en-GB")}`;
      response.license_valid = true;
      response.is_expired = true;
      return response;
    }

    // License is valid and not expired
    response.success = true;
    response.message = "License verified successfully";
    response.license_valid = true;
    response.is_expired = false;

    // Add image as base64 if available and license is valid
    if (dbLicense.PhotoImage) {
      const imageBuffer = Buffer.from(dbLicense.PhotoImage);
      const base64Image = imageBuffer.toString("base64");
      // Assuming JPEG format, adjust MIME type if needed (jpeg, png, etc.)
      response.image = `data:image/jpeg;base64,${base64Image}`;
    }

    return response;
  } catch (error) {
    console.error("❌ Database Error:", error);
    return {
      success: false,
      message: `Database error: ${error.message}`,
      license_valid: false,
      is_expired: null,
    };
  }
}

/**
 * POST /verify-license
 * Verify a driver's license using LicenseNumber only
 */
app.post("/verify-license", async (req, res) => {
  try {
    if (!req.body || typeof req.body !== "object") {
      return res.status(400).json({
        success: false,
        message:
          "Invalid request format. Expected JSON object with LicenseNumber",
        license_valid: false,
        is_expired: null,
      });
    }

    const { LicenseNumber } = req.body;

    if (!LicenseNumber) {
      return res.status(400).json({
        success: false,
        message: "LicenseNumber field is required",
        license_valid: false,
        is_expired: null,
      });
    }

    const result = await verifyLicenseFromDB(LicenseNumber);
    const statusCode = result.success ? 200 : 400;
    return res.status(statusCode).json(result);
  } catch (error) {
    console.error("❌ API Error:", error);
    return res.status(500).json({
      success: false,
      message: `API error: ${error.message}`,
      license_valid: false,
      is_expired: null,
    });
  }
});

/**
 * POST /admin/upload
 * Upload a new license with photo
 */
app.post("/admin/upload", upload.single("PhotoImage"), async (req, res) => {
  try {
    // Validate required fields
    const { LicenseNumber, Name, DOB, ExpiryDate } = req.body;

    if (!LicenseNumber || !Name || !DOB || !ExpiryDate) {
      return res.status(400).json({
        success: false,
        message:
          "All fields (LicenseNumber, Name, DOB, ExpiryDate) are required",
      });
    }

    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "PhotoImage file is required",
      });
    }

    // Validate date format
    const dateRegex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
    const match = ExpiryDate.trim().match(dateRegex);

    if (!match) {
      return res.status(400).json({
        success: false,
        message: `Invalid expiry date format. Expected DD/MM/YYYY, got: ${ExpiryDate}`,
      });
    }

    const [, day, month, year] = match;
    const date = new Date(year, month - 1, day);

    if (
      date.getDate() !== parseInt(day) ||
      date.getMonth() !== parseInt(month) - 1
    ) {
      return res.status(400).json({
        success: false,
        message: `Invalid date values: ${ExpiryDate}`,
      });
    }

    // Insert into database
    const connection = await pool.getConnection();

    const query = `
      INSERT INTO ${DB_TABLE} (LicenseNumber, Name, DOB, ExpiryDate, PhotoImage)
      VALUES (?, ?, ?, ?, ?)
    `;

    await connection.execute(query, [
      LicenseNumber.trim(),
      Name.trim(),
      DOB.trim(),
      ExpiryDate.trim(),
      req.file.buffer,
    ]);

    connection.release();

    res.status(201).json({
      success: true,
      message: `License for ${Name} (${LicenseNumber}) uploaded successfully`,
      data: {
        LicenseNumber,
        Name,
        DOB,
        ExpiryDate,
        imageSize: req.file.size,
      },
    });
  } catch (error) {
    console.error("❌ Upload Error:", error);
    res.status(500).json({
      success: false,
      message: `Upload error: ${error.message}`,
    });
  }
});

/**
 * GET /health
 * Health check endpoint - pings database
 */
app.get("/health", async (req, res) => {
  try {
    // Attempt to get a connection from the pool to verify database connectivity
    const connection = await pool.getConnection();
    await connection.ping();
    connection.release();

    res.status(200).json({
      status: "OK",
      message: "License Verification API is running",
      database: "Connected",
    });
  } catch (error) {
    console.error("❌ Health Check Error:", error);
    res.status(503).json({
      status: "ERROR",
      message: "License Verification API is down",
      database: "Disconnected",
      error: error.message,
    });
  }
});

/**
 * GET /
 * API documentation endpoint
 */
app.get("/", (req, res) => {
  res.status(200).json({
    name: "License Verification API",
    version: "1.0.0",
    endpoints: {
      "POST /verify-license": "Verify a driver's license",
      "GET /health": "Health check",
      "GET /": "API documentation",
    },
  });
});

/**
 * Error handling middleware
 */
app.use((err, req, res, next) => {
  console.error("❌ Unhandled Error:", err);
  res.status(500).json({
    success: false,
    message: "Internal server error",
    error: process.env.NODE_ENV === "development" ? err.message : undefined,
  });
});

/**
 * 404 handler
 */
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: "Endpoint not found",
  });
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(
    `🚀 License Verification API is running on http://localhost:${PORT}`,
  );
  console.log(`📚 API Documentation: http://localhost:${PORT}/`);
});

module.exports = app;
