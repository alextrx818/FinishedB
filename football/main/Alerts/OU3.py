# over_under_alert.py

import logging

# Configure logging
logger = logging.getLogger('OverUnderAlert')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class OverUnderAlert:
    """
    Alert when the Over/Under line is at or above a given threshold,
    and the match is currently in first half, halftime, or second half.
    """
    # Status IDs typically: 1=Not Started, 2=First Half, 3=Halftime, 4=Second Half, 5=Finished
    VALID_STATUS_IDS = {2, 3, 4}

    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold
        logger.info(f"Initialized OverUnderAlert with threshold {threshold}")

    def check(self, match: dict) -> str | None:
        """Check if match meets Over/Under alert criteria
        
        Args:
            match: Enriched match object from merge_logic.py
            
        Returns:
            Alert message or None if criteria not met
        """
        match_id = match.get("match_id", "unknown")
        
        # 1. Only consider matches in valid live statuses
        status_id = match.get("status_id")
        if status_id not in self.VALID_STATUS_IDS:
            logger.debug(f"Match {match_id} skipped: invalid status {status_id}")
            return None

        # 2. Extract the O/U line value - checking two potential formats
        value = None
        
        # First try the odds.markets structure (likely from merge_logic)
        odds = match.get("odds", {})
        for market in odds.get("markets", []):
            if market.get("type") == "OVER_UNDER":
                try:
                    value = float(market.get("line"))
                    break
                except (TypeError, ValueError):
                    pass
        
        # If not found, try alternative structure
        if value is None:
            ou = match.get("betting", {}).get("over_under", {})
            line = ou.get("line")
            try:
                value = float(line)
            except (TypeError, ValueError):
                pass
            
        if value is None:
            logger.debug(f"Match {match_id} skipped: no valid O/U line found")
            return None

        # 3. Fire alert if threshold met
        if value >= self.threshold:
            # Try different potential team name locations in the data structure
            home = None
            away = None
            
            if match.get("home_team") and match.get("away_team"):
                home = match.get("home_team", {}).get("name", "Unknown Home")
                away = match.get("away_team", {}).get("name", "Unknown Away")
            else:
                home = match.get("home", "Unknown Home")
                away = match.get("away", "Unknown Away")
                
            status = match.get("status", f"Status ID {status_id}")
            competition = match.get("competition", {}).get("name", "Unknown League")
            
            logger.info(f"Alert triggered for match {match_id}: O/U line = {value} (threshold: {self.threshold})")
            
            return (
                f"🔔 *HIGH O/U ALERT* 🔔\n\n"
                f"Match has Over/Under line of *{value:.2f}*\n"
                f"Teams: {home} vs {away}\n"
                f"Status: {status}\n"
                f"Competition: {competition}"
            )
        
        logger.debug(f"Match {match_id} skipped: O/U line {value} below threshold {self.threshold}")
        return None
