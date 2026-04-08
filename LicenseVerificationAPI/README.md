# License Verification API

An Express.js REST API that verifies driver's licenses against a MySQL database.

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Configuration

The `.env` file is already configured with the database credentials:

- Host: `mysqldb-striverdileep-df7e.d.aivencloud.com`
- Port: `25359`
- User: `avnadmin`
- Database: `defaultdb`
- SSL: Required (CA certificate included in `ca.pem`)

### 3. Database Prerequisites

Ensure the database has a `licenses` table with the following columns:

- `LicenseNumber` (VARCHAR or TEXT) - Primary identifier
- `Name` (VARCHAR or TEXT)
- `DOB` (VARCHAR or TEXT in DD/MM/YYYY format)
- `ExpiryDate` (VARCHAR or TEXT in DD/MM/YYYY format)

### 4. Run the API

**Production:**

```bash
npm start
```

**Development (with auto-reload):**

```bash
npm run dev
```

The API will start on `http://localhost:5000`

## API Endpoints

### POST /verify-license

Verifies a driver's license against the database by License Number.

**Method:** POST  
**Status Codes:** 200 (Success), 400 (Bad Request), 500 (Server Error)

#### Request Input Parameters

| Parameter     | Type   | Required | Format | Description                                |
| ------------- | ------ | -------- | ------ | ------------------------------------------ |
| LicenseNumber | String | Yes      | Text   | Unique identifier for the driver's license |

#### Response Output

| Field         | Type    | Description                                               |
| ------------- | ------- | --------------------------------------------------------- |
| success       | Boolean | True if verification passed, false otherwise              |
| message       | String  | Descriptive message about the verification result         |
| license_valid | Boolean | True if license details are valid and found in database   |
| is_expired    | Boolean | True if license has expired (null if unable to determine) |
| image         | String  | Optional. Base64 encoded image data (data URI format)     |

**Request:**

```json
{
  "LicenseNumber": "DL001"
}
```

**Response (Success - Not Expired):**

```json
{
  "success": true,
  "message": "License verified successfully",
  "license_valid": true,
  "is_expired": false,
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Response (Expired):**

```json
{
  "success": false,
  "message": "License expired on 14/03/2025",
  "license_valid": true,
  "is_expired": true
}
```

**Response (Not Found):**

```json
{
  "success": false,
  "message": "License not found in database: DL001",
  "license_valid": false,
  "is_expired": null
}
```

**Response (Invalid Request):**

```json
{
  "success": false,
  "message": "LicenseNumber field is required",
  "license_valid": false,
  "is_expired": null
}
```

### POST /admin/upload

Uploads a new driver's license with photo to the database.

**Method:** POST  
**Content-Type:** multipart/form-data  
**Status Codes:** 201 (Created), 400 (Bad Request), 500 (Server Error)

#### Request Parameters

| Parameter     | Type   | Required | Format     | Description                                |
| ------------- | ------ | -------- | ---------- | ------------------------------------------ |
| LicenseNumber | String | Yes      | Text       | Unique identifier for the driver's license |
| Name          | String | Yes      | Text       | Full name of the license holder            |
| DOB           | String | Yes      | DD/MM/YYYY | Date of birth                              |
| ExpiryDate    | String | Yes      | DD/MM/YYYY | License expiry date                        |
| PhotoImage    | File   | Yes      | Image      | License photo (JPEG, PNG, GIF, WebP)       |

**Max File Size:** 10MB

#### Response Output

| Field              | Type    | Description                                    |
| ------------------ | ------- | ---------------------------------------------- |
| success            | Boolean | True if upload was successful, false otherwise |
| message            | String  | Descriptive message about the upload result    |
| data               | Object  | Upload details (returned on success)           |
| data.LicenseNumber | String  | The uploaded license number                    |
| data.Name          | String  | The uploaded license holder name               |
| data.DOB           | String  | The uploaded date of birth                     |
| data.ExpiryDate    | String  | The uploaded expiry date                       |
| data.imageSize     | Number  | Size of the uploaded image in bytes            |

**Request Example (using cURL):**

```bash
curl -X POST http://localhost:5000/admin/upload \
  -F "LicenseNumber=DL001" \
  -F "Name=John Doe" \
  -F "DOB=15/03/1990" \
  -F "ExpiryDate=14/03/2030" \
  -F "PhotoImage=@/path/to/photo.jpg"
```

**Response (Success):**

```json
{
  "success": true,
  "message": "License for John Doe (DL001) uploaded successfully",
  "data": {
    "LicenseNumber": "DL001",
    "Name": "John Doe",
    "DOB": "15/03/1990",
    "ExpiryDate": "14/03/2030",
    "imageSize": 45678
  }
}
```

**Response (Missing Fields):**

```json
{
  "success": false,
  "message": "All fields (LicenseNumber, Name, DOB, ExpiryDate) are required"
}
```

**Response (No Image File):**

```json
{
  "success": false,
  "message": "PhotoImage file is required"
}
```

### GET /health

Health check endpoint that verifies API and database connectivity.

**Method:** GET  
**Status Codes:** 200 (OK), 503 (Service Unavailable)

#### Response Output

| Field    | Type   | Description                                               |
| -------- | ------ | --------------------------------------------------------- |
| status   | String | API status: "OK" or "ERROR"                               |
| message  | String | Descriptive message                                       |
| database | String | Database connection status: "Connected" or "Disconnected" |
| error    | String | Error message (only on failure)                           |

**Response (Success):**

```json
{
  "status": "OK",
  "message": "License Verification API is running",
  "database": "Connected"
}
```

**Response (Failure):**

```json
{
  "status": "ERROR",
  "message": "License Verification API is down",
  "database": "Disconnected",
  "error": "Connection refused"
}
```

### GET /

API documentation and endpoint listing endpoint.

**Method:** GET  
**Status Code:** 200

#### Response Output

| Field     | Type   | Description         |
| --------- | ------ | ------------------- |
| name      | String | API name            |
| version   | String | API version         |
| endpoints | Object | Available endpoints |

**Response:**

```json
{
  "name": "License Verification API",
  "version": "1.0.0",
  "endpoints": {
    "POST /verify-license": "Verify a driver's license",
    "POST /admin/upload": "Upload a new license with photo",
    "GET /health": "Health check",
    "GET /": "API documentation"
  }
}
```

## Testing

### Verify License Endpoint

#### Using cURL

```bash
curl -X POST http://localhost:5000/verify-license \
  -H "Content-Type: application/json" \
  -d '{
    "LicenseNumber": "DL001"
  }'
```

#### Using cURL (with verbose output):

```bash
curl -X POST http://localhost:5000/verify-license \
  -H "Content-Type: application/json" \
  -d '{"LicenseNumber": "DL001"}' \
  -v
```

### Admin Upload Endpoint

#### Using cURL

```bash
curl -X POST http://localhost:5000/admin/upload \
  -F "LicenseNumber=DL001" \
  -F "Name=John Doe" \
  -F "DOB=15/03/1990" \
  -F "ExpiryDate=14/03/2030" \
  -F "PhotoImage=@/path/to/photo.jpg"
```

### Using Postman

**For /verify-license:**

1. Create a new POST request to `http://localhost:5000/verify-license`
2. Set header: `Content-Type: application/json`
3. Add request body: `{"LicenseNumber": "DL001"}`
4. Send request

**For /admin/upload:**

1. Create a new POST request to `http://localhost:5000/admin/upload`
2. Select "Body" → "form-data"
3. Add the following key-value pairs:
   - `LicenseNumber`: DL001
   - `Name`: John Doe
   - `DOB`: 15/03/1990
   - `ExpiryDate`: 14/03/2030
   - `PhotoImage`: Select your image file (type: File)
4. Send request

### Using Node.js/JavaScript (Verify License)

```javascript
const axios = require("axios");

const licenseData = {
  LicenseNumber: "DL001",
};

axios
  .post("http://localhost:5000/verify-license", licenseData)
  .then((response) => console.log(response.data))
  .catch((error) => console.error(error.response?.data || error.message));
```

### Using Node.js/JavaScript (Admin Upload)

```javascript
const axios = require("axios");
const FormData = require("form-data");
const fs = require("fs");

const form = new FormData();
form.append("LicenseNumber", "DL001");
form.append("Name", "John Doe");
form.append("DOB", "15/03/1990");
form.append("ExpiryDate", "14/03/2030");
form.append("PhotoImage", fs.createReadStream("/path/to/photo.jpg"));

axios
  .post("http://localhost:5000/admin/upload", form, {
    headers: form.getHeaders(),
  })
  .then((response) => console.log(response.data))
  .catch((error) => console.error(error.response?.data || error.message));
```

### Using Python (Verify License)

```python
import requests

license_data = {
    "LicenseNumber": "DL001"
}

response = requests.post(
    'http://localhost:5000/verify-license',
    json=license_data
)
print(response.json())
```

### Using Python (Admin Upload)

```python
import requests

files = {
    'PhotoImage': open('/path/to/photo.jpg', 'rb')
}

data = {
    'LicenseNumber': 'DL001',
    'Name': 'John Doe',
    'DOB': '15/03/1990',
    'ExpiryDate': '14/03/2030'
}

response = requests.post(
    'http://localhost:5000/admin/upload',
    files=files,
    data=data
)
print(response.json())
```

## HTTP Status Codes

| Code | Status              | Description                                        |
| ---- | ------------------- | -------------------------------------------------- |
| 200  | OK                  | Request successful (GET /health, GET /)            |
| 201  | Created             | Resource created successfully (POST /admin/upload) |
| 400  | Bad Request         | Invalid request format or missing required fields  |
| 404  | Not Found           | Endpoint does not exist                            |
| 500  | Server Error        | Internal server error                              |
| 503  | Service Unavailable | Database connection failed (GET /health)           |

## Error Handling

All error responses follow a consistent JSON format:

```json
{
  "success": false,
  "message": "Descriptive error message",
  "license_valid": false,
  "is_expired": null
}
```

**Common Error Scenarios:**

- Missing LicenseNumber: Returns 400 with message "LicenseNumber field is required"
- Invalid date format: Returns 400 with message about expected DD/MM/YYYY format
- License not found: Returns 400 with message "License not found in database: [LicenseNumber]"
- Database error: Returns 500 with database error details
- Missing required upload fields: Returns 400 with specific field requirements
- Invalid image file: Returns 400 with message about allowed formats

## Features

- ✅ Express.js REST API
- ✅ Connects to remote MySQL database with SSL
- ✅ Verifies license data against database records
- ✅ Checks license expiry date (DD/MM/YYYY format)
- ✅ Returns detailed verification status
- ✅ Error handling and input validation
- ✅ Health check endpoint
- ✅ Environment variable configuration (.env)
- ✅ Connection pooling for better performance
- ✅ Admin portal for uploading licenses with photos
- ✅ Image upload with drag-and-drop support
- ✅ Material UI-based admin interface

## Admin Portal

The License Verification API includes an admin portal for uploading new driver's licenses with photos. The portal provides a Material UI-based interface for easy data entry and image upload.

### Access the Admin Portal

Navigate to: **`http://localhost:5000/admin/`**

### License Upload Methods

#### 1. Through Admin Portal UI

- Navigate to `http://localhost:5000/admin/`
- Fill in the form with license details
- Upload an image using click or drag-and-drop
- Submit the form

#### 2. Direct API Endpoint

- Use the **POST /admin/upload** endpoint
- Send multipart form data with all required fields
- Returns HTTP 201 on success

### Admin Portal Features

#### ✅ License Upload Form

- **License Number**: Unique identifier for the license
- **Full Name**: Name of the license holder
- **Date of Birth**: Selected via date picker (auto-formatted to DD/MM/YYYY)
- **Expiry Date**: Selected via date picker (auto-formatted to DD/MM/YYYY)
- **Photo/Image**: Upload any image file

#### 📸 Image Upload Methods

1. **Click to Upload**: Click the upload area to select a file
2. **Drag & Drop**: Drag image files directly into the upload area
3. **Supported Formats**: JPEG, PNG, GIF, WebP
4. **Max Size**: 10MB

#### ✨ Real-time Features

- **Image Preview**: See uploaded image before submitting
- **Validation**: Server-side and client-side validation of all fields
- **Loading State**: Visual feedback during upload
- **Success Message**: Displays uploaded license details
- **Error Handling**: Clear error messages for validation failures

### Admin Portal Database Requirements

The `licenses` table must include:

- `PhotoImage` (LONGBLOB) - Stores binary image data

**Example CREATE TABLE:**

```sql
CREATE TABLE licenses (
  LicenseNumber VARCHAR(50) PRIMARY KEY,
  Name VARCHAR(100) NOT NULL,
  DOB VARCHAR(10) NOT NULL,
  ExpiryDate VARCHAR(10) NOT NULL,
  PhotoImage LONGBLOB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Project Structure

```
LicenseVerificationAPI/
├── app.js                 # Main Express.js application
├── db.js                  # Database configuration
├── .env                   # Environment variables (database credentials)
├── ca.pem                 # SSL certificate for database connection
├── package.json           # Node.js dependencies and scripts
├── public/
│   └── admin/
│       └── index.html     # Admin portal interface
└── README.md              # This file
```

## Notes

- All dates must be in `DD/MM/YYYY` format
- License names are compared case-insensitively
- SSL certificate (`ca.pem`) is required for secure database connection
- The API uses connection pooling for efficient database access
- Response status codes: 200 (success), 400 (validation error), 500 (server error)

## Troubleshooting

**Database Connection Error:**

- Verify `.env` file has correct credentials
- Check if `ca.pem` file exists in the project root
- Ensure database host is accessible from your network

**Certificate Error:**

- Make sure `ca.pem` is in the root directory
- Path in `.env` should be `./ca.pem`

**Port Already in Use:**

- Change PORT in `.env` or pass it as environment variable: `PORT=3000 npm start`
