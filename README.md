# Automated Secret Santa CLI Application

Setup:
1. Clone or download this project into your local directory.
2. Install dependencies listed in requirements.txt
3. Update config.json with your email/app-pw information
4. Update/create the input files with your group

Input files
1. participants.csv - name-email pairs
2. constraints.csv (optional) - to prevent people gifting each other (eg to make sure couples not gifting only among themselves)


Optional arguments:
--subject "Your Custom Subject": Override the default email subject line.

--message "Additional text here": Inject custom instructions (e.g., budget limits or party date/time) into the email body after the second line.

--output-dir "path/to/custom_folder": Specify a custom root directory for output folders.

--dry-run : generating files only without senging emails

Running:
venv/bin/python run_secret_santa.py --participants participants.csv --constraints constraints.csv --config config.json --subject "🎄 Annual Family Secret Santa 2026!" --message "Just a reminder: The spending limit this year is $30, and exchange happens on Dec 24th!"





A robust Python command-line application that automates your Secret Santa draw. It securely handles random assignment while respecting complex mutual constraints, generates password-protected individual PDFs with numeric PINs, creates a confidential master record, and emails results directly via your Gmail account.

---

## ✨ Features

- **Smart Random Assignment:** Uses a backtracking solver to generate valid derangements (no one gifts themselves) while strictly honoring exclusion constraints.
- **Mutual Constraints:** Easily prevent specific people from gifting each other (e.g., couples or family members). Constraints are fully bidirectional.
- **Password-Protected PDFs:** Each participant gets a unique 6-digit numeric PIN required to open their assignment PDF.
- **Privacy-First Manifest:** The generated `passwords_manifest.csv` logs individual PINs and filenames **without** revealing pairings—meaning the operator can safely run the script even if they are participating themselves!
- **Master Backup Record:** Generates a secure, password-protected `all_gift_information.pdf` containing complete pairing info for organizers.
- **Timestamped Runs:** Automatically saves each execution into a safe, unique run directory (`run_YYYY-MM-DD_HH-MM-SS`) so past draws are never overwritten.
- **Flexible CLI & Config:** Load credentials via a clean JSON config, with optional overrides for custom email subjects and extra body messages.
- **Dry-Run Mode:** Test your full generation pipeline locally without dispatching live emails.

---

## 📁 Project Structure

```text
secret-santa-app/
├── secret_santa.py          # Main application script
├── test_secret_santa.py     # Unit test suite
├── config.json              # Gmail credentials config
├── participants.csv         # List of participants
├── constraints.csv          # Optional exclusion rules
├── requirements.txt         # Python dependencies
└── secret_santa_output/     # Generated timestamped output folders


