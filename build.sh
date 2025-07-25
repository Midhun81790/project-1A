#!/bin/bash
# Build and test script for PDF Outline Extractor
# Adobe India Hackathon Challenge - Project 1A

echo "🚀 Building PDF Outline Extractor"
echo "=================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Build Docker image
echo "🔨 Building Docker image..."
docker build --platform=linux/amd64 -t outline-extractor .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully"

# Check image size
echo "📏 Checking image size..."
docker images outline-extractor --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Test the container
echo ""
echo "🧪 Testing the container..."

# Create test input if needed
if [ ! -f "input/sample.pdf" ]; then
    echo "⚠️  No test PDFs found in input directory"
    echo "   Please add PDF files to the input directory for testing"
fi

# Run the container
echo "🏃 Running container..."
docker run --rm \
    -v "$(pwd)/input:/app/input" \
    -v "$(pwd)/output:/app/output" \
    --network none \
    outline-extractor

if [ $? -eq 0 ]; then
    echo "✅ Container executed successfully"
else
    echo "❌ Container execution failed"
    exit 1
fi

# Check outputs
echo ""
echo "📄 Generated outputs:"
ls -la output/*.json 2>/dev/null || echo "No JSON files generated"

echo ""
echo "🎉 Build and test complete!"
echo "Ready for submission to Adobe Hackathon"
echo ""
echo "To run manually:"
echo "docker run --rm -v \$(pwd)/input:/app/input -v \$(pwd)/output:/app/output --network none outline-extractor"
