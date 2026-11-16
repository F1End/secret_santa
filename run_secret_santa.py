#!/usr/bin/env python3
import argparse
import csv
import datetime
import json
import os
import random
import secrets
import string
import smtplib
from email.message import EmailMessage
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader, PdfWriter


class Participant:
    def __init__(self, name, email):
        self.name = name
        self.email = email.strip().lower()
        self.assigned_to = None
        self.pdf_password = None


def load_config(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Config file not found at '{filepath}'. Please create it based on the documentation.")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_participants(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Participants file specified ('{filepath}') does not exist.")
    
    participants = []
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('Name') or row.get('name')
            email = row.get('Email') or row.get('email')
            if name and email:
                participants.append(Participant(name.strip(), email.strip()))
    return participants


def load_constraints(filepath):
    forbidden_pairs = set()
    if not filepath:
        return forbidden_pairs
        
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Constraints file specified ('{filepath}') does not exist.")
    
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            emails = [e.strip().lower() for e in row if e.strip()]
            for i in range(len(emails)):
                for j in range(i + 1, len(emails)):
                    forbidden_pairs.add((emails[i], emails[j]))
                    forbidden_pairs.add((emails[j], emails[i]))
    return forbidden_pairs


def generate_assignment(participants, forbidden_pairs):
    emails = [p.email for p in participants]
    email_to_obj = {p.email: p for p in participants}
    
    def solve(giver_idx, current_assignments, used_receivers):
        if giver_idx == len(participants):
            return current_assignments
        
        giver = emails[giver_idx]
        available_receivers = [
            r for r in emails 
            if r != giver 
            and r not in used_receivers 
            and (giver, r) not in forbidden_pairs
        ]
        
        random.shuffle(available_receivers)
        
        for receiver in available_receivers:
            current_assignments[giver] = receiver
            used_receivers.add(receiver)
            
            result = solve(giver_idx + 1, current_assignments, used_receivers)
            if result:
                return result
            
            used_receivers.remove(receiver)
            del current_assignments[giver]
            
        return None

    assignments = solve(0, {}, set())
    if not assignments:
        raise ValueError("Could not find a valid Secret Santa assignment satisfying all constraints! Try relaxing constraints.")
    
    for giver_email, receiver_email in assignments.items():
        email_to_obj[giver_email].assigned_to = email_to_obj[receiver_email]


def generate_numeric_password(length=6):
    """Generates a secure numeric-only PIN password."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def create_protected_pdf(giver, recipient, password, output_path):
    temp_pdf = output_path.with_name(f"temp_{output_path.name}")
    
    doc = SimpleDocTemplate(str(temp_pdf), pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=22,
        alignment=1,
        spaceAfter=30
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=14,
        leading=20,
        alignment=1
    )
    
    story = [
        Paragraph("🎄 Secret Santa Reveal 🎄", title_style),
        Spacer(1, 20),
        Paragraph(f"Hello <b>{giver.name}</b>,", body_style),
        Spacer(1, 15),
        Paragraph("The draw has been completed! Your Secret Santa recipient is:", body_style),
        Spacer(1, 20),
        Paragraph(f"<font size=20 color='#006600'><b>🎁 {recipient.name} 🎁</b></font>", body_style),
        Spacer(1, 30),
        Paragraph("Keep it a secret! Happy gifting!", body_style)
    ]
    
    doc.build(story)
    
    reader = PdfReader(str(temp_pdf))
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    writer.encrypt(user_password=password, owner_password=secrets.token_hex(16))
    
    with open(output_path, "wb") as f:
        writer.write(f)
        
    if temp_pdf.exists():
        temp_pdf.unlink()


def create_master_pdf(participants, password, output_path):
    temp_pdf = output_path.with_name(f"temp_{output_path.name}")
    
    doc = SimpleDocTemplate(str(temp_pdf), pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,
        spaceAfter=10
    )
    
    story = [
        Paragraph("🎄 Secret Santa Master Record 🎄", title_style),
        Paragraph("<font color='#666666'>Confidential: Complete Gifter & Giftee Pairings</font>", ParagraphStyle('Sub', parent=styles['Normal'], alignment=1, spaceAfter=20)),
        Spacer(1, 10)
    ]
    
    table_data = [["Gifter Name", "Gifter Email", "-->", "Giftee Name", "Giftee Email"]]
    for p in participants:
        table_data.append([p.name, p.email, "-->", p.assigned_to.name, p.assigned_to.email])
        
    t = Table(table_data, colWidths=[110, 140, 25, 110, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
    ]))
    
    story.append(t)
    doc.build(story)
    
    reader = PdfReader(str(temp_pdf))
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    writer.encrypt(user_password=password, owner_password=secrets.token_hex(16))
    
    with open(output_path, "wb") as f:
        writer.write(f)
        
    if temp_pdf.exists():
        temp_pdf.unlink()


def send_email(sender_email, app_password, recipient_participant, pdf_path, custom_subject=None, custom_message=None):
    msg = EmailMessage()
    msg['Subject'] = custom_subject or "🎄 Your Secret Santa Assignment is Ready! 🎁"
    msg['From'] = sender_email
    msg['To'] = recipient_participant.email
    
    lines = [
        f"Hi {recipient_participant.name},",
        f"The Secret Santa draw is complete!"
    ]
    
    if custom_message:
        lines.append("")
        lines.append(custom_message)
        
    lines.extend([
        "",
        f"Your assignment is attached to this email in a password-protected PDF file. "
        f"To open the PDF, use the following numeric PIN:",
        f"",
        f"Password PIN: {recipient_participant.pdf_password}",
        f"",
        f"Shh... keep it a secret!",
        f"",
        f"Best regards,",
        f"Secret Santa Bot"
    ])
    
    msg.set_content("\n".join(lines))
    
    with open(pdf_path, 'rb') as f:
        file_data = f.read()
        file_name = pdf_path.name
        
    msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, app_password)
        smtp.send_message(msg)


def main():
    parser = argparse.ArgumentParser(description="Automated Secret Santa CLI App with timestamped directories and strict file validation.")
    parser.add_argument('--participants', required=True, help="Path to participants CSV file")
    parser.add_argument('--constraints', required=False, help="Path to constraints CSV file")
    parser.add_argument('--config', default='config.json', help="Path to JSON config file (default: config.json)")
    parser.add_argument('--subject', required=False, help="Custom override for email subject line")
    parser.add_argument('--message', required=False, help="Additional text to insert into the email body")
    parser.add_argument('--output-dir', default="./secret_santa_output", help="Base directory to save generated runs")
    parser.add_argument('--dry-run', action='store_true', help="Run assignment and generate local files without sending emails")
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    sender_email = config.get("sender_email")
    app_password = config.get("app_password")
    
    if not sender_email or not app_password:
        raise ValueError("Configuration file missing 'sender_email' or 'app_password'.")
    
    # Create a Windows- and POSIX-safe timestamped subdirectory for this specific run
    run_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = Path(args.output_dir) / f"run_{run_timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output files will be saved to: {out_dir}")
    
    print("📥 Loading participants and constraints...")
    participants = load_participants(args.participants)
    if len(participants) < 3:
        raise ValueError("You need at least 3 participants for a Secret Santa draw.")
        
    forbidden_pairs = load_constraints(args.constraints)
    
    print("🎲 Generating valid random assignments...")
    generate_assignment(participants, forbidden_pairs)
    
    manifest_data = []
    
    print("🔒 Creating password-protected individual PDFs...")
    for p in participants:
        p.pdf_password = generate_numeric_password(4)
        safe_name = "".join(c for c in p.name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        pdf_path = out_dir / f"secret_santa_{safe_name}.pdf"
        
        create_protected_pdf(p, p.assigned_to, p.pdf_password, pdf_path)
        p.pdf_filename = pdf_path.name
        
        manifest_data.append({
            "RecordType": "Participant",
            "Name": p.name,
            "Email": p.email,
            "Password": p.pdf_password,
            "FileName": p.pdf_filename
        })
        
    print("🔒 Creating master gift information PDF...")
    master_password = generate_numeric_password(6)
    master_pdf_path = out_dir / "all_gift_information.pdf"
    create_master_pdf(participants, master_password, master_pdf_path)
    
    manifest_data.append({
        "RecordType": "MasterBackup",
        "Name": "All Gift Information",
        "Email": "-",
        "Password": master_password,
        "FileName": "all_gift_information.pdf"
    })
    
    manifest_path = out_dir / "passwords_manifest.csv"
    with open(manifest_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["RecordType", "Name", "Email", "Password", "FileName"])
        writer.writeheader()
        writer.writerows(manifest_data)
    print(f"📄 Saved safe passwords manifest locally to: {manifest_path}")
    
    if args.dry_run:
        print("🔍 Dry-run mode enabled. Skipping email dispatch.")
        return

    print("📧 Sending emails via Gmail...")
    for p in participants:
        pdf_path = out_dir / p.pdf_filename
        try:
            send_email(sender_email, app_password, p, pdf_path, custom_subject=args.subject, custom_message=args.message)
            print(f"  [Sent] Successfully emailed {p.email}")
        except Exception as e:
            print(f"  [Error] Failed to email {p.email}: {e}")
            
    print("✨ Secret Santa execution completed successfully!")


if __name__ == '__main__':
    main()
