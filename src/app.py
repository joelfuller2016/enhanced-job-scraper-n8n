#!/usr/bin/env python3
"""
Enhanced Flask API for Multi-Source Job Scraper

Provides RESTful endpoints for job scraping with comprehensive error handling,
logging, and configuration management.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from loguru import logger
import yaml
import os
import traceback
from datetime import datetime
import time

# Initialize Flask app
app = Flask(__name__)

# Load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    if not os.path.exists(config_path):
        # Fallback to default config
        return {
            'api': {'host': '0.0.0.0', 'port': 5000, 'debug': False, 'cors_origins': ['*']},
            'logging': {'level': 'INFO', 'file': 'logs/job_scraper.log'},
            'search': {'default_keywords': ['python engineer'], 'max_results_per_source': 100}
        }
    
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

config = load_config()

# Configure CORS
CORS(app, origins=config.get('api', {}).get('cors_origins', ['*']))

# Configure logging
os.makedirs('logs', exist_ok=True)
logger.add(
    config.get('logging', {}).get('file', 'logs/job_scraper.log'),
    rotation="1 week",
    retention="1 month",
    level=config.get('logging', {}).get('level', 'INFO')
)

# Import scraper (with fallback for missing modules)
try:
    from scraper import scrape_jobs
    scraper_available = True
except ImportError:
    logger.warning("Scraper module not available - using mock data")
    scraper_available = False
    
    def scrape_jobs():
        """Mock scraper function for testing"""
        return [
            {
                "title": "Python Developer",
                "company": "Tech Corp",
                "location": "Warsaw, Poland",
                "technologies": ["Python", "Django", "PostgreSQL"],
                "link": "https://example.com/job/1",
                "source": "pracuj",
                "score": 0.9,
                "extracted": datetime.now().isoformat()
            }
        ]

@app.route('/health')
def health_check():
    """Enhanced health check endpoint"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0',
            'components': {
                'scraper': 'available' if scraper_available else 'mock',
                'config': 'loaded'
            }
        }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/jobs')
def get_jobs():
    """Enhanced job scraping endpoint"""
    start_time = time.time()
    
    try:
        # Parse query parameters
        keywords = request.args.get('keywords', config.get('search', {}).get('default_keywords', ['python engineer'])[0])
        max_results = int(request.args.get('max_results', config.get('search', {}).get('max_results_per_source', 100)))
        
        logger.info(f"Starting job scraping - Keywords: {keywords}, Max results: {max_results}")
        
        # Scrape jobs
        results = scrape_jobs()
        
        # Apply max_results limit
        if len(results) > max_results:
            results = results[:max_results]
        
        processing_time = time.time() - start_time
        
        response = {
            'success': True,
            'jobs': results,
            'total_count': len(results),
            'processing_time': round(processing_time, 2),
            'timestamp': datetime.now().isoformat(),
            'version': '2.0'
        }
        
        logger.info(f"Scraping completed successfully. Found {len(results)} jobs in {processing_time:.2f}s")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in job scraping: {str(e)}\\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/config')
def get_config():
    """Get current configuration (excluding sensitive data)"""
    safe_config = {
        'api': {
            'version': '2.0',
            'port': config.get('api', {}).get('port', 5000)
        },
        'search': config.get('search', {}),
        'sources': {k: {
            'enabled': v.get('enabled', False),
            'base_url': v.get('base_url', '')
        } for k, v in config.get('sources', {}).items()}
    }
    
    return jsonify({
        'success': True,
        'config': safe_config,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    """Backward compatibility endpoint"""
    return get_jobs()

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': ['/health', '/jobs', '/config'],
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'timestamp': datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    logger.info("Starting Enhanced Job Scraper API v2.0")
    
    # Ensure directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    # Run Flask app
    api_config = config.get('api', {})
    app.run(
        host=api_config.get('host', '0.0.0.0'),
        port=api_config.get('port', 5000),
        debug=api_config.get('debug', False)
    )
