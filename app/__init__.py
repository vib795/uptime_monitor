from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging

# Initialize Flask extensions
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configure app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uptime.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev-key-change-in-production'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("[APP] Initializing Flask application")
    
    # Initialize extensions
    db.init_app(app)
    logger.info("[APP] Initialized database")
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    logger.info("[APP] Registered blueprints")
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("[APP] Created database tables")
    
    logger.info("[APP] Application initialization complete")
    return app