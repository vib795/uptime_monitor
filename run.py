from app import create_app
from app.monitor import start_monitor_thread

app = create_app()

if __name__ == '__main__':
    # Start the monitoring thread
    monitor_thread = start_monitor_thread(app)
    
    # Run the Flask app
    app.run(debug=False)