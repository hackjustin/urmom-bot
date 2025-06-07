import datetime
import pytz
import re
import logging
from dateutil import parser

logger = logging.getLogger('urmom-bot')

class Reminder:
    """Class to represent a reminder"""
    def __init__(self, user_id, channel_id, message, time, reference_msg=None, reference_author=None):
        self.user_id = user_id
        self.channel_id = channel_id
        self.message = message
        self.time = time
        self.reference_msg = reference_msg
        self.reference_author = reference_author

class ReminderManager:
    """Class to manage reminders"""
    def __init__(self, bot):
        self.bot = bot
        self.reminders = []
        self.est_timezone = pytz.timezone('US/Eastern')
        
    def add_reminder(self, reminder):
        """Add a new reminder"""
        self.reminders.append(reminder)
        # Sort reminders by time
        self.reminders.sort(key=lambda r: r.time)
        
    async def check_reminders(self):
        """Check for due reminders"""
        now = datetime.datetime.now(pytz.utc)
        due_reminders = [r for r in self.reminders if r.time <= now]
        
        for reminder in due_reminders:
            self.reminders.remove(reminder)
            await self.send_reminder(reminder)
    
    async def send_reminder(self, reminder):
        """Send a reminder to the user"""
        try:
            channel = self.bot.get_channel(reminder.channel_id)
            if not channel:
                channel = await self.bot.fetch_channel(reminder.channel_id)
                
            user_mention = f"<@{reminder.user_id}>"
            
            if reminder.reference_msg and reminder.reference_author:
                ref_author_mention = f"<@{reminder.reference_author}>"
                message = f"{user_mention}, you asked to be reminded about this message from {ref_author_mention}:\n\n> {reminder.reference_msg}\n\n{reminder.message}"
            else:
                message = f"{user_mention}, you asked me to remind you: {reminder.message}"
                
            await channel.send(message)
            
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
    
    def parse_time(self, time_str):
        """Parse a time string into a datetime object"""
        now = datetime.datetime.now(self.est_timezone)
        logger.info(f"Parsing time: {time_str} (Current time EST: {now})")
        
        # First try to parse as a relative time
        relative_time = self._parse_relative_time(time_str, now)
        if relative_time:
            logger.info(f"Parsed as relative time: {relative_time}")
            return relative_time
            
        # Then try to parse as an absolute time
        absolute_time = self._parse_absolute_time(time_str, now)
        if absolute_time:
            logger.info(f"Parsed as absolute time: {absolute_time}")
            return absolute_time
            
        logger.warning(f"Failed to parse time: {time_str}")
        return None
        
    def _parse_relative_time(self, time_str, now):
        """Parse relative time expressions like '5 minutes' or '2 hours'"""
        time_units = {
            "sec": "seconds", "secs": "seconds", "second": "seconds", "seconds": "seconds",
            "min": "minutes", "mins": "minutes", "minute": "minutes", "minutes": "minutes",
            "hr": "hours", "hrs": "hours", "hour": "hours", "hours": "hours",
            "day": "days", "days": "days",
            "week": "weeks", "weeks": "weeks"
        }
        
        pattern = r'(?:in\s+)?(\d+)\s+([a-zA-Z]+)'
        match = re.match(pattern, time_str.lower().strip())
        
        if match:
            amount = int(match.group(1))
            unit_raw = match.group(2).lower().strip()
            
            unit = time_units.get(unit_raw)
            
            if unit:
                delta_args = {unit: amount}
                delta = datetime.timedelta(**delta_args)
                return now + delta
        
        return None
        
    def _parse_absolute_time(self, time_str, now):
        """Parse absolute time expressions like 'at 5pm' or '14:30'"""
        try:
            parsed_time = parser.parse(time_str, fuzzy=True)
            logger.info(f"Parser result: {parsed_time}, type: {type(parsed_time)}")
            
            if not isinstance(parsed_time, datetime.datetime):
                logger.warning(f"Parsed time is not a datetime object: {parsed_time}")
                return None
            
            # If only time is specified (no date), use today's date
            if parsed_time.year == 1900:
                logger.info("Detected time-only value, combining with today's date")
                parsed_time = datetime.datetime.combine(
                    now.date(),
                    parsed_time.time()
                )
                parsed_time = self.est_timezone.localize(parsed_time)
                
                # If the parsed time is earlier than now, assume tomorrow
                if parsed_time < now:
                    logger.info("Time is in the past, assuming tomorrow")
                    parsed_time = parsed_time + datetime.timedelta(days=1)
            else:
                # If it already has a date, just add timezone
                if parsed_time.tzinfo is None:
                    logger.info("Adding timezone info to datetime")
                    parsed_time = self.est_timezone.localize(parsed_time)
            
            return parsed_time
        
        except (ValueError, parser.ParserError) as e:
            logger.error(f"Error parsing absolute time: {e}")
            return None