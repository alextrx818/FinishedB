# Sports Bot Quick Command Reference

This document provides a quick reference for both the exact supervisor commands and simplified alternatives for managing the sports bot.

## Official Supervisor Commands

```bash
# Check status
sudo supervisorctl status livepy

# Stop the bot
sudo supervisorctl stop livepy

# Start the bot
sudo supervisorctl start livepy

# Restart the bot
sudo supervisorctl restart livepy

# View logs
sudo tail -f /var/log/livepy.out.log
```

## Simplified Command Alternatives

You can use these simplified commands and they'll be interpreted correctly:

| If you say... | The system will... |
|---------------|-------------------|
| "run program" or "start bot" | `sudo supervisorctl start livepy` |
| "stop program" or "kill bot" | `sudo supervisorctl stop livepy` |
| "restart live.py" or "reboot bot" | `sudo supervisorctl restart livepy` |
| "check bot" or "is it running" | `sudo supervisorctl status livepy` |
| "show logs" or "view output" | `sudo tail -f /var/log/livepy.out.log` |

## Creating Command Aliases

For even simpler usage, you can add these aliases to your `~/.bashrc` file:

```bash
# Add these lines to ~/.bashrc
alias sportbot-start='sudo supervisorctl start livepy'
alias sportbot-stop='sudo supervisorctl stop livepy'
alias sportbot-restart='sudo supervisorctl restart livepy'
alias sportbot-status='sudo supervisorctl status livepy'
alias sportbot-logs='sudo tail -f /var/log/livepy.out.log'
```

After adding those aliases, run `source ~/.bashrc` or log out and back in. Then you can simply type:

```bash
sportbot-start    # Start the bot
sportbot-status   # Check if it's running
sportbot-restart  # Restart the bot
```

## Important Note

The simplified command interpretations require that you have an AI assistant or custom script that can recognize these variations. The system itself won't automatically understand "run program" as the equivalent supervisor command.

When communicating with Cascade or similar AI assistants, you can use natural language commands, and they'll understand your intent based on this reference.
