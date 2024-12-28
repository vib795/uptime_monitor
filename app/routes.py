from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
from . import db
from .models import Site, Check
from .monitor import check_site  # Import the check_site function

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Display the monitoring dashboard"""
    sites = Site.query.all()
    
    # Perform immediate checks for all sites
    for site in sites:
        try:
            # Only check if no recent check exists
            latest = site.latest_check
            if not latest or \
               (datetime.utcnow() - latest.timestamp) > timedelta(seconds=site.frequency):
                check_site(site)
        except Exception as e:
            print(f"Error checking {site.url}: {e}")
    
    # Get fresh site data after checks
    sites = Site.query.all()
    return render_template('index.html', sites=sites)

@main.route('/add', methods=['POST'])
def add_site():
    """Add a new site to monitor"""
    data = request.get_json()
    
    # Validate URL
    url = data['url']
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    site = Site(
        url=url,
        frequency=data.get('frequency', 300),
        alert_threshold=data.get('alert_threshold', 3),
        alert_email=data.get('alert_email')
    )
    
    db.session.add(site)
    try:
        db.session.commit()
        # Perform initial check right away
        check_site(site)
        return jsonify({'message': 'Site added successfully', 'id': site.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@main.route('/check/<int:site_id>', methods=['POST'])
def check_site_now(site_id):
    """Manually trigger a check for a specific site"""
    site = Site.query.get_or_404(site_id)
    try:
        # Only check the requested site
        check = check_site(site)
        return jsonify({
            'status': 'success',
            'is_up': check.is_up,
            'response_time': check.response_time,
            'status_code': check.status_code,
            'timestamp': check.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@main.route('/delete/<int:site_id>', methods=['POST'])
def delete_site(site_id):
    """Delete a monitored site"""
    site = Site.query.get_or_404(site_id)
    try:
        Check.query.filter_by(site_id=site_id).delete()
        db.session.delete(site)
        db.session.commit()
        return redirect(url_for('main.index'))
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@main.route('/history/<int:site_id>')
def site_history(site_id):
    """Get historical uptime data for a site"""
    days = int(request.args.get('days', 7))
    since = datetime.utcnow() - timedelta(days=days)
    
    checks = Check.query.filter_by(
        site_id=site_id
    ).filter(
        Check.timestamp >= since
    ).order_by(Check.timestamp.asc()).all()
    
    return jsonify({
        'times': [check.timestamp.isoformat() for check in checks],
        'response_times': [check.response_time for check in checks],
        'up_status': [check.is_up for check in checks]
    })