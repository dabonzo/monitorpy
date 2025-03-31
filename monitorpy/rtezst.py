import concurrent.futures
import json
import logging
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.message import EmailMessage

import pandas as pd

from monitorpy import run_check

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("certificate_monitor.log"), logging.StreamHandler()])
logger = logging.getLogger("certificate_monitor")


class CertificateMonitor:
    """Advanced certificate monitoring system."""

    def __init__(self, config_file):
        """Initialize with a configuration file."""
        self.config_file = config_file
        self.domains = []
        self.notification_config = {}
        self.check_interval = 86400  # Default: daily
        self.history_dir = "certificate_history"
        self.report_dir = "certificate_reports"

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

            self.domains = config.get("domains", [])
            self.notification_config = config.get("notifications", {})
            self.check_interval = config.get("check_interval", 86400)

            logger.info(f"Loaded configuration with {len(self.domains)} domains")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise

    def check_certificate(self, domain_info):
        """Check a single domain's certificate."""
        domain = domain_info["domain"] if isinstance(domain_info, dict) else domain_info
        port = domain_info.get("port", 443) if isinstance(domain_info, dict) else 443
        name = domain_info.get("name", f"{domain}:{port}") if isinstance(domain_info, dict) else f"{domain}:{port}"

        logger.info(f"Checking certificate for {name}")

        # Set up configuration
        config = {"hostname": domain, "port": port, "check_chain": True,
                  "warning_days": domain_info.get("warning_days", 30) if isinstance(domain_info, dict) else 30,
                  "critical_days": domain_info.get("critical_days", 14) if isinstance(domain_info, dict) else 14}

        try:
            # Run the check
            result = run_check("ssl_certificate", config)

            # Basic result data
            cert_data = {"timestamp": datetime.now().isoformat(), "domain": domain, "port": port, "name": name,
                         "status": result.status, "message": result.message,
                         "days_until_expiration": result.raw_data.get("days_until_expiration",
                                                                      0) if result.is_success() or result.status == "warning" else 0,
                         "not_after": result.raw_data.get("not_after",
                                                          "") if result.is_success() or result.status == "warning" else "",
                         "issuer": result.raw_data.get("issuer", {}).get("commonName",
                                                                         "Unknown") if result.is_success() or result.status == "warning" else "Unknown"}

            # Check for changes
            changes = self.check_for_changes(name, cert_data)
            cert_data["changes"] = changes

            # Save history
            self.save_certificate_history(name, cert_data)

            # Send notifications if needed
            if changes or result.status != "success":
                self.send_notification(name, cert_data, changes)

            return cert_data

        except Exception as e:
            logger.error(f"Error checking certificate for {name}: {str(e)}")
            cert_data = {"timestamp": datetime.now().isoformat(), "domain": domain, "port": port, "name": name,
                         "status": "error", "message": f"Exception: {str(e)}", "days_until_expiration": 0,
                         "not_after": "", "issuer": "Unknown", "changes": []}

            # Save history even for errors
            self.save_certificate_history(name, cert_data)

            # Send error notification
            self.send_notification(name, cert_data, [])

            return cert_data

    def check_for_changes(self, name, current_data):
        """Check if certificate has changed from previous state."""
        history_file = os.path.join(self.history_dir, f"{name.replace(':', '_').replace('.', '_')}_history.json")

        if not os.path.exists(history_file):
            return []  # No history to compare against

        try:
            with open(history_file, 'r') as f:
                history = json.load(f)

            if not history:
                return []

            # Get the most recent entry
            last_entry = history[-1]
            changes = []

            # Check for status change
            if last_entry.get("status") != current_data.get("status"):
                changes.append({"type": "status", "old": last_entry.get("status"), "new": current_data.get("status")})

            # Check for expiration date change
            if last_entry.get("not_after") != current_data.get("not_after"):
                changes.append(
                    {"type": "expiration", "old": last_entry.get("not_after"), "new": current_data.get("not_after")})

            # Check for issuer change
            if last_entry.get("issuer") != current_data.get("issuer"):
                changes.append({"type": "issuer", "old": last_entry.get("issuer"), "new": current_data.get("issuer")})

            return changes

        except Exception as e:
            logger.error(f"Error checking for changes: {str(e)}")
            return []

    def save_certificate_history(self, name, cert_data):
        """Save certificate history for a domain."""
        history_file = os.path.join(self.history_dir, f"{name.replace(':', '_').replace('.', '_')}_history.json")

        try:
            # Load existing history or create new one
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []

            # Add current data to history
            history.append(cert_data)

            # Save updated history
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving certificate history for {name}: {str(e)}")

    def send_notification(self, name, cert_data, changes):
        """Send notification about certificate issues or changes."""
        if not self.notification_config:
            return

        # Determine notification level
        if cert_data["status"] == "error":
            level = "CRITICAL"
        elif cert_data["status"] == "warning" or changes:
            level = "WARNING"
        else:
            return  # Don't notify for successful checks without changes

        # Build notification message
        message = f"{level} Certificate Alert: {name}\n\n"
        message += f"Status: {cert_data['status'].upper()}\n"
        message += f"Message: {cert_data['message']}\n"

        if cert_data["days_until_expiration"] > 0:
            message += f"Expires in: {cert_data['days_until_expiration']} days ({cert_data['not_after']})\n"

        if changes:
            message += "\nChanges detected:\n"
            for change in changes:
                message += f"- {change['type'].capitalize()} changed: {change['old']} → {change['new']}\n"

        message += f"\nTimestamp: {cert_data['timestamp']}"

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

            if not email_config.get("smtp_server") or not email_config.get("from_address") or not email_config.get(
                    "to_addresses"):
                logger.warning("Incomplete email configuration, skipping email notification")
                return

            msg = EmailMessage()
            msg["Subject"] = f"{level} Certificate Alert: {name}"
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

            payload = {"level": level, "name": name, "message": message}

            # Add additional fields if configured
            if webhook_config.get("include_timestamp", True):
                payload["timestamp"] = datetime.now().isoformat()

            if webhook_config.get("include_source", True):
                payload["source"] = "MonitorPy Certificate Monitor"

            response = requests.post(webhook_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Webhook notification failed with status {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")

    def run_checks(self):
        """Run certificate checks for all configured domains."""
        results = []

        # Use thread pool for parallel checks
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_domain = {executor.submit(self.check_certificate, domain): domain for domain in self.domains}

            for future in concurrent.futures.as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    cert_data = future.result()
                    results.append(cert_data)
                except Exception as e:
                    logger.error(f"Unhandled exception checking {domain}: {str(e)}")

        # Generate report
        self.generate_report(results)

        return results

    def generate_report(self, results):
        """Generate a report summarizing certificate status."""
        # Create a timestamp for the report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Prepare report summary
        summary = {"timestamp": datetime.now().isoformat(), "total_domains": len(results),
                   "status_counts": {"success": sum(1 for r in results if r["status"] == "success"),
                                     "warning": sum(1 for r in results if r["status"] == "warning"),
                                     "error": sum(1 for r in results if r["status"] == "error")},
                   "expiration_summary": {"expired": sum(1 for r in results if r["days_until_expiration"] <= 0),
                                          "expires_within_30_days": sum(
                                              1 for r in results if 0 < r["days_until_expiration"] <= 30),
                                          "expires_within_90_days": sum(
                                              1 for r in results if 30 < r["days_until_expiration"] <= 90),
                                          "expires_after_90_days": sum(
                                              1 for r in results if r["days_until_expiration"] > 90)},
                   "changed_certificates": sum(1 for r in results if r.get("changes"))}

        # Save detailed JSON report
        json_report_file = os.path.join(self.report_dir, f"certificate_report_{timestamp}.json")

        with open(json_report_file, 'w') as f:
            json.dump({"summary": summary, "results": results}, f, indent=2)

        # Save Excel report with key information
        excel_report_file = os.path.join(self.report_dir, f"certificate_report_{timestamp}.xlsx")

        # Convert results to DataFrame
        df = pd.DataFrame([{"Domain": r["domain"], "Port": r["port"], "Name": r["name"], "Status": r["status"],
                            "Message": r["message"], "Days Until Expiration": r["days_until_expiration"],
                            "Expiration Date": r["not_after"], "Issuer": r["issuer"], "Changed": bool(r.get("changes")),
                            "Timestamp": r["timestamp"]} for r in results])

        # Sort by expiration (warning/critical first)
        df = df.sort_values(by=["Status", "Days Until Expiration"])

        # Save to Excel
        df.to_excel(excel_report_file, index=False)

        # Log summary
        logger.info(f"Certificate check summary:")
        logger.info(f"  Total domains: {summary['total_domains']}")
        logger.info(
            f"  Success: {summary['status_counts']['success']}, Warning: {summary['status_counts']['warning']}, Error: {summary['status_counts']['error']}")
        logger.info(
            f"  Expiration: {summary['expiration_summary']['expired']} expired, {summary['expiration_summary']['expires_within_30_days']} within 30 days")
        logger.info(f"  Changed certificates: {summary['changed_certificates']}")
        logger.info(f"  Reports saved to {json_report_file} and {excel_report_file}")

    def run_monitoring_loop(self):
        """Run continuous certificate monitoring."""
        logger.info("Starting certificate monitoring loop")

        while True:
            try:
                self.run_checks()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")

            # Log next check time
            next_check = datetime.now() + timedelta(seconds=self.check_interval)
            logger.info(f"Next check scheduled at: {next_check.isoformat()}")

            # Sleep until next check
            time.sleep(self.check_interval)


# Example usage
if __name__ == "__main__":
    monitor = CertificateMonitor("certificate_monitor_config.json")
    monitor.run_monitoring_loop()
