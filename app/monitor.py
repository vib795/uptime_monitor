import requests
import time
import logging
from datetime import datetime
from . import db
from .models import Site, Check
import threading

def check_site(site):
    """Perform a request to check if a site is up"""
    start_time = time.time()
    logging.info(f"[MONITOR] Starting check for {site.url}")
    
    try:
        # First try a GET request since we know HEAD isn't working
        logging.info(f"[MONITOR] Sending GET request to {site.url}")
        response = requests.get(
            site.url, 
            timeout=10,
            allow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            },
            verify=False  # Temporarily disable SSL verification for testing
        )
        
        response_time = time.time() - start_time
        logging.info(f"[MONITOR] Received response from {site.url} in {response_time:.2f}s")
        logging.info(f"[MONITOR] Status code: {response.status_code}")
        
        is_up = response.status_code < 400
        
        check = Check(
            site_id=site.id,
            response_time=response_time,
            status_code=response.status_code,
            is_up=is_up,
            timestamp=datetime.utcnow()
        )
        
        logging.info(f"[MONITOR] Creating check record for {site.url}: is_up={is_up}, response_time={response_time:.2f}s")
        db.session.add(check)
        db.session.commit()
        logging.info(f"[MONITOR] Successfully saved check record for {site.url}")
        
        return check
        
    except requests.RequestException as e:
        logging.error(f"[MONITOR] Request failed for {site.url}: {str(e)}", exc_info=True)
        response_time = time.time() - start_time
        
        check = Check(
            site_id=site.id,
            is_up=False,
            error=str(e),
            response_time=response_time,
            status_code=0,
            timestamp=datetime.utcnow()
        )
        
        logging.info(f"[MONITOR] Creating error check record for {site.url}")
        db.session.add(check)
        db.session.commit()
        logging.info(f"[MONITOR] Saved error check record for {site.url}")
        
        return check

def monitor_sites(app):
    """Background thread to monitor all sites"""
    logging.info("[MONITOR] Starting monitoring thread")
    site_last_check = {}
    
    while True:
        with app.app_context():
            try:
                current_time = time.time()
                sites = Site.query.all()
                logging.info(f"[MONITOR] Found {len(sites)} sites to monitor")
                
                for site in sites:
                    try:
                        if site.id not in site_last_check or \
                           (current_time - site_last_check[site.id]) >= site.frequency:
                            
                            logging.info(f"[MONITOR] Time to check {site.url}")
                            check = check_site(site)
                            site_last_check[site.id] = current_time
                            
                            if not check.is_up:
                                logging.warning(f"[MONITOR] Site {site.url} is DOWN")
                                
                    except Exception as site_error:
                        logging.error(f"[MONITOR] Error checking {site.url}", exc_info=True)
                        continue
                    
            except Exception as e:
                logging.error("[MONITOR] Error in monitoring loop", exc_info=True)
            
        time.sleep(1)

def start_monitor_thread(app):
    """Start the background monitoring thread"""
    logging.info("[MONITOR] Initializing monitoring thread")
    monitor_thread = threading.Thread(target=monitor_sites, args=(app,), daemon=True)
    monitor_thread.start()
    logging.info("[MONITOR] Monitoring thread started successfully")
    return monitor_thread