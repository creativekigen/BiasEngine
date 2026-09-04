"""
Setup Script for Forex Scanner
Initializes directories and performs system checks
"""

import os
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def create_directories():
    """Create necessary project directories"""
    logger.info("Creating project directories...")
    
    directories = [
        "logs",
        "data",
        "cache",
        "backtest_results",
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True)
        logger.info(f"  ✓ {directory}/")
    
    logger.info("✓ All directories created")


def check_python_version():
    """Check Python version"""
    logger.info("Checking Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        logger.info(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        logger.error(f"  ✗ Python 3.8+ required (found {version.major}.{version.minor})")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    logger.info("Checking dependencies...")
    
    required_packages = [
        'MetaTrader5',
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'pytz',
        'requests',
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            logger.info(f"  ✓ {package}")
        except ImportError:
            logger.warning(f"  ✗ {package} (not installed)")
            all_installed = False
    
    if not all_installed:
        logger.warning("Some packages not installed. Run: pip install -r requirements.txt")
        return False
    
    logger.info("✓ All dependencies available")
    return True


def check_env_file():
    """Check if .env file exists"""
    logger.info("Checking configuration...")
    
    if Path(".env").exists():
        logger.info("  ✓ .env file found")
        return True
    elif Path(".env.example").exists():
        logger.warning("  ⚠ .env file not found (but .env.example exists)")
        logger.info("  → Copy .env.example to .env and fill in your details")
        return False
    else:
        logger.error("  ✗ .env.example not found!")
        return False


def check_mt5():
    """Check if MetaTrader5 can be imported"""
    logger.info("Checking MetaTrader5 package...")
    
    try:
        import MetaTrader5 as mt5
        logger.info("  ✓ MetaTrader5 module available")
        
        # Note: Can't test connection without running MT5 terminal
        logger.info("  ℹ MT5 terminal connection will be tested at runtime")
        return True
    except ImportError:
        logger.error("  ✗ MetaTrader5 not installed")
        logger.info("  → Run: pip install MetaTrader5")
        return False


def print_summary(checks):
    """Print summary of checks"""
    logger.info("\n" + "="*60)
    logger.info("SETUP SUMMARY")
    logger.info("="*60)
    
    all_passed = all(checks.values())
    
    for check_name, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {check_name}")
    
    logger.info("="*60)
    
    if all_passed:
        logger.info("\n✓ Setup complete! Ready to run the scanner.")
        logger.info("\nNext steps:")
        logger.info("  1. Fill in your MT5 credentials in .env")
        logger.info("  2. Launch MetaTrader 5 and login to your account")
        logger.info("  3. Run: python main.py (for live scanning)")
        logger.info("     Or: streamlit run dashboard/app.py (for dashboard)")
        logger.info("     Or: python backtest/backtest.py (for backtesting)")
    else:
        logger.warning("\n✗ Some checks failed. Please fix the issues above.")
        return 1
    
    return 0


def main():
    """Main setup function"""
    logger.info("\n" + "="*60)
    logger.info("FOREX SCANNER - SETUP WIZARD")
    logger.info("="*60 + "\n")
    
    checks = {
        "Python Version": check_python_version(),
        "Project Directories": create_directories() or True,
        "Dependencies": check_dependencies(),
        "MetaTrader5 Module": check_mt5(),
        "Configuration File": check_env_file(),
    }
    
    return print_summary(checks)


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Setup error: {e}")
        sys.exit(1)
