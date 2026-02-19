"""
Email Checker - Seven Checks Your Email

Connects to Gmail (IMAP) or MS365 (IMAP) to check for new mail.
Seven summarizes unread messages through Ollama.

Requires: imaplib (stdlib), email (stdlib)
"""

import imaplib
import email
import json
import logging
from email.header import decode_header
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger("EmailChecker")


class EmailChecker:
    """
    Seven's email awareness.
    
    - Connects to Gmail or MS365 via IMAP
    - Checks unread messages
    - Summarizes email content through Ollama
    - Respects privacy — reads subjects/senders by default, full body on request
    """
    
    # IMAP server configs
    PROVIDERS = {
        'gmail': {'host': 'imap.gmail.com', 'port': 993},
        'ms365': {'host': 'outlook.office365.com', 'port': 993},
        'outlook': {'host': 'outlook.office365.com', 'port': 993},
        'hotmail': {'host': 'outlook.office365.com', 'port': 993},
    }
    
    def __init__(self, config_dir: Optional[str] = None):
        self.logger = logging.getLogger("EmailChecker")
        
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / "Documents" / "Seven" / "email"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "accounts.json"
        self.accounts = self._load_accounts()
        
        self.logger.info(f"[OK] Email checker ready — {len(self.accounts)} account(s)")
    
    # ============ ACCOUNT CONFIG ============
    
    def add_account(self, name: str, email_addr: str, password: str,
                    provider: str = 'gmail') -> str:
        """
        Add an email account.
        
        For Gmail: Use an App Password (not your regular password).
        Go to: Google Account → Security → 2-Step Verification → App passwords
        
        For MS365: Use your regular password or App Password.
        """
        if provider not in self.PROVIDERS:
            return f"Unknown provider '{provider}'. Supported: {', '.join(self.PROVIDERS.keys())}"
        
        self.accounts[name] = {
            'email': email_addr,
            'provider': provider,
            'host': self.PROVIDERS[provider]['host'],
            'port': self.PROVIDERS[provider]['port'],
            'password': password,  # TODO: encrypt at rest
            'added': datetime.now().isoformat()
        }
        self._save_accounts()
        return f"Email account '{name}' ({email_addr}) configured. Provider: {provider}"
    
    def remove_account(self, name: str) -> str:
        if name in self.accounts:
            del self.accounts[name]
            self._save_accounts()
            return f"Account '{name}' removed."
        return f"No account named '{name}'."
    
    def list_accounts(self) -> str:
        if not self.accounts:
            return "No email accounts configured. Use 'add email account' to set one up."
        lines = ["Email accounts:"]
        for name, cfg in self.accounts.items():
            lines.append(f"  - {name}: {cfg['email']} ({cfg['provider']})")
        return "\n".join(lines)
    
    # ============ CHECK EMAIL ============
    
    def check_unread(self, account_name: Optional[str] = None,
                     max_emails: int = 10) -> Dict:
        """
        Check for unread emails.
        
        Returns:
            Dict with 'success', 'count', 'emails' (list of subject/sender/date)
        """
        # Use first account if none specified
        if not account_name:
            if not self.accounts:
                return {'success': False, 'message': 'No email accounts configured'}
            account_name = list(self.accounts.keys())[0]
        
        if account_name not in self.accounts:
            return {'success': False, 'message': f"Unknown account: {account_name}"}
        
        cfg = self.accounts[account_name]
        
        try:
            # Connect
            mail = imaplib.IMAP4_SSL(cfg['host'], cfg['port'])
            mail.login(cfg['email'], cfg['password'])
            mail.select('INBOX')
            
            # Search unread
            status, messages = mail.search(None, 'UNSEEN')
            if status != 'OK':
                mail.logout()
                return {'success': False, 'message': 'Failed to search inbox'}
            
            msg_ids = messages[0].split()
            total_unread = len(msg_ids)
            
            # Get latest N
            emails = []
            for msg_id in msg_ids[-max_emails:]:
                try:
                    status, msg_data = mail.fetch(msg_id, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
                    if status == 'OK':
                        msg = email.message_from_bytes(msg_data[0][1])
                        
                        subject = self._decode_header(msg.get('Subject', '(no subject)'))
                        sender = self._decode_header(msg.get('From', 'unknown'))
                        date = msg.get('Date', 'unknown')
                        
                        emails.append({
                            'id': msg_id.decode(),
                            'subject': subject,
                            'from': sender,
                            'date': date,
                        })
                except Exception as e:
                    self.logger.debug(f"Error reading email {msg_id}: {e}")
            
            mail.logout()
            
            return {
                'success': True,
                'count': total_unread,
                'emails': emails,
                'account': account_name,
            }
            
        except imaplib.IMAP4.error as e:
            return {'success': False, 'message': f"IMAP error: {str(e)[:200]}. For Gmail, use an App Password."}
        except Exception as e:
            return {'success': False, 'message': f"Email check failed: {str(e)[:200]}"}
    
    def read_email(self, account_name: str, email_id: str) -> Dict:
        """Read full email body"""
        if account_name not in self.accounts:
            return {'success': False, 'message': f"Unknown account: {account_name}"}
        
        cfg = self.accounts[account_name]
        
        try:
            mail = imaplib.IMAP4_SSL(cfg['host'], cfg['port'])
            mail.login(cfg['email'], cfg['password'])
            mail.select('INBOX')
            
            status, msg_data = mail.fetch(email_id.encode(), '(RFC822)')
            if status != 'OK':
                mail.logout()
                return {'success': False, 'message': 'Failed to fetch email'}
            
            msg = email.message_from_bytes(msg_data[0][1])
            
            subject = self._decode_header(msg.get('Subject', ''))
            sender = self._decode_header(msg.get('From', ''))
            
            # Extract body
            body = self._extract_body(msg)
            
            mail.logout()
            
            return {
                'success': True,
                'subject': subject,
                'from': sender,
                'body': body[:5000],
            }
            
        except Exception as e:
            return {'success': False, 'message': f"Failed to read email: {str(e)[:200]}"}
    
    def get_summary(self, account_name: Optional[str] = None) -> str:
        """Get human-readable email summary"""
        result = self.check_unread(account_name)
        if not result['success']:
            return result['message']
        
        if result['count'] == 0:
            return "No unread emails."
        
        lines = [f"You have {result['count']} unread email(s):"]
        for em in result['emails']:
            lines.append(f"  From: {em['from'][:50]}")
            lines.append(f"  Subject: {em['subject'][:80]}")
            lines.append("")
        
        return "\n".join(lines)
    
    # ============ HELPERS ============
    
    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        try:
            decoded = decode_header(header)
            parts = []
            for content, charset in decoded:
                if isinstance(content, bytes):
                    parts.append(content.decode(charset or 'utf-8', errors='replace'))
                else:
                    parts.append(str(content))
            return ' '.join(parts)
        except Exception:
            return str(header)
    
    def _extract_body(self, msg) -> str:
        """Extract text body from email message"""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        return part.get_payload(decode=True).decode(charset, errors='replace')
                    except Exception:
                        pass
            # Fallback to HTML
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        html = part.get_payload(decode=True).decode(charset, errors='replace')
                        # Strip HTML tags (basic)
                        import re
                        return re.sub(r'<[^>]+>', '', html)[:5000]
                    except Exception:
                        pass
        else:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                return msg.get_payload(decode=True).decode(charset, errors='replace')
            except Exception:
                pass
        return "(couldn't extract email body)"
    
    def _load_accounts(self) -> Dict:
        try:
            if self.config_file.exists():
                return json.loads(self.config_file.read_text(encoding='utf-8'))
        except Exception:
            pass
        return {}
    
    def _save_accounts(self):
        try:
            # Save without passwords in plaintext
            safe = {}
            for name, cfg in self.accounts.items():
                safe[name] = {k: v for k, v in cfg.items() if k != 'password'}
                if cfg.get('password'):
                    safe[name]['has_password'] = True
            self.config_file.write_text(json.dumps(safe, indent=2), encoding='utf-8')
        except Exception:
            pass
