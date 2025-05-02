# START_SUPERVISOR

This document outlines the process for configuring the sports bot to run under Supervisor control, providing automatic startup and recovery without using systemd services (which cause Telegram notification issues).

## Legacy Cleanup

- **Systemd units disabled & archived**
  ```bash
  sudo systemctl stop sportsbot.service sportsbot-master.service
  sudo systemctl disable sportsbot.service sportsbot-master.service
  sudo mv /etc/systemd/system/sportsbot.service /etc/systemd/system/sportsbot.service.bak
  sudo mv /etc/systemd/system/sportsbot-master.service /etc/systemd/system/sportsbot-master.service.bak
  sudo systemctl daemon-reload
  ```

- **Bad cron entries removed**
  ```bash
  # Check existing crontab
  sudo crontab -l
  
  # Replace with environment settings only, removing any @reboot entries
  cat << 'EOF' | sudo crontab -
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  TZ=America/New_York
  EOF
  ```

- **Stale lock or wrapper files cleared**
  ```bash
  # Remove lock files if sports bot not running correctly
  sudo rm /root/CascadeProjects/sports_bot/football/live.lock
  
  # Remove old wrapper script
  sudo rm /opt/sportsbot_wrapper.sh.bak
  ```

## Supervisor Configuration

- **Create livepy.conf file**
  ```bash
  sudo nano /etc/supervisor/conf.d/livepy.conf
  ```

- **Configuration content**
  ```
  [program:livepy]
  command=/usr/bin/python3 /root/CascadeProjects/sports_bot/football/live.py
  directory=/root/CascadeProjects/sports_bot/football
  autostart=true
  autorestart=true
  startretries=3
  stopwaitsecs=10
  stdout_logfile=/var/log/livepy.out.log
  stderr_logfile=/var/log/livepy.err.log
  stdout_logfile_maxbytes=10MB
  stderr_logfile_maxbytes=10MB
  stdout_logfile_backups=5
  stderr_logfile_backups=5
  environment=TZ="America/New_York"
  user=root
  ```

- **Update Supervisor**
  ```bash
  sudo supervisorctl reread
  sudo supervisorctl update
  ```

## Verification

- **Check process status**
  ```bash
  sudo supervisorctl status livepy
  # You should see: livepy RUNNING pid XXXX, uptime X:XX:XX
  ```

- **Test auto-restart**
  ```bash
  # Stop the process
  sudo supervisorctl stop livepy
  
  # Start it again
  sudo supervisorctl start livepy
  
  # Verify it's running with a new PID
  sudo supervisorctl status livepy
  ```

## Operational Benefits

- **Direct Python Execution**: Still runs via `python3 live.py` (no systemd hooks) which preserves Telegram notification functionality
- **Automatic Startup**: Auto-starts on reboot without needing cron jobs
- **Fault Tolerance**: Auto-restarts on failure, improving reliability
- **Enhanced Logging**: Clean, separate logs you can easily monitor
  ```bash
  # View standard output logs
  sudo tail -f /var/log/livepy.out.log
  
  # View error logs
  sudo tail -f /var/log/livepy.err.log
  ```

## Common Supervisor Commands

```bash
# Check status
sudo supervisorctl status livepy

# Stop the bot
sudo supervisorctl stop livepy

# Start the bot
sudo supervisorctl start livepy

# Restart the bot
sudo supervisorctl restart livepy
```

This configuration ensures your sports bot runs reliably while maintaining compatibility with your Telegram notification system.
