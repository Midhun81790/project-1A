# 🎯 Project 1A - Advanced PDF Outline Extractor

## 📋 Overview
This system extracts document outlines from PDF files using a hybrid ML approach combining transformer-based semantic understanding with rule-based classification. Optimized for Challenge 1A requirements with both traditional and AI-enhanced extraction methods.

## 🤖 AI-Enhanced Features
- **MiniLM Transformer**: Semantic heading detection (binary classification)
- **Rule-based Classification**: Font size, boldness, and position analysis for H1/H2/H3 assignment
- **Hybrid Pipeline**: Best of both worlds - accuracy + speed
- **Training Pipeline**: Custom dataset builder for model fine-tuning

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install PyMuPDF transformers torch pandas scikit-learn
```### 2. Add PDF FilesPlace your PDF files in the `input/` directory:```input/├── document1.pdf├── document2.pdf└── ...```### 3. Run the Extractor```bashpython main.py```### 4. Check ResultsFind your JSON outputs in the `output/` directory:```output/├── document1_outline.json├── document2_outline.json└── ...```## 📄 Output Format```json{    "title": "Document Title",    "outline": [        {            "level": "H1",            "text": "Section Title ",            "page": 1        },        {            "level": "H2",             "text": "Subsection Title ",            "page": 2        }    ]}```## 🏗️ Project Structure
```
Project-1A/
├── input/              # Place PDF files here
├── output/             # Generated JSON files appear here
├── data/               # Training data and datasets
├── model/              # Trained ML models
├── src/
│   ├── extractor.py    # Main PDF processing logic
│   ├── classifier.py   # MiniLM heading classifier
│   └── json_builder.py # JSON output formatting
├── build_dataset.py    # Training data generator
├── train_model.py      # ML model training script
├── main.py             # Entry point
├── requirements.txt    # Dependencies
└── Dockerfile          # Container setup
```

## 🤖 ML Training Workflow

### 1. Build Training Dataset
```bash
python build_dataset.py
```

### 2. Train MiniLM Classifier
```bash
python train_model.py
```

### 3. Run Hybrid Extraction
```bash
python main.py
```## 🔧 Docker Usage (Optional)```bash# Build containerdocker build -t pdf-extractor .# Run with volume mountsdocker run -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" pdf-extractor```## ✅ Features
- ✅ **Hybrid ML Pipeline**: MiniLM transformer + rule-based classification
- ✅ **Semantic Understanding**: AI-powered heading detection
- ✅ **Fast Processing**: Optimized for speed (<0.2s per PDF)
- ✅ **Accurate Classification**: H1/H2/H3 level assignment
- ✅ **Training Pipeline**: Custom model fine-tuning capability
- ✅ **Challenge 1A Optimized**: Perfect format compliance
- ✅ **Clean JSON Output**: Proper spacing and formatting
- ✅ **Batch Processing**: Multiple PDF support
- ✅ **Docker Ready**: Containerized deployment

## 🎯 Hybrid Approach Benefits
- **Transformer Strength**: Semantic understanding of content context
- **Rule-based Reliability**: Consistent formatting cue detection
- **Balanced Performance**: High accuracy with fast inference
- **Adaptable Training**: Fine-tune on domain-specific documents

## 🎯 Ready for Challenge 1A!
This extractor combines traditional PDF processing with modern AI to deliver superior outline extraction accuracy while maintaining the speed requirements for Challenge 1A.