#!/bin/bash
# Script to start both the Live Monitor and Alerts system as background processes

cd "/root/CascadeProjects/sports bot"

# First, kill any existing tmux sessions for our football monitor
if command -v tmux &> /dev/null; then
    tmux kill-session -t football_monitor 2>/dev/null || true
elif command -v screen &> /dev/null; then
    screen -X -S football_monitor quit 2>/dev/null || true
fi

echo "Starting Football Live Monitor in the background..."
# Create a new terminal session with tmux or screen for viewing the output
if command -v tmux &> /dev/null; then
    echo "Creating a new tmux session for football monitor..."
    tmux new-session -d -s football_monitor "cd \"$PWD\" && python3 football/live_monitor_wrapper.py 6128359776 30 | tee -a football/main_logger.log"
    echo "Session created! To view live output: tmux attach -t football_monitor"
    # Get the tmux session PID
    LIVE_PID=$(pgrep -f "football/live_monitor_wrapper.py")
elif command -v screen &> /dev/null; then
    echo "Creating a new screen session for football monitor..."
    screen -dmS football_monitor bash -c "cd \"$PWD\" && python3 football/live_monitor_wrapper.py 6128359776 30 | tee -a football/main_logger.log"
    echo "Session created! To view live output: screen -r football_monitor"
    # Get the screen session PID
    LIVE_PID=$(pgrep -f "football/live_monitor_wrapper.py")
else
    # Fallback if neither tmux nor screen are available
    echo "No terminal multiplexer found. Running in background mode only."
    nohup bash football/run_live_monitor.sh --background > football/live_monitor.log 2>&1 &
    LIVE_PID=$!
fi

echo "Live Monitor started with PID: $LIVE_PID"
echo "Live Monitor logs: football/live_monitor.log"
echo "Main logger: football/main_logger.log"

echo ""
echo "Starting Football Alerts System in the background..."
nohup bash football/run_alerts.sh > football/alerts.log 2>&1 &
ALERTS_PID=$!
echo "Alerts System started with PID: $ALERTS_PID"
echo "Alerts logs: football/alerts.log"

echo ""
echo "Both systems are now running in the background."
echo "To view the Football Monitor in a terminal window:"
if command -v tmux &> /dev/null; then
    echo "  tmux attach -t football_monitor"
    echo "  (To detach: Ctrl+B then D)"
elif command -v screen &> /dev/null; then
    echo "  screen -r football_monitor"
    echo "  (To detach: Ctrl+A then D)"
fi
echo ""
echo "To view the logs:"
echo "  tail -f football/live_monitor.log"
echo "  tail -f football/main_logger.log"
echo "  tail -f football/alerts.log"
echo ""
echo "To stop the processes:"
echo "  kill $LIVE_PID $ALERTS_PID"
echo ""
echo "To automatically start these services on boot, add this line to your crontab:"
echo "  @reboot cd $(pwd) && bash football/start_24_7_monitoring.sh"
echo ""
echo "To edit your crontab:"
echo "  crontab -e"

# Save the PIDs to a file for easy reference later
echo "$LIVE_PID $ALERTS_PID" > football/running_pids.txt
echo "PIDs saved to football/running_pids.txt"
