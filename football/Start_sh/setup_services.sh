#!/bin/bash
# Script to install and enable the football services

echo "Setting up the Football Live Monitor and Alerts as system services..."

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Update the service files with the correct paths
sed -i "s|/root/CascadeProjects/sports bot|$PROJECT_DIR|g" "$PROJECT_DIR/football/football-live.service"
sed -i "s|/root/CascadeProjects/sports bot|$PROJECT_DIR|g" "$PROJECT_DIR/football/football-alerts.service"

# Copy service files to systemd directory
sudo cp "$PROJECT_DIR/football/football-live.service" "/etc/systemd/system/"
sudo cp "$PROJECT_DIR/football/football-alerts.service" "/etc/systemd/system/"

# Reload systemd to recognize new services
sudo systemctl daemon-reload

# Enable and start the live monitor service
echo "Enabling and starting the Football Live Monitor service..."
sudo systemctl enable football-live.service
sudo systemctl start football-live.service
sudo systemctl status football-live.service

# Enable and start the alerts service
echo "Enabling and starting the Football Alerts service..."
sudo systemctl enable football-alerts.service
sudo systemctl start football-alerts.service
sudo systemctl status football-alerts.service

echo "
=====================================================
Services have been set up successfully!
=====================================================

The Football Live Monitor and Alerts are now running as system services.
They will start automatically on boot and restart if they crash.

To check the status of the services:
  sudo systemctl status football-live.service
  sudo systemctl status football-alerts.service

To view the live output logs:
  sudo journalctl -f -u football-live.service
  sudo journalctl -f -u football-alerts.service

To stop the services:
  sudo systemctl stop football-live.service
  sudo systemctl stop football-alerts.service

To disable the services from starting automatically:
  sudo systemctl disable football-live.service
  sudo systemctl disable football-alerts.service
"
