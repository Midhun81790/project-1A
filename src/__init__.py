"""
PDF Outline Extractor - Source Package
Adobe India Hackathon Challenge - Project 1A

This package provides comprehensive PDF structure extraction capabilities
using advanced heuristics and optional BERT-based classification.
"""

__version__ = "1.0.0"
__author__ = "Adobe India Hackathon Challenge"
__description__ = "Advanced PDF Outline Extraction with ML Enhancement"

from .extractor import PDFExtractor
from .json_builder import JSONBuilder
from .bert_classifier import BERTHeadingClassifier

__all__ = [
    'PDFExtractor',
    'JSONBuilder', 
    'BERTHeadingClassifier'
]
