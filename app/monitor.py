import requests
import time
import logging
import threading
from datetime import datetime
from . import db
from .models import Site, Check

def check_site(site):
    """Perform a request to check if a site is up"""
    start_time = time.time()
    logging.info(f"[MONITOR] Starting check for {site.url}")
    
    try:
        response = requests.get(
            site.url, 
            timeout=10,
            allow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
        )
        
        response_time = time.time() - start_time
        is_up = response.status_code < 400
        
        check = Check(
            site_id=site.id,
            response_time=response_time,
            status_code=response.status_code,
            is_up=is_up,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(check)
        db.session.commit()
        
        logging.info(f"[MONITOR] Check completed for {site.url}: is_up={is_up}, time={response_time:.2f}s")
        return check
        
    except Exception as e:
        logging.error(f"[MONITOR] Error checking {site.url}: {str(e)}")
        response_time = time.time() - start_time
        
        check = Check(
            site_id=site.id,
            is_up=False,
            error=str(e),
            response_time=response_time,
            status_code=0,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(check)
        db.session.commit()
        return check

class MonitorThread(threading.Thread):
    """A dedicated thread class for monitoring sites"""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.daemon = True
        self.site_last_check = {}
        self._stop_event = threading.Event()
        self.name = "UptimeMonitorThread"

    def stop(self):
        """Signal the thread to stop"""
        self._stop_event.set()

    def run(self):
        """Main monitoring loop"""
        logging.info("[MONITOR] Monitor thread starting")
        
        while not self._stop_event.is_set():
            with self.app.app_context():
                try:
                    sites = Site.query.all()
                    current_time = time.time()
                    
                    for site in sites:
                        try:
                            # Get or initialize last check time
                            last_check_time = self.site_last_check.get(site.id, 0)
                            time_since_check = current_time - last_check_time
                            
                            # Check if it's time for this site
                            if time_since_check >= site.frequency:
                                logging.info(
                                    f"[MONITOR] Time to check {site.url} "
                                    f"(frequency={site.frequency}s, "
                                    f"elapsed={time_since_check:.1f}s)"
                                )
                                
                                check = check_site(site)
                                self.site_last_check[site.id] = current_time
                                
                        except Exception as e:
                            logging.error(f"[MONITOR] Site check error for {site.url}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logging.error(f"[MONITOR] Monitor loop error: {str(e)}")
                
            # Sleep for a short time to prevent excessive CPU usage
            # Use wait() instead of sleep() to allow for clean shutdown
            self._stop_event.wait(1.0)

def start_monitor_thread(app):
    """Start the monitoring thread"""
    monitor_thread = MonitorThread(app)
    monitor_thread.start()
    logging.info("[MONITOR] Monitor thread started")
    return monitor_thread