# Advanced Mail Server Monitoring

This document covers advanced usage and techniques for the mail server monitoring plugin in MonitorPy.

## Working with Raw Results

The `CheckResult` object returned by the mail server plugin contains detailed information in its `raw_data` attribute. Understanding this structure allows for advanced analysis and custom processing.

### Raw Data Structure

The structure of `raw_data` depends on the protocol being checked:

#### SMTP Raw Data

```python
result = run_check("mail_server", {"hostname": "example.com", "protocol": "smtp"})
raw_data = result.raw_data

# Basic SMTP check raw data:
{
    "hostname": "mail.example.com",    # Server hostname
    "port": 25,                        # Port used
    "protocol": "smtp",                # Protocol checked
    "extensions": {                    # SMTP extensions supported
        "SIZE": "10240000",
        "STARTTLS": "",
        "AUTH": "PLAIN LOGIN",
        "ENHANCEDSTATUSCODES": "",
        "8BITMIME": ""
    },
    "supports_tls": True,              # Whether server supports STARTTLS
    "local_address": "192.0.2.2",      # Local connection address
    "remote_address": "192.0.2.1",     # Remote server address
    "ehlo_code": 250,                  # EHLO response code
    "ehlo_message": "mail.example.com Hello client" # EHLO response message
}

# With authentication:
{
    # ...basic fields...
    "authenticated": True              # Authentication successful
}

# With test email:
{
    # ...basic fields...
    "authenticated": True,
    "test_send": True,
    "test_send_success": True
}
```

#### IMAP Raw Data

```python
result = run_check("mail_server", {"hostname": "example.com", "protocol": "imap"})
raw_data = result.raw_data

# Basic IMAP check raw data:
{
    "hostname": "mail.example.com",
    "port": 143,
    "protocol": "imap",
    "capabilities": "IMAP4rev1 STARTTLS AUTH=PLAIN AUTH=LOGIN LOGINDISABLED"
}

# With authentication:
{
    "hostname": "mail.example.com",
    "port": 143,
    "protocol": "imap",
    "authenticated": True,
    "mailbox_status": "OK",
    "mailbox_message_count": 42
}
```

#### POP3 Raw Data

```python
result = run_check("mail_server", {"hostname": "example.com", "protocol": "pop3"})
raw_data = result.raw_data

# Basic POP3 check raw data:
{
    "hostname": "mail.example.com",
    "port": 110,
    "protocol": "pop3",
    "welcome_message": "+OK POP3 server ready",
    "capabilities": ["USER", "PIPELINING", "UIDL", "TOP"]
}

# With authentication:
{
    "hostname": "mail.example.com",
    "port": 110,
    "protocol": "pop3",
    "authenticated": True,
    "message_count": 15,
    "mailbox_size": 45000
}
```

#### MX Resolution Raw Data

When using `resolve_mx`, additional fields are included:

```python
{
    # ...protocol-specific fields...
    "mx_records": ["primary-mx.example.com", "secondary-mx.example.com"],
    "hostname_used": "primary-mx.example.com"
}
```

## Mail Server Diagnostics

### Comprehensive Mail Server Analysis

```python
from monitorpy import run_check
import json
from datetime import datetime

def analyze_mail_server(domain, username=None, password=None):
    """Perform comprehensive analysis of a domain's mail server configuration."""
    results = {
        "domain": domain,
        "timestamp": datetime.now().isoformat(),
        "mx_records": [],
        "smtp": {},
        "imap": {},
        "pop3": {}
    }
    
    # First, check for MX records
    try:
        print(f"\nAnalyzing mail servers for {domain}...")
        mx_config = {
            "hostname": domain,
            "protocol": "smtp",
            "resolve_mx": True
        }
        
        mx_result = run_check("mail_server", mx_config)
        if "mx_records" in mx_result.raw_data:
            results["mx_records"] = mx_result.raw_data["mx_records"]
            print(f"Found {len(results['mx_records'])} MX records:")
            for mx in results["mx_records"]:
                print(f"  {mx}")
        else:
            print("No MX records found or unable to resolve")
    except Exception as e:
        print(f"Error checking MX records: {e}")
    
    # Check SMTP on each MX record
    for mx_index, mx_server in enumerate(results["mx_records"]):
        print(f"\nChecking SMTP on {mx_server}...")
        
        # Basic SMTP check
        smtp_config = {
            "hostname": mx_server,
            "protocol": "smtp",
            "timeout": 10
        }
        
        smtp_result = run_check("mail_server", smtp_config)
        
        results["smtp"][mx_server] = {
            "basic_check": {
                "status": smtp_result.status,
                "message": smtp_result.message,
                "response_time": smtp_result.response_time
            }
        }
        
        if smtp_result.is_success():
            # Store SMTP capabilities
            results["smtp"][mx_server]["extensions"] = smtp_result.raw_data.get("extensions", {})
            results["smtp"][mx_server]["supports_tls"] = smtp_result.raw_data.get("supports_tls", False)
            
            print(f"  Basic SMTP: ✅ {smtp_result.message}")
            
            # Check STARTTLS if supported
            if smtp_result.raw_data.get("supports_tls", False):
                print("  Testing SMTP with STARTTLS...")
                
                tls_config = {
                    "hostname": mx_server,
                    "protocol": "smtp",
                    "use_tls": True,
                    "timeout": 10
                }
                
                if username and password:
                    tls_config["username"] = username
                    tls_config["password"] = password
                
                tls_result = run_check("mail_server", tls_config)
                
                results["smtp"][mx_server]["starttls"] = {
                    "status": tls_result.status,
                    "message": tls_result.message,
                    "authenticated": username is not None and tls_result.raw_data.get("authenticated", False)
                }
                
                if tls_result.is_success():
                    print(f"  STARTTLS: ✅ {tls_result.message}")
                else:
                    print(f"  STARTTLS: ❌ {tls_result.message}")
            
            # Check SSL
            print("  Testing SMTP with SSL...")
            ssl_config = {
                "hostname": mx_server,
                "protocol": "smtp",
                "use_ssl": True,
                "port": 465,
                "timeout": 10
            }
            
            ssl_result = run_check("mail_server", ssl_config)
            
            results["smtp"][mx_server]["ssl"] = {
                "status": ssl_result.status,
                "message": ssl_result.message
            }
            
            if ssl_result.is_success():
                print(f"  SSL: ✅ {ssl_result.message}")
            else:
                print(f"  SSL: ❌ {ssl_result.message}")
        else:
            print(f"  Basic SMTP: ❌ {smtp_result.message}")
    
    # Check IMAP
    if results["mx_records"]:
        primary_mx = results["mx_records"][0]
        print(f"\nChecking IMAP on {primary_mx}...")
        
        imap_config = {
            "hostname": primary_mx,
            "protocol": "imap",
            "timeout": 10
        }
        
        imap_result = run_check("mail_server", imap_config)
        
        results["imap"]["basic_check"] = {
            "status": imap_result.status,
            "message": imap_result.message
        }
        
        if imap_result.is_success():
            results["imap"]["capabilities"] = imap_result.raw_data.get("capabilities", "")
            print(f"  Basic IMAP: ✅ {imap_result.message}")
            
            # Check IMAP with SSL
            print("  Testing IMAP with SSL...")
            imap_ssl_config = {
                "hostname": primary_mx,
                "protocol": "imap",
                "use_ssl": True,
                "port": 993,
                "timeout": 10
            }
            
            if username and password:
                imap_ssl_config["username"] = username
                imap_ssl_config["password"] = password
            
            imap_ssl_result = run_check("mail_server", imap_ssl_config)
            
            results["imap"]["ssl"] = {
                "status": imap_ssl_result.status,
                "message": imap_ssl_result.message,
                "authenticated": username is not None and imap_ssl_result.raw_data.get("authenticated", False)
            }
            
            if imap_ssl_result.is_success():
                print(f"  IMAP SSL: ✅ {imap_ssl_result.message}")
            else:
                print(f"  IMAP SSL: ❌ {imap_ssl_result.message}")
        else:
            print(f"  Basic IMAP: ❌ {imap_result.message}")
    
    # Check POP3
    if results["mx_records"]:
        primary_mx = results["mx_records"][0]
        print(f"\nChecking POP3 on {primary_mx}...")
        
        pop3_config = {
            "hostname": primary_mx,
            "protocol": "pop3",
            "timeout": 10
        }
        
        pop3_result = run_check("mail_server", pop3_config)
        
        results["pop3"]["basic_check"] = {
            "status": pop3_result.status,
            "message": pop3_result.message
        }
        
        if pop3_result.is_success():
            results["pop3"]["capabilities"] = pop3_result.raw_data.get("capabilities", [])
            print(f"  Basic POP3: ✅ {pop3_result.message}")
            
            # Check POP3 with SSL
            print("  Testing POP3 with SSL...")
            pop3_ssl_config = {
                "hostname": primary_mx,
                "protocol": "pop3",
                "use_ssl": True,
                "port": 995,
                "timeout": 10
            }
            
            if username and password:
                pop3_ssl_config["username"] = username
                pop3_ssl_config["password"] = password
            
            pop3_ssl_result = run_check("mail_server", pop3_ssl_config)
            
            results["pop3"]["ssl"] = {
                "status": pop3_ssl_result.status,
                "message": pop3_ssl_result.message,
                "authenticated": username is not None and pop3_ssl_result.raw_data.get("authenticated", False)
            }
            
            if pop3_ssl_result.is_success():
                print(f"  POP3 SSL: ✅ {pop3_ssl_result.message}")
            else:
                print(f"  POP3 SSL: ❌ {pop3_ssl_result.message}")
        else:
            print(f"  Basic POP3: ❌ {pop3_result.message}")
    
    # Generate summary report
    print("\nMail Server Analysis Summary:")
    print(f"Domain: {domain}")
    print(f"MX Records: {', '.join(results['mx_records']) if results['mx_records'] else 'None found'}")
    
    # SMTP Summary
    smtp_servers = list(results["smtp"].keys())
    if smtp_servers:
        print(f"SMTP Servers: {len(smtp_servers)}")
        for server in smtp_servers:
            status = results["smtp"][server]["basic_check"]["status"]
            status_icon = "✅" if status == "success" else "❌"
            print(f"  {status_icon} {server}")
    
    # IMAP Summary
    if "basic_check" in results["imap"]:
        status = results["imap"]["basic_check"]["status"]
        status_icon = "✅" if status == "success" else "❌"
        print(f"IMAP: {status_icon}")
    
    # POP3 Summary
    if "basic_check" in results["pop3"]:
        status = results["pop3"]["basic_check"]["status"]
        status_icon = "✅" if status == "success" else "❌"
        print(f"POP3: {status_icon}")
    
    # Save results to file
    filename = f"{domain.replace('.', '_')}_mail_analysis.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to {filename}")
    
    return results

# Example usage
# analyze_mail_server("example.com", "user@example.com", "password123")

## Mail Server Security Assessment

```python
from monitorpy import run_check
import re

def assess_mail_security(hostname, protocol="smtp"):
    """Assess the security configuration of a mail server."""
    security_scores = {
        "tls_available": 0,    # 0-25
        "ssl_available": 0,    # 0-25
        "auth_required": 0,    # 0-25
        "modern_protocol": 0,  # 0-25
    }
    security_notes = []
    
    # Basic check first
    config = {
        "hostname": hostname,
        "protocol": protocol
    }
    
    result = run_check("mail_server", config)
    
    if not result.is_success():
        return {
            "status": "error",
            "message": f"Unable to connect to mail server: {result.message}",
            "security_score": 0,
            "security_notes": ["Server unreachable"]
        }
    
    # Security assessment
    
    # Check for TLS support (SMTP)
    if protocol == "smtp":
        # Check if STARTTLS is supported
        if result.raw_data.get("supports_tls", False):
            security_scores["tls_available"] = 25
            security_notes.append("✅ STARTTLS is supported")
            
            # Test TLS connection
            tls_config = {
                "hostname": hostname,
                "protocol": "smtp",
                "use_tls": True
            }
            
            tls_result = run_check("mail_server", tls_config)
            if not tls_result.is_success():
                security_scores["tls_available"] = 15
                security_notes.append("⚠️ STARTTLS advertised but connection failed")
        else:
            security_notes.append("❌ STARTTLS not supported")
        
        # Check if server requires authentication
        extensions = result.raw_data.get("extensions", {})
        if "AUTH" in extensions:
            security_scores["auth_required"] = 25
            security_notes.append("✅ Authentication is supported")
            
            # Check if LOGIN authentication is supported (less secure)
            if "LOGIN" in extensions.get("AUTH", ""):
                security_scores["auth_required"] -= 5
                security_notes.append("⚠️ Less secure LOGIN authentication method is supported")
        else:
            security_notes.append("❌ No authentication methods advertised")
    
    # Check SSL availability for all protocols
    ssl_port = 465 if protocol == "smtp" else 993 if protocol == "imap" else 995
    
    ssl_config = {
        "hostname": hostname,
        "protocol": protocol,
        "use_ssl": True,
        "port": ssl_port
    }
    
    ssl_result = run_check("mail_server", ssl_config)
    if ssl_result.is_success():
        security_scores["ssl_available"] = 25
        security_notes.append(f"✅ SSL connection on port {ssl_port} is supported")
    else:
        security_notes.append(f"❌ SSL connection on port {ssl_port} failed")
    
    # Check for protocol capabilities to determine modern features
    protocol_capabilities = None
    
    if protocol == "smtp":
        protocol_capabilities = result.raw_data.get("extensions", {})
        # Check for modern SMTP features
        modern_features = {"PIPELINING", "SIZE", "ENHANCEDSTATUSCODES", "8BITMIME", "DSN"}
        found_features = set(protocol_capabilities.keys()).intersection(modern_features)
        
        if found_features:
            feature_score = len(found_features) / len(modern_features) * 25
            security_scores["modern_protocol"] = feature_score
            security_notes.append(f"✅ Modern SMTP features: {', '.join(found_features)}")
    
    elif protocol == "imap":
        capabilities_str = result.raw_data.get("capabilities", "")
        if capabilities_str:
            capabilities = set(capabilities_str.split())
            modern_features = {"IMAP4rev1", "IDLE", "NAMESPACE", "UIDPLUS", "AUTH=PLAIN"}
            found_features = capabilities.intersection(modern_features)
            
            if found_features:
                feature_score = len(found_features) / len(modern_features) * 25
                security_scores["modern_protocol"] = feature_score
                security_notes.append(f"✅ Modern IMAP features: {', '.join(found_features)}")
    
    elif protocol == "pop3":
        capabilities = result.raw_data.get("capabilities", [])
        modern_features = {"UIDL", "TOP", "PIPELINING"}
        found_features = set(capabilities).intersection(modern_features)
        
        if found_features:
            feature_score = len(found_features) / len(modern_features) * 25
            security_scores["modern_protocol"] = feature_score
            security_notes.append(f"✅ Modern POP3 features: {', '.join(found_features)}")
    
    # Calculate overall security score
    security_score = sum(security_scores.values())
    
    # Determine security rating
    if security_score >= 90:
        security_rating = "Excellent"
    elif security_score >= 70:
        security_rating = "Good"
    elif security_score >= 50:
        security_rating = "Adequate"
    elif security_score >= 30:
        security_rating = "Poor"
    else:
        security_rating = "Critical"
    
    return {
        "status": "success",
        "hostname": hostname,
        "protocol": protocol,
        "security_score": security_score,
        "security_rating": security_rating,
        "security_notes": security_notes,
        "security_scores": security_scores
    }

# Example usage
def main():
    """Run a security assessment on a mail server."""
    hostname = "mail.example.com"
    
    # Check SMTP
    smtp_security = assess_mail_security(hostname, "smtp")
    print(f"\nSMTP Security Assessment for {hostname}")
    print(f"Security Score: {smtp_security['security_score']}/100 ({smtp_security['security_rating']})")
    for note in smtp_security['security_notes']:
        print(f"- {note}")
    
    # Check IMAP
    imap_security = assess_mail_security(hostname, "imap")
    print(f"\nIMAP Security Assessment for {hostname}")
    print(f"Security Score: {imap_security['security_score']}/100 ({imap_security['security_rating']})")
    for note in imap_security['security_notes']:
        print(f"- {note}")
    
    # Check POP3
    pop3_security = assess_mail_security(hostname, "pop3")
    print(f"\nPOP3 Security Assessment for {hostname}")
    print(f"Security Score: {pop3_security['security_score']}/100 ({pop3_security['security_rating']})")
    for note in pop3_security['security_notes']:
        print(f"- {note}")

# if __name__ == "__main__":
#     main()
```

## Mail Server Monitoring System

The following example demonstrates a comprehensive mail server monitoring system that can be run on a schedule to continuously monitor mail servers and alert on problems:

```python
import time
import json
import logging
import smtplib
import os
from email.message import EmailMessage
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from monitorpy import run_check

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mail_server_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mail_monitor")

class MailServerMonitor:
    """Comprehensive mail server monitoring system."""
    
    def __init__(self, config_file):
        """Initialize with a configuration file."""
        self.config_file = config_file
        self.servers = []
        self.notification_config = {}
        self.check_interval = 3600  # Default: 1 hour
        self.history_dir = "mail_server_history"
        self.report_dir = "mail_server_reports"
        
        # Create directories if they don't exist
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            self.servers = config.get("servers", [])
            self.notification_config = config.get("notifications", {})
            self.check_interval = config.get("check_interval", 3600)
            
            logger.info(f"Loaded configuration with {len(self.servers)} mail servers")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def check_server(self, server_config):
        """Check a single mail server."""
        hostname = server_config["hostname"]
        protocol = server_config.get("protocol", "smtp")
        name = server_config.get("name", f"{hostname} ({protocol})")
        
        logger.info(f"Checking {name}...")
        
        # Build configuration for the check
        config = {k: v for k, v in server_config.items() if k != "name"}
        
        try:
            # Run the check
            result = run_check("mail_server", config)
            
            # Check for changes from previous state
            changes = self.check_for_changes(name, result)
            
            # Save current state
            self.save_state(name, result)
            
            # Send notification if needed
            if changes or result.status != "success":
                self.send_notification(name, server_config, result, changes)
            
            return {
                "name": name,
                "hostname": hostname,
                "protocol": protocol,
                "status": result.status,
                "message": result.message,
                "changes": changes
            }
            
        except Exception as e:
            logger.error(f"Error checking {name}: {str(e)}")
            return {
                "name": name,
                "hostname": hostname,
                "protocol": protocol,
                "status": "error",
                "message": f"Exception: {str(e)}",
                "changes": []
            }
    
    def check_for_changes(self, name, result):
        """Check if mail server status has changed from previous state."""
        state_file = os.path.join(self.history_dir, f"{name.replace(' ', '_').replace('(', '').replace(')', '')}.json")
        
        if not os.path.exists(state_file):
            return []  # No previous state
        
        try:
            with open(state_file, 'r') as f:
                previous_state = json.load(f)
            
            changes = []
            
            # Check for status change
            if previous_state.get("status") != result.status:
                changes.append({
                    "type": "status",
                    "old": previous_state.get("status"),
                    "new": result.status
                })
            
            # Check for protocol-specific changes
            if result.raw_data.get("protocol") == "smtp":
                # Check for SMTP extensions changes
                prev_extensions = set(previous_state.get("extensions", {}).keys())
                curr_extensions = set(result.raw_data.get("extensions", {}).keys())
                
                if prev_extensions != curr_extensions:
                    changes.append({
                        "type": "smtp_extensions",
                        "old": sorted(list(prev_extensions)),
                        "new": sorted(list(curr_extensions))
                    })
            
            return changes
            
        except Exception as e:
            logger.error(f"Error checking changes for {name}: {str(e)}")
            return []
    
    def save_state(self, name, result):
        """Save the current state for future comparison."""
        state_file = os.path.join(self.history_dir, f"{name.replace(' ', '_').replace('(', '').replace(')', '')}.json")
        
        try:
            # Extract the most relevant parts from raw_data
            state = {
                "status": result.status,
                "message": result.message,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add protocol-specific information
            protocol = result.raw_data.get("protocol")
            if protocol == "smtp":
                state["extensions"] = result.raw_data.get("extensions", {})
                state["supports_tls"] = result.raw_data.get("supports_tls", False)
            elif protocol == "imap":
                state["capabilities"] = result.raw_data.get("capabilities", "")
            elif protocol == "pop3":
                state["capabilities"] = result.raw_data.get("capabilities", [])
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving state for {name}: {str(e)}")
    
    def send_notification(self, name, server_config, result, changes):
        """Send notification about mail server issues or changes."""
        if not self.notification_config:
            return
        
        # Determine notification level
        if result.status == "error":
            level = "CRITICAL"
        elif result.status == "warning" or changes:
            level = "WARNING"
        else:
            return  # Don't notify for successful checks without changes
        
        # Build notification message
        message = f"{level} Mail Server Alert: {name}\n\n"
        message += f"Status: {result.status.upper()}\n"
        message += f"Hostname: {server_config['hostname']}\n"
        message += f"Protocol: {server_config.get('protocol', 'smtp')}\n"
        message += f"Message: {result.message}\n"
        
        if changes:
            message += "\nChanges detected:\n"
            for change in changes:
                if change["type"] == "status":
                    message += f"- Status changed: {change['old']} → {change['new']}\n"
                elif change["type"] == "smtp_extensions":
                    added = set(change["new"]) - set(change["old"])
                    removed = set(change["old"]) - set(change["new"])
                    
                    if added:
                        message += f"- Added extensions: {', '.join(added)}\n"
                    if removed:
                        message += f"- Removed extensions: {', '.join(removed)}\n"
        
        message += f"\nTimestamp: {datetime.now().isoformat()}"
        
        # Send email notification if configured
        if self.notification_config.get("email", {}).get("enabled", False):
            self.send_email_notification(level, name, message)
        
        # Send webhook notification if configured
        if self.notification_config.get("webhook", {}).get("enabled", False):
            self.send_webhook_notification(level, name, message)
        
        logger.info(f"Sent {level} notification for {name}")
    
    def send_email_notification(self, level, name, message):
        """Send email notification."""
        try:
            email_config = self.notification_config.get("email", {})
            
            if not email_config.get("smtp_server") or not email_config.get("from_address") or not email_config.get("to_addresses"):
                logger.warning("Incomplete email configuration, skipping email notification")
                return
            
            msg = EmailMessage()
            msg["Subject"] = f"{level} Mail Server Alert: {name}"
            msg["From"] = email_config["from_address"]
            msg["To"] = ", ".join(email_config["to_addresses"])
            msg.set_content(message)
            
            # Send the email
            with smtplib.SMTP(email_config["smtp_server"], email_config.get("smtp_port", 25)) as server:
                if email_config.get("use_tls", False):
                    server.starttls()
                
                if email_config.get("username") and email_config.get("password"):
                    server.login(email_config["username"], email_config["password"])
                
                server.send_message(msg)
            
            logger.info(f"Sent email notification to {', '.join(email_config['to_addresses'])}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
    
    def send_webhook_notification(self, level, name, message):
        """Send webhook notification."""
        try:
            import requests
            
            webhook_config = self.notification_config.get("webhook", {})
            webhook_url = webhook_config.get("url")
            
            if not webhook_url:
                logger.warning("Missing webhook URL, skipping webhook notification")
                return
            
            payload = {
                "level": level,
                "name": name,
                "message": message
            }
            
            response = requests.post(webhook_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Webhook notification failed with status {response.status_code}: {response.text}")
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")
    
    def run_checks(self):
        """Run all configured mail server checks."""
        results = []
        
        # Use thread pool for parallel checks
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.check_server, server): server for server in self.servers}
            
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    server = futures[future]
                    logger.error(f"Error in future for {server.get('hostname')}: {str(e)}")
        
        # Generate report
        self.generate_report(results)
        
        return results
    
    def generate_report(self, results):
        """Generate a report of all mail server checks."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Prepare report summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_servers": len(results),
            "status_counts": {
                "success": sum(1 for r in results if r["status"] == "success"),
                "warning": sum(1 for r in results if r["status"] == "warning"),
                "error": sum(1 for r in results if r["status"] == "error")
            },
            "changed_servers": sum(1 for r in results if r.get("changes"))
        }
        
        # Save detailed JSON report
        report_file = os.path.join(self.report_dir, f"mail_server_report_{timestamp}.json")
        
        with open(report_file, 'w') as f:
            json.dump({"summary": summary, "results": results}, f, indent=2)
        
        logger.info(f"Generated report: {report_file}")
        
        # Log summary
        logger.info(f"Mail server check summary: {summary['total_servers']} servers checked")
        logger.info(f"  Success: {summary['status_counts']['success']}, Warning: {summary['status_counts']['warning']}, Error: {summary['status_counts']['error']}")
        logger.info(f"  Changed: {summary['changed_servers']}")
    
    def run_monitoring_loop(self):
        """Run continuous monitoring."""
        logger.info("Starting mail server monitoring loop")
        
        while True:
            try:
                self.run_checks()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
            
            next_check = datetime.now() + timedelta(seconds=self.check_interval)
            logger.info(f"Next check scheduled at: {next_check.isoformat()}")
            time.sleep(self.check_interval)
```

### Example Configuration File

Here's an example configuration file for the mail server monitoring system:

```json
{
  "servers": [
    {
      "name": "Primary SMTP",
      "hostname": "mail.example.com",
      "protocol": "smtp",
      "port": 25
    },
    {
      "name": "Primary SMTP (TLS)",
      "hostname": "mail.example.com",
      "protocol": "smtp",
      "port": 587,
      "use_tls": true,
      "username": "monitor@example.com",
      "password": "monitorpass"
    },
    {
      "name": "Primary SMTP (SSL)",
      "hostname": "mail.example.com",
      "protocol": "smtp",
      "port": 465,
      "use_ssl": true
    },
    {
      "name": "Primary IMAP",
      "hostname": "mail.example.com",
      "protocol": "imap",
      "port": 143
    },
    {
      "name": "Primary IMAP (SSL)",
      "hostname": "mail.example.com",
      "protocol": "imap",
      "port": 993,
      "use_ssl": true
    },
    {
      "name": "Primary POP3",
      "hostname": "mail.example.com",
      "protocol": "pop3",
      "port": 110
    },
    {
      "name": "Backup MX",
      "hostname": "backup-mail.example.com",
      "protocol": "smtp",
      "port": 25
    },
    {
      "name": "Domain MX Records",
      "hostname": "example.com",
      "protocol": "smtp",
      "resolve_mx": true
    }
  ],
  "check_interval": 3600,
  "notifications": {
    "email": {
      "enabled": true,
      "smtp_server": "mail.example.com",
      "smtp_port": 587,
      "use_tls": true,
      "username": "alerts@example.com",
      "password": "alertspass",
      "from_address": "alerts@example.com",
      "to_addresses": ["admin@example.com", "operations@example.com"]
    },
    "webhook": {
      "enabled": true,
      "url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
    }
  }
}
```

### Usage Example

```python
# Example usage
monitor = MailServerMonitor("mail_server_config.json")
monitor.run_monitoring_loop()
```

## Integration with Monitoring Platforms

### Prometheus Integration

The following example demonstrates how to expose mail server metrics for Prometheus:

```python
from prometheus_client import start_http_server, Gauge
import time
import threading
from monitorpy import run_check

# Define Prometheus metrics
MAIL_SERVER_UP = Gauge('mail_server_up', 'Mail server check status (1=up, 0=down)', 
                       ['hostname', 'protocol', 'port'])
MAIL_SERVER_RESPONSE_TIME = Gauge('mail_server_response_time', 'Mail server response time in seconds', 
                                 ['hostname', 'protocol', 'port'])
MAIL_SERVER_TLS_SUPPORTED = Gauge('mail_server_tls_supported', 'Mail server TLS support (1=yes, 0=no)', 
                                 ['hostname', 'protocol'])
MAIL_SERVER_MESSAGES = Gauge('mail_server_messages', 'Number of messages in mailbox', 
                           ['hostname', 'protocol', 'username'])

def monitor_mail_servers(server_configs, interval=60):
    """
    Continuously monitor mail servers and update Prometheus metrics.
    
    Args:
        server_configs: List of server configurations
        interval: Check interval in seconds
    """
    while True:
        for server in server_configs:
            hostname = server['hostname']
            protocol = server['protocol']
            port = server.get('port', '')
            
            try:
                result = run_check("mail_server", server)
                
                # Update server up/down metric
                MAIL_SERVER_UP.labels(
                    hostname=hostname, 
                    protocol=protocol, 
                    port=port
                ).set(1 if result.is_success() else 0)
                
                # Update response time metric
                MAIL_SERVER_RESPONSE_TIME.labels(
                    hostname=hostname, 
                    protocol=protocol, 
                    port=port
                ).set(result.response_time)
                
                # Update protocol-specific metrics
                if protocol == "smtp":
                    # Update TLS support metric
                    MAIL_SERVER_TLS_SUPPORTED.labels(
                        hostname=hostname, 
                        protocol=protocol
                    ).set(1 if result.raw_data.get('supports_tls', False) else 0)
                
                elif (protocol == "imap" or protocol == "pop3") and result.is_success():
                    # Update mailbox message count if available
                    if 'username' in server:
                        username = server['username']
                        
                        if protocol == "imap" and "mailbox_message_count" in result.raw_data:
                            MAIL_SERVER_MESSAGES.labels(
                                hostname=hostname, 
                                protocol=protocol, 
                                username=username
                            ).set(result.raw_data["mailbox_message_count"])
                        
                        elif protocol == "pop3" and "message_count" in result.raw_data:
                            MAIL_SERVER_MESSAGES.labels(
                                hostname=hostname, 
                                protocol=protocol, 
                                username=username
                            ).set(result.raw_data["message_count"])
                
                print(f"Updated metrics for {hostname} ({protocol}): {result.status}")
                
            except Exception as e:
                print(f"Error updating metrics for {hostname} ({protocol}): {e}")
                # Set server as down when exception occurs
                MAIL_SERVER_UP.labels(
                    hostname=hostname, 
                    protocol=protocol, 
                    port=port
                ).set(0)
        
        time.sleep(interval)

# Example usage
if __name__ == "__main__":
    # Start Prometheus HTTP server
    start_http_server(9090)
    print("Prometheus metrics available at http://localhost:9090/metrics")
    
    # Define mail servers to monitor
    mail_servers = [
        {
            "hostname": "mail.example.com",
            "protocol": "smtp",
            "port": 25
        },
        {
            "hostname": "mail.example.com",
            "protocol": "smtp",
            "port": 587,
            "use_tls": True
        },
        {
            "hostname": "mail.example.com",
            "protocol": "imap",
            "port": 993,
            "use_ssl": True,
            "username": "monitor@example.com",
            "password": "password123"
        }
    ]
    
    # Start monitoring in a background thread
    monitoring_thread = threading.Thread(
        target=monitor_mail_servers,
        args=(mail_servers, 60),
        daemon=True
    )
    monitoring_thread.start()
    
    # Keep main thread running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping monitoring...")
```

## Mail Delivery Testing

For a more comprehensive test of mail delivery, you can extend the testing beyond just checking server connectivity:

```python
from monitorpy import run_check
import time
import imaplib
import email
from email.message import EmailMessage
import uuid
import re

def test_mail_delivery(smtp_config, imap_config, timeout=120):
    """
    Test complete mail delivery by sending an email and verifying it was received.
    
    Args:
        smtp_config: Configuration for SMTP server (for sending)
        imap_config: Configuration for IMAP server (for receiving)
        timeout: Maximum time to wait for email to be delivered (seconds)
    
    Returns:
        dict: Results of the test
    """
    # Generate a unique identifier for this test
    test_id = str(uuid.uuid4())
    subject = f"Mail Delivery Test {test_id}"
    
    # Set up send configuration
    from_addr = smtp_config.get("username", "test@example.com")
    to_addr = imap_config.get("username", "test@example.com")
    
    send_config = {
        "hostname": smtp_config["hostname"],
        "protocol": "smtp",
        "username": smtp_config.get("username"),
        "password": smtp_config.get("password"),
        "use_ssl": smtp_config.get("use_ssl", False),
        "use_tls": smtp_config.get("use_tls", False),
        "port": smtp_config.get("port"),
        "test_send": True,
        "from_email": from_addr,
        "to_email": to_addr,
        "subject": subject,
        "message": f"This is an automated mail delivery test with ID {test_id}.\n\nTimestamp: {time.time()}"
    }
    
    results = {
        "test_id": test_id,
        "send_time": None,
        "receive_time": None,
        "delivery_time": None,
        "send_status": None,
        "receive_status": None,
        "overall_status": "failed"
    }
    
    # Step 1: Send the email
    print(f"Sending test email with ID {test_id}...")
    send_start = time.time()
    send_result = run_check("mail_server", send_config)
    results["send_time"] = time.time() - send_start
    
    if not send_result.is_success() or not send_result.raw_data.get("test_send_success", False):
        results["send_status"] = "failed"
        results["error"] = f"Failed to send email: {send_result.message}"
        return results
    
    results["send_status"] = "success"
    print(f"Email sent in {results['send_time']:.2f} seconds")
    
    # Step 2: Wait for the email to arrive
    print(f"Waiting for email to arrive (timeout: {timeout}s)...")
    receive_start = time.time()
    end_time = receive_start + timeout
    
    while time.time() < end_time:
        # Check IMAP for the test email
        try:
            # Configure IMAP check
            check_config = {
                "hostname": imap_config["hostname"],
                "protocol": "imap",
                "username": imap_config.get("username"),
                "password": imap_config.get("password"),
                "use_ssl": imap_config.get("use_ssl", True),
                "port": imap_config.get("port", 993),
                "timeout": 10
            }
            
            # Check if we can connect and authenticate
            imap_result = run_check("mail_server", check_config)
            
            if not imap_result.is_success():
                print(f"Warning: IMAP check failed: {imap_result.message}")
                time.sleep(5)
                continue
            
            # Connect to IMAP server directly to search for our message
            if check_config.get("use_ssl", True):
                mail = imaplib.IMAP4_SSL(check_config["hostname"], check_config.get("port", 993))
            else:
                mail = imaplib.IMAP4(check_config["hostname"], check_config.get("port", 143))
            
            mail.login(check_config["username"], check_config["password"])
            mail.select('INBOX')
            
            # Search for the test email by subject
            subject_pattern = f'SUBJECT "{subject}"'
            status, data = mail.search(None, subject_pattern)
            
            if status == 'OK' and data[0]:
                # We found the email!
                email_ids = data[0].split()
                if email_ids:
                    # Get the latest matching message
                    latest_email_id = email_ids[-1]
                    status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
                    
                    if status == 'OK':
                        # Parse the email
                        msg = email.message_from_bytes(msg_data[0][1])
                        
                        # Verify it's the correct email by checking the unique ID
                        email_body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == "text/plain":
                                    email_body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            email_body = msg.get_payload(decode=True).decode()
                        
                        if test_id in email_body:
                            results["receive_time"] = time.time() - receive_start
                            results["delivery_time"] = results["receive_time"]
                            results["receive_status"] = "success"
                            results["overall_status"] = "success"
                            
                            mail.close()
                            mail.logout()
                            
                            print(f"Email found in {results['receive_time']:.2f} seconds")
                            return results
            
            # Close the connection
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"Error checking for email: {e}")
        
        # Wait before retrying
        time.sleep(5)
    
    # If we get here, the email wasn't found within the timeout period
    results["receive_status"] = "timeout"
    results["error"] = f"Email not found within {timeout} seconds"
    print(f"Email not found within {timeout} seconds")
    
    return results

# Example usage
def main():
    """Run a mail delivery test."""
    smtp_config = {
        "hostname": "mail.example.com",
        "port": 587,
        "use_tls": True,
        "username": "sender@example.com",
        "password": "senderpass"
    }
    
    imap_config = {
        "hostname": "mail.example.com",
        "port": 993,
        "use_ssl": True,
        "username": "receiver@example.com",
        "password": "receiverpass"
    }
    
    results = test_mail_delivery(smtp_config, imap_config)
    
    if results["overall_status"] == "success":
        print(f"\n✅ Mail delivery test successful!")
        print(f"Total delivery time: {results['delivery_time']:.2f} seconds")
    else:
        print(f"\n❌ Mail delivery test failed!")
        print(f"Error: {results.get('error', 'Unknown error')}")
    
    print("\nTest Details:")
    print(f"  Test ID: {results['test_id']}")
    print(f"  Send status: {results['send_status']}")
    if results["send_status"] == "success":
        print(f"  Send time: {results['send_time']:.2f} seconds")
    print(f"  Receive status: {results['receive_status']}")
    if results["receive_status"] == "success":
        print(f"  Receive time: {results['receive_time']:.2f} seconds")

# if __name__ == "__main__":
#     main()
```

These advanced examples demonstrate how to build comprehensive mail server monitoring and testing systems using the MonitorPy mail server plugin.