from app import create_app
from app.monitor import start_monitor_thread
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
)

# Create the Flask app
app = create_app()

if __name__ == '__main__':
    # Start the monitoring thread
    monitor_thread = start_monitor_thread(app)
    
    # Run the Flask app without debug mode to prevent duplicate monitors
    app.run(debug=False)