@echo off
REM Build and test script for PDF Outline Extractor (Windows)
REM Adobe India Hackathon Challenge - Project 1A

echo 🚀 Building PDF Outline Extractor
echo ==================================

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found. Please install Docker first.
    exit /b 1
)

REM Build Docker image
echo 🔨 Building Docker image...
docker build --platform=linux/amd64 -t outline-extractor .

if errorlevel 1 (
    echo ❌ Docker build failed
    exit /b 1
)

echo ✅ Docker image built successfully

REM Check image size
echo 📏 Checking image size...
docker images outline-extractor

REM Test the container
echo.
echo 🧪 Testing the container...

REM Check for test files
if not exist "input\*.pdf" (
    echo ⚠️  No test PDFs found in input directory
    echo    Please add PDF files to the input directory for testing
)

REM Run the container
echo 🏃 Running container...
docker run --rm -v "%cd%/input:/app/input" -v "%cd%/output:/app/output" --network none outline-extractor

if errorlevel 1 (
    echo ❌ Container execution failed
    exit /b 1
)

echo ✅ Container executed successfully

REM Check outputs
echo.
echo 📄 Generated outputs:
dir /b output\*.json 2>nul || echo No JSON files generated

echo.
echo 🎉 Build and test complete!
echo Ready for submission to Adobe Hackathon
echo.
echo To run manually:
echo docker run --rm -v "%cd%/input:/app/input" -v "%cd%/output:/app/output" --network none outline-extractor
