"""
api_server.py

Purpose:
--------
Professional Flask API server acting as the bridge between the modern
web frontend and the drawdown-minimization portfolio optimizer pipeline.

Features:
- Secure execution of the backend pipeline
- Real-time status tracking
- Results serving
- Static file serving for the frontend
- User Authentication & Session Management

Author:
-------
Drawdown-Minimization Portfolio Optimizer
"""

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
import threading
import subprocess
import sys
import os
import time
import json
import yaml
import secrets
import hashlib
from functools import wraps
from pathlib import Path

app = Flask(__name__)
# Generate a secure secret key for sessions
app.secret_key = secrets.token_hex(32)
# Enable CORS with credentials support
CORS(app, supports_credentials=True)

# Global Execution State
execution_lock = threading.Lock()
execution_state = {
    'is_running': False,
    'current_step': 0,
    'status': 'idle',  # idle, running, completed, error
    'step_details': 'Ready to start',
    'results': None,
    'error': None,
    'start_time': None
}

# Configuration
PORT = 5000
FRONTEND_DIR = os.path.join(os.getcwd(), 'frontend')

# Mock User Database (In production, use a real DB)
# Password is 'password123' for all demo users
# Generated with hashlib.sha256('password123'.encode()).hexdigest()
PASSWORD_HASH = 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'

USERS = {
    'user@finance.com': {
        'name': 'Portfolio Manager', 
        'role': 'Admin', 
        'password': PASSWORD_HASH,
        'avatar': 'assets/avatar_user.png' 
    },
    'analyst@finance.com': { 
        'name': 'Risk Analyst', 
        'role': 'Viewer', 
        'password': PASSWORD_HASH,
        'avatar': 'assets/avatar_analyst.png'
    }
}

# -----------------------------------------------------------------------------
# AUTHENTICATION DECORATORS & HELPERS
# -----------------------------------------------------------------------------

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# -----------------------------------------------------------------------------
# UTILITIES
# -----------------------------------------------------------------------------

def parse_pipeline_output(output):
    """Parses the stdout from the main pipeline to extract structured results."""
    results = {
        'metrics': {},
        'weights': {},
        'monte_carlo': {},
        'allocation': {}
    }
    
    try:
        lines = output.split('\n')
        is_weights_section = False
        is_allocation_section = False
        
        print("[API] Parsing pipeline output...")
        
        for line in lines:
            original_line = line
            line = line.strip()
            
            if not line:
                continue
            
            # Detect sections
            if "Optimal Portfolio Weights:" in line:
                is_weights_section = True
                is_allocation_section = False
                print("[API] Entered weights section")
                continue
            
            if "Capital Allocation" in line:
                is_weights_section = False
                is_allocation_section = True
                print("[API] Entered allocation section")
                continue
            
            # Stop both sections on next major step
            if "4. Running" in line or "walk-forward" in line.lower():
                is_weights_section = False
                is_allocation_section = False
            
            # Parse weights (format: "   AAPL: 0.2500")
            if is_weights_section and ":" in line:
                # Skip lines that are clearly not weights
                if any(skip in line.lower() for skip in ['running', 'backtesting', 'optimization', '=====']):
                    is_weights_section = False
                    continue
                    
                parts = line.split(':')
                if len(parts) == 2:
                    try:
                        ticker = parts[0].strip()
                        weight = float(parts[1].strip())
                        if ticker and 0 <= weight <= 1:  # Valid weight
                            results['weights'][ticker] = weight
                            print(f"[API] Parsed weight: {ticker} = {weight}")
                    except ValueError:
                        pass
            
            # Parse allocation lines (format: "Allocation: TICKER: AMOUNT")
            if is_allocation_section and "Allocation:" in line:
                # Format is "Allocation: AAPL: 25000.00"
                content = line.replace("Allocation:", "").strip()
                parts = content.split(":")
                if len(parts) == 2:
                    try:
                        ticker = parts[0].strip()
                        amount = float(parts[1].strip())
                        results['allocation'][ticker] = amount
                        print(f"[API] Parsed allocation: {ticker} = ${amount}")
                    except ValueError:
                        pass
            
            # Extract Performance Metrics
            if "Max Drawdown:" in line and "worst" not in line.lower():
                try:
                    results['metrics']['max_drawdown'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif "CVaR:" in line:
                try:
                    results['metrics']['cvar'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif "Calmar Ratio:" in line:
                try:
                    results['metrics']['calmar_ratio'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif "Annualized Return:" in line:
                try:
                    results['metrics']['annualized_return'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif "Volatility:" in line:
                try:
                    results['metrics']['volatility'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif "Total Return:" in line:
                try:
                    results['metrics']['total_return'] = float(line.split(':')[1].strip())
                except:
                    pass
                    
            # Extract Monte Carlo results
            if "worst_case_drawdown:" in line:
                try:
                    results['monte_carlo']['worst_case'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif "95_percentile_drawdown:" in line:
                try:
                    results['monte_carlo']['percentile_95'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif "median_drawdown:" in line:
                try:
                    results['monte_carlo']['median'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif "average_drawdown:" in line:
                try:
                    results['monte_carlo']['average'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif "simulations:" in line:
                try:
                    results['monte_carlo']['simulations'] = int(line.split(':')[1].strip())
                except:
                    pass
                
        print(f"[API] Parsed weights: {results['weights']}")
        print(f"[API] Parsed allocation: {results['allocation']}")
        print(f"[API] Parsed metrics: {results['metrics']}")
                
    except Exception as e:
        print(f"[API] Error parsing results: {e}")
        
    return results

def run_pipeline_thread():
    """Background thread to run the pipeline subprocess."""
    global execution_state
    
    print("[API] Starting pipeline execution...")
    
    try:
        with execution_lock:
            execution_state['status'] = 'running'
            execution_state['current_step'] = 1
            execution_state['step_details'] = 'Initializing Execution Environment'
            execution_state['error'] = None
            execution_state['results'] = None
        
        steps = [
            (1, "Market Data Ingestion"),
            (2, "Data Cleaning & Return Engineering"),
            (3, "Risk Metric Computation"),
            (4, "CVaR-Based Portfolio Optimization"),
            (5, "Walk-Forward Backtesting"),
            (6, "Monte Carlo Stress Testing"),
        ]
        
        process = subprocess.Popen(
            [sys.executable, '__main__.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        
        for step_num, step_name in steps:
            if process.poll() is not None:
                break
            
            with execution_lock:
                execution_state['current_step'] = step_num
                execution_state['step_details'] = step_name
            
            time.sleep(1.5) 
            
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            results = parse_pipeline_output(stdout)
            with execution_lock:
                execution_state['status'] = 'completed'
                execution_state['current_step'] = 7
                execution_state['step_details'] = 'Evaluation & Reporting'
                execution_state['results'] = results
                print("[API] Pipeline completed successfully.")
        else:
            with execution_lock:
                execution_state['status'] = 'error'
                execution_state['error'] = stderr if stderr else "Unknown error occurred"
                print(f"[API] Pipeline failed: {stderr}")

    except Exception as e:
        with execution_lock:
            execution_state['status'] = 'error'
            execution_state['error'] = str(e)
            print(f"[API] Exception running pipeline: {e}")
            
    finally:
        with execution_lock:
            execution_state['is_running'] = False


# -----------------------------------------------------------------------------
# API ENDPOINTS
# -----------------------------------------------------------------------------

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'system': 'Drawdown-Portfolio-Optimizer-v1'})

# --- Auth Endpoints ---

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Missing credentials'}), 400
        
    user = USERS.get(email)
    
    if user:
        # Check password hash
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        if input_hash == user['password']:
            session['user'] = email
            session['role'] = user['role']
            session.permanent = True
            return jsonify({
                'status': 'success', 
                'user': {
                    'email': email,
                    'name': user['name'],
                    'role': user['role']
                }
            })
            
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return jsonify({'status': 'success', 'message': 'Logged out'})

@app.route('/api/auth/validate', methods=['GET'])
def validate_session():
    if 'user' in session:
        email = session['user']
        user = USERS.get(email)
        if user:
            return jsonify({
                'status': 'success', 
                'user': {
                    'email': email,
                    'name': user['name'],
                    'role': user['role']
                }
            })
    return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401

# --- Protected Endpoints ---

@app.route('/api/config', methods=['GET'])
@require_auth
def get_config():
    try:
        config_path = Path('configs/parameters.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return jsonify({'status': 'success', 'data': config})
        return jsonify({'status': 'error', 'message': 'Config file not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/config', methods=['POST'])
@require_auth
def update_config():
    try:
        new_config = request.json
        config_path = Path('configs/parameters.yaml')
        
        if not config_path.exists():
             return jsonify({'status': 'error', 'message': 'Config file not found'}), 404

        # Read existing
        with open(config_path, 'r') as f:
            current_config = yaml.safe_load(f)

        # Deep merge (simplified for specific sections)
        # We primarily expect updates to 'optimization' and 'data' sections
        if 'optimization' in new_config:
            current_config['optimization'].update(new_config['optimization'])
        if 'data' in new_config:
             current_config['data'].update(new_config['data'])
        if 'simulation' in new_config:
             current_config['simulation'].update(new_config['simulation'])
        if 'capital' in new_config:
             current_config['capital'].update(new_config['capital'])
        if 'backtesting' in new_config:
             current_config['backtesting'].update(new_config['backtesting'])
        if 'evaluation' in new_config:
             current_config['evaluation'].update(new_config['evaluation'])

        # Write back
        with open(config_path, 'w') as f:
            yaml.dump(current_config, f, default_flow_style=False)

        return jsonify({'status': 'success', 'message': 'Configuration updated', 'data': current_config})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/validate_ticker', methods=['POST'])
@require_auth
def validate_ticker():
    # ... (existing code) ...
    try:
        data = request.json
        ticker_symbol = data.get('ticker')
        if not ticker_symbol:
            return jsonify({'status': 'error', 'message': 'Ticker is required'}), 400

        # Use yfinance to check if ticker exists
        import yfinance as yf
        ticker = yf.Ticker(ticker_symbol)
        
        hist = ticker.history(period='1d')
        
        if not hist.empty:
            info = {}
            try:
                info = ticker.info or {}
            except:
                pass
            name = info.get('shortName') or info.get('longName') or ticker_symbol
            
            return jsonify({
                'status': 'success', 
                'valid': True, 
                'ticker': ticker_symbol.upper(),
                'name': name
            })
        else:
             return jsonify({'status': 'success', 'valid': False, 'message': 'No data found for ticker'})

    except Exception as e:
        print(f"Validation error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/assets/discover', methods=['GET'])
@require_auth
def discover_assets():
    try:
        asset_type = request.args.get('type', 'equity')
        from src.data.screener import AssetScreener
        
        assets = AssetScreener.fetch_assets(asset_type)
        return jsonify({'status': 'success', 'data': assets})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/execute', methods=['POST'])
@require_auth
def execute_pipeline():
    global execution_state
    
    with execution_lock:
        if execution_state['is_running']:
            return jsonify({'status': 'error', 'message': 'Pipeline already running'}), 400
        
        execution_state['is_running'] = True
        execution_state['start_time'] = time.time()
    
    thread = threading.Thread(target=run_pipeline_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'success', 'message': 'Execution initiated'})

@app.route('/api/status', methods=['GET'])
@require_auth
def get_status():
    with execution_lock:
        return jsonify(execution_state)

@app.route('/api/results', methods=['GET'])
@require_auth
def get_results():
    with execution_lock:
        if execution_state['results']:
            return jsonify({'status': 'success', 'data': execution_state['results']})
        return jsonify({'status': 'pending', 'message': 'No results available'}), 404

# -----------------------------------------------------------------------------
# STATIC FILE SERVING
# -----------------------------------------------------------------------------

@app.route('/')
@app.route('/intro')
def serve_intro():
    return send_from_directory(FRONTEND_DIR, 'intro.html')

@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/login')
def serve_login():
    return send_from_directory(FRONTEND_DIR, 'login.html')

@app.route('/<path:path>')
def serve_static(path):
    # Check if file exists in frontend directory
    full_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(full_path):
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        return send_from_directory(directory, filename)
    return "File not found", 404

if __name__ == '__main__':
    print(f"[*] Starting API Server on http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=False)
