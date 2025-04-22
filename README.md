# IFC Conversational AI

A powerful chatbot application that allows users to interact with IFC (Industry Foundation Classes) files using natural language. The application consists of a FastAPI backend and a React frontend.

## Table of Contents

1. [Overview](#overview)
2. [Technical Documentation](#technical-documentation)
3. [Setup Instructions](#setup-instructions)
4. [Source Code Documentation](#source-code-documentation)
5. [Sample Outputs](#sample-outputs)
6. [Troubleshooting](#troubleshooting)

## Overview

IFC Conversational AI is a web application that enables users to upload IFC files and ask questions about them in natural language. The application uses Google's Gemini AI model to analyze the IFC file and provide intelligent responses to user queries.

### Key Features

- Upload and process IFC files
- Ask questions about the IFC file in natural language
- Receive intelligent responses based on the file content
- Modern, responsive UI with real-time feedback
- Error handling and user-friendly messages

## Technical Documentation

### Architecture

The application follows a client-server architecture:

1. **Frontend**: React-based single-page application
   - Handles user interactions
   - Manages file uploads
   - Displays chat interface
   - Communicates with backend API

2. **Backend**: FastAPI-based REST API
   - Processes file uploads
   - Integrates with Google Gemini AI
   - Analyzes IFC files
   - Generates responses to user queries

### Technology Stack

- **Frontend**:
  - React.js
  - React Icons
  - CSS for styling

- **Backend**:
  - FastAPI
  - Uvicorn (ASGI server)
  - Google Generative AI (Gemini)
  - IFC OpenShell (for IFC file processing)
  - Python Multipart (for file uploads)

### Data Flow

1. User uploads an IFC file through the frontend
2. File is sent to the backend and stored
3. User asks a question about the file
4. Backend processes the question and file using Gemini AI
5. Response is sent back to the frontend and displayed to the user

### Error Handling

The application implements comprehensive error handling:

- Frontend displays user-friendly error messages
- Backend provides detailed error responses
- Retry mechanisms for API calls
- Graceful degradation when services are unavailable

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn
- Google API key for Gemini AI

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up your Google API key:
   - Create a `.env` file in the backend directory
   - Add your API key:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

6. Start the backend server:
   ```bash
   python -m uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

## Source Code Documentation

### Backend Structure

```
backend/
├── main.py                 # Main application entry point
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── routes/                 # API route handlers
│   ├── __init__.py
│   ├── health_routes.py    # Health check endpoints
│   ├── query_routes.py     # Query processing endpoints
│   └── upload_routes.py    # File upload endpoints
├── services/               # Business logic
│   ├── __init__.py
│   ├── gemini_service.py   # Gemini AI integration
│   └── ifc_service.py      # IFC file processing
├── models/                 # Data models
│   ├── __init__.py
│   ├── query.py            # Query request/response models
│   └── upload.py           # Upload request/response models
└── utils/                  # Utility functions
    ├── __init__.py
    └── error_handling.py   # Error handling utilities
```

### Frontend Structure

```
frontend/
├── public/                 # Static files
├── src/                    # Source code
│   ├── App.js              # Main application component
│   ├── index.js            # Application entry point
│   ├── index.css           # Global styles
│   └── components/         # React components
├── package.json            # Node.js dependencies
└── .gitignore              # Git ignore file
```

### Key Components

#### Backend

1. **main.py**
   - Initializes FastAPI application
   - Configures CORS middleware
   - Includes API routers
   - Sets up error handlers

2. **routes/query_routes.py**
   - Handles user queries
   - Processes IFC files
   - Integrates with Gemini AI
   - Returns responses to the frontend

3. **services/gemini_service.py**
   - Manages communication with Google Gemini AI
   - Formats prompts for the AI model
   - Handles API rate limits and errors

#### Frontend

1. **App.js**
   - Main application component
   - Manages application state
   - Handles file uploads
   - Displays chat interface
   - Communicates with backend API

## Sample Outputs

### File Upload

When a user successfully uploads an IFC file, they will see:

```
File "example.ifc" uploaded successfully. You can now ask questions about this IFC file.
```

### Sample Questions and Responses

#### Question: "What is the total area of the building?"

**Response:**
```
The total area of the building is approximately 2,500 square meters. This includes all floors and spaces within the building envelope.
```

#### Question: "How many doors are in the building?"

**Response:**
```
There are 42 doors in the building. This includes:
- 12 exterior doors
- 30 interior doors
- 8 fire-rated doors
```

#### Question: "What materials are used for the walls?"

**Response:**
```
The walls in this building are constructed using the following materials:
- Exterior walls: Reinforced concrete with thermal insulation
- Interior walls: Gypsum board on metal studs
- Fire walls: Concrete block with fire rating
```

## Troubleshooting

### Common Issues

1. **API Connection Error**
   - Ensure the backend server is running
   - Check that the API_BASE_URL in App.js is correct
   - Verify network connectivity

2. **File Upload Failures**
   - Ensure the file is a valid IFC file
   - Check file size (should be under 10MB)
   - Verify CORS settings if uploading from a different domain

3. **Gemini AI Quota Exceeded**
   - The free tier of Gemini AI has a daily request limit
   - Consider upgrading to a paid plan for higher quotas
   - Implement caching to reduce API calls

### Getting Help

If you encounter issues not covered in this documentation:

1. Check the application logs for detailed error messages
2. Review the FastAPI documentation at https://fastapi.tiangolo.com/
3. Review the React documentation at https://reactjs.org/
4. Review the Google Generative AI documentation at https://ai.google.dev/

---

© 2023 IFC Conversational AI. All rights reserved. 