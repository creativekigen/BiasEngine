"""
Alert Manager Module
Handles multi-channel alerts (console, Telegram, Discord, email, sound)
"""

import logging
import sys
from typing import Optional, List
from datetime import datetime
from abc import ABC, abstractmethod
import json

from src.forex_scanner.config import config, AlertType
from src.forex_scanner.scanner import BreakoutSignal, LowSignal

logger = logging.getLogger(__name__)


class AlertChannel(ABC):
    """Base class for all alert channels"""
    
    @abstractmethod
    def send(self, message: str, data: dict) -> bool:
        """Send alert through this channel"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this channel is properly configured"""
        pass


class ConsoleAlert(AlertChannel):
    """Send alerts to console/stdout"""
    
    def send(self, message: str, data: dict) -> bool:
        """Print alert to console with formatting"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Create formatted output
            output = f"\n{'='*80}\n"
            output += f"🚨 FOREX SCANNER ALERT - {timestamp}\n"
            output += f"{'='*80}\n"
            output += f"{message}\n"
            output += f"\nDetails:\n"
            
            for key, value in data.items():
                output += f"  • {key}: {value}\n"
            
            output += f"{'='*80}\n"
            
            # Print with color if available
            print(output, file=sys.stdout, flush=True)
            return True
            
        except Exception as e:
            logger.error(f"Console alert error: {e}")
            return False
    
    def is_available(self) -> bool:
        return True


class TelegramAlert(AlertChannel):
    """Send alerts via Telegram Bot"""
    
    def send(self, message: str, data: dict) -> bool:
        """Send Telegram message"""
        if not config.TELEGRAM_ENABLED or not config.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram not configured")
            return False
        
        try:
            from telegram import Bot
            import asyncio
            
            bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
            
            # Format message
            telegram_message = f"🚨 FOREX ALERT\n\n{message}\n\n"
            for key, value in data.items():
                telegram_message += f"<b>{key}:</b> <code>{value}</code>\n"
            
            # Send async
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                bot.send_message(
                    chat_id=config.TELEGRAM_CHAT_ID,
                    text=telegram_message,
                    parse_mode='HTML'
                )
            )
            
            logger.info("✓ Telegram alert sent")
            return True
            
        except Exception as e:
            logger.error(f"Telegram alert error: {e}")
            return False
    
    def is_available(self) -> bool:
        return (config.TELEGRAM_ENABLED and 
                bool(config.TELEGRAM_BOT_TOKEN) and 
                bool(config.TELEGRAM_CHAT_ID))


class DiscordAlert(AlertChannel):
    """Send alerts via Discord Webhook"""
    
    def send(self, message: str, data: dict) -> bool:
        """Send Discord webhook message"""
        if not config.DISCORD_ENABLED or not config.DISCORD_WEBHOOK_URL:
            logger.warning("Discord not configured")
            return False
        
        try:
            import requests
            
            # Format Discord embed
            embed = {
                "title": "🚨 Forex Scanner Alert",
                "description": message,
                "color": 16711680,  # Red
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [
                    {"name": key, "value": str(value), "inline": True}
                    for key, value in data.items()
                ]
            }
            
            payload = {"embeds": [embed]}
            
            response = requests.post(
                config.DISCORD_WEBHOOK_URL,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 204:
                logger.info("✓ Discord alert sent")
                return True
            else:
                logger.error(f"Discord webhook error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Discord alert error: {e}")
            return False
    
    def is_available(self) -> bool:
        return (config.DISCORD_ENABLED and 
                bool(config.DISCORD_WEBHOOK_URL))


class EmailAlert(AlertChannel):
    """Send alerts via Email"""
    
    def send(self, message: str, data: dict) -> bool:
        """Send email alert"""
        if not config.EMAIL_ENABLED or not all([
            config.EMAIL_SMTP_SERVER,
            config.EMAIL_SENDER,
            config.EMAIL_PASSWORD,
            config.EMAIL_RECIPIENT
        ]):
            logger.warning("Email not configured")
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Format email body
            body = f"{message}\n\n"
            for key, value in data.items():
                body += f"{key}: {value}\n"
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = config.EMAIL_SENDER
            msg['To'] = config.EMAIL_RECIPIENT
            msg['Subject'] = "🚨 Forex Scanner Alert"
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(config.EMAIL_SMTP_SERVER, config.EMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info("✓ Email alert sent")
            return True
            
        except Exception as e:
            logger.error(f"Email alert error: {e}")
            return False
    
    def is_available(self) -> bool:
        return (config.EMAIL_ENABLED and 
                bool(config.EMAIL_SMTP_SERVER) and
                bool(config.EMAIL_SENDER) and
                bool(config.EMAIL_PASSWORD) and
                bool(config.EMAIL_RECIPIENT))


class SoundAlert(AlertChannel):
    """Play sound alert"""
    
    def send(self, message: str, data: dict) -> bool:
        """Play sound alert"""
        if not config.SOUND_ENABLED:
            return False
        
        try:
            # Try multiple methods to play sound
            try:
                import winsound  # Windows
                winsound.Beep(1000, 500)  # 1000Hz for 500ms
                return True
            except ImportError:
                pass
            
            try:
                import os
                os.system('afplay /System/Library/Sounds/Glass.aiff')  # macOS
                return True
            except:
                pass
            
            try:
                import subprocess
                subprocess.run(['paplay', config.SOUND_FILE])  # Linux
                return True
            except:
                pass
            
            logger.warning("Could not play sound - no audio system available")
            return False
            
        except Exception as e:
            logger.error(f"Sound alert error: {e}")
            return False
    
    def is_available(self) -> bool:
        return config.SOUND_ENABLED


class AlertManager:
    """Manages multiple alert channels"""
    
    def __init__(self):
        """Initialize alert manager"""
        self.channels: dict[AlertType, AlertChannel] = {
            AlertType.CONSOLE: ConsoleAlert(),
            AlertType.TELEGRAM: TelegramAlert(),
            AlertType.DISCORD: DiscordAlert(),
            AlertType.EMAIL: EmailAlert(),
            AlertType.SOUND: SoundAlert(),
        }
        
        self.available_channels = [
            alert_type for alert_type in config.ALERT_TYPES
            if self.channels[alert_type].is_available()
        ]
        
        logger.info(f"Alert channels available: {[ch.name for ch in self.available_channels]}")
    
    def send_low_signal_alert(self, signal: LowSignal) -> bool:
        """Send alert for detected low signal"""
        message = (
            f"✓ {signal.pair}: Late 8am 4H Candle Low Detected\n"
            f"Ready to monitor for 12:00 breakout"
        )
        
        data = {
            "Pair": signal.pair,
            "Low Price": f"{signal.low_price:.5f}",
            "Low Time (Nairobi)": signal.low_time.strftime("%H:%M:%S"),
            "Low Position": f"Minute {signal.low_minute} of 4H candle",
            "Candle High": f"{signal.candle_high:.5f}",
            "Candle Open": f"{signal.candle_open:.5f}",
            "Target (50% midpoint)": f"{signal.midpoint_target:.5f}",
            "Detected At": signal.detected_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        return self._send_to_all_channels(message, data)
    
    def send_breakout_alert(self, breakout: BreakoutSignal) -> bool:
        """Send alert for detected breakout"""
        message = (
            f"🚀 {breakout.pair}: 12:00 4H Candle BREAKOUT - {breakout.signal_strength}\n"
            f"Price took out the 8am low! READY TO TRADE!"
        )
        
        data = {
            "Pair": breakout.pair,
            "Original Low": f"{breakout.low_signal.low_price:.5f}",
            "Breakout Price": f"{breakout.breakout_price:.5f}",
            "Breakout Distance": f"{breakout.breakout_distance_pips:.1f} pips",
            "Signal Strength": breakout.signal_strength,
            "Breakout Time": breakout.breakout_time.strftime("%H:%M:%S"),
            "Target (50% midpoint)": f"{breakout.low_signal.midpoint_target:.5f}",
            "Distance to Target": f"{abs(breakout.breakout_price - breakout.low_signal.midpoint_target):.5f}",
        }
        
        return self._send_to_all_channels(message, data)
    
    def send_info_alert(self, title: str, info: dict) -> bool:
        """Send generic info alert"""
        return self._send_to_all_channels(title, info)
    
    def _send_to_all_channels(self, message: str, data: dict) -> bool:
        """Send message to all available channels"""
        results = []
        
        for alert_type in self.available_channels:
            channel = self.channels[alert_type]
            try:
                result = channel.send(message, data)
                results.append(result)
            except Exception as e:
                logger.error(f"Error sending {alert_type.value} alert: {e}")
                results.append(False)
        
        return any(results)  # Return True if at least one channel succeeded
    
    def get_status(self) -> dict:
        """Get alert status"""
        return {
            "available_channels": [ch.value for ch in self.available_channels],
            "total_channels": len(self.channels),
            "console_enabled": AlertType.CONSOLE in self.available_channels,
            "telegram_enabled": AlertType.TELEGRAM in self.available_channels,
            "discord_enabled": AlertType.DISCORD in self.available_channels,
            "email_enabled": AlertType.EMAIL in self.available_channels,
            "sound_enabled": AlertType.SOUND in self.available_channels,
        }


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create global alert manager"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
