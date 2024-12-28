from datetime import datetime, timedelta
from . import db
import logging

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    frequency = db.Column(db.Integer, default=300)
    alert_threshold = db.Column(db.Integer, default=3)
    alert_email = db.Column(db.String(120))
    checks = db.relationship('Check', backref='site', lazy=True,
                           order_by="desc(Check.timestamp)")
    
    @property
    def latest_check(self):
        """Get the most recent check for this site"""
        logging.info(f"[MODELS] Getting latest check for {self.url}")
        try:
            check = Check.query.filter_by(site_id=self.id)\
                              .order_by(Check.timestamp.desc())\
                              .first()
            
            if check:
                logging.info(
                    f"[MODELS] Found check for {self.url}:\n"
                    f"  Time: {check.timestamp}\n"
                    f"  Status: {'UP' if check.is_up else 'DOWN'}\n"
                    f"  Response Time: {check.response_time}s\n"
                    f"  Code: {check.status_code}"
                )
            else:
                logging.info(f"[MODELS] No checks found for {self.url}")
            
            return check
            
        except Exception as e:
            logging.error(f"[MODELS] Error getting latest check for {self.url}", exc_info=True)
            return None

class Check(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    response_time = db.Column(db.Float)
    is_up = db.Column(db.Boolean)
    status_code = db.Column(db.Integer)
    error = db.Column(db.String(500))
    
    def __repr__(self):
        return f'<Check {self.site_id} @ {self.timestamp}: {"UP" if self.is_up else "DOWN"}>'