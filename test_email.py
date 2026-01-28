#!/usr/bin/env python3
"""
Email SMTP Connection Test
This script tests if your email configuration is correct
"""

import os
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

print("=" * 70)
print("EMAIL SMTP CONNECTION TEST")
print("=" * 70)

# Get configuration
smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
debug_mode = os.getenv("DEBUG_MODE", "True").lower() == "true"

print("\nConfiguration Loaded:")
print(f"  SMTP Server: {smtp_server}")
print(f"  SMTP Port: {smtp_port}")
print(f"  Sender Email: {sender_email}")
print(f"  Password: {'*' * len(sender_password) if sender_password else 'NOT SET'}")
print(f"  Debug Mode: {debug_mode}")

# Validate configuration
print("\n" + "=" * 70)
print("VALIDATION CHECKS")
print("=" * 70)

errors = []

if not smtp_server:
    errors.append("ERROR: SMTP_SERVER not configured in .env")
else:
    print(f"✓ SMTP Server configured: {smtp_server}")

if not smtp_port:
    errors.append("ERROR: SMTP_PORT not configured in .env")
else:
    print(f"✓ SMTP Port configured: {smtp_port}")

if not sender_email:
    errors.append("ERROR: SENDER_EMAIL not configured in .env")
else:
    print(f"✓ Sender Email configured: {sender_email}")

if not sender_password:
    errors.append("ERROR: SENDER_PASSWORD not configured in .env")
else:
    print(f"✓ Sender Password configured: {len(sender_password)} characters")

if debug_mode:
    print("⚠ WARNING: DEBUG_MODE is True - Emails will NOT be sent!")
    print("          To send real emails, set DEBUG_MODE=False in .env")
else:
    print("✓ DEBUG_MODE is False - Emails will be sent")

# Show errors if any
if errors:
    print("\n" + "=" * 70)
    print("CONFIGURATION ERRORS")
    print("=" * 70)
    for error in errors:
        print(f"  {error}")

# Test SMTP connection
if not errors and not debug_mode:
    print("\n" + "=" * 70)
    print("SMTP CONNECTION TEST")
    print("=" * 70)
    
    try:
        print("Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        print("✓ Connected to SMTP server")
        
        print("Starting TLS encryption...")
        server.starttls()
        print("✓ TLS encryption started")
        
        print("Authenticating with email and password...")
        server.login(sender_email, sender_password)
        print("✓ Authentication successful!")
        
        server.quit()
        
        print("\n" + "=" * 70)
        print("SUCCESS: All SMTP checks passed!")
        print("=" * 70)
        print("\nYour email configuration is correct.")
        print("OTP emails will be sent successfully when users signup/login.")
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n✗ AUTHENTICATION ERROR: {str(e)}")
        print("\nPossible causes:")
        print("  1. Gmail app password is incorrect")
        print("  2. 2-Step Verification not enabled on your Gmail account")
        print("  3. Using regular Gmail password instead of app password")
        print("\nSolution:")
        print("  - Go to https://myaccount.google.com/security")
        print("  - Enable 2-Step Verification")
        print("  - Go to App passwords")
        print("  - Generate new 16-character password")
        print("  - Copy and paste it as SENDER_PASSWORD in .env")
        
    except smtplib.SMTPException as e:
        print(f"\n✗ SMTP ERROR: {str(e)}")
        print("\nPossible causes:")
        print("  1. SMTP server is unreachable")
        print("  2. SMTP port is blocked by firewall/ISP")
        print("  3. SMTP server is down")
        
    except Exception as e:
        print(f"\n✗ CONNECTION ERROR: {str(e)}")
        print(f"  Error type: {type(e).__name__}")

elif debug_mode and not errors:
    print("\n" + "=" * 70)
    print("DEBUG MODE ENABLED")
    print("=" * 70)
    print("\nEmails will be printed to console instead of being sent.")
    print("To send real emails:")
    print("  1. Set DEBUG_MODE=False in .env")
    print("  2. Ensure all configuration is correct")
    print("  3. Run SMTP connection test again")

# Summary
print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)

if errors:
    print("\n1. Fix the configuration errors listed above")
    print("2. Update .env file with correct values")
    print("3. Restart Flask app: python app.py")
    print("4. Run this test again to verify")
    
elif debug_mode:
    print("\n1. Change DEBUG_MODE=False in .env")
    print("2. Restart Flask app: python app.py")
    print("3. Test signup/login - OTP will be sent to email")
    print("4. Check your email inbox for OTP")
    
else:
    print("\n1. Restart Flask app: python app.py")
    print("2. Test signup/login - OTP will be sent to email")
    print("3. Check your email inbox for OTP")
    print("4. If you don't receive email, check spam folder")

print("\n" + "=" * 70)
