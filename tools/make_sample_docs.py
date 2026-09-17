"""Generate the sample PDF corpus used by the demo.

The project brief asks for 3-10 representative PDFs (internal policy documents,
product manuals, a company knowledge base). This script writes that corpus into
``docs/`` so the retriever has real text to work with out of the box.

Every fact below is deliberately specific (numbers, SLAs, limits) so retrieval
quality and citation accuracy can be checked by hand. Replace these files with
your own PDFs at any time, then re-run ``python build_index.py``.
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"

TITLE_SIZE = 18
HEADING_SIZE = 13
BODY_SIZE = 11
LINE_HEIGHT = 6


def write_block(pdf: FPDF, text: str, height: float) -> None:
    """Write a full-width block and return the cursor to the left margin.

    fpdf2 >= 2.8 defaults ``multi_cell`` to ``new_x=XPos.RIGHT``, which leaves
    the cursor at the right margin and makes the following cell zero-width.
    """
    pdf.multi_cell(0, height, text, new_x="LMARGIN", new_y="NEXT")


def render_pdf(path: Path, title: str, subtitle: str, sections: list[tuple[str, list[str]]]) -> None:
    """Write one multi-page PDF with a title page header and numbered sections."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_font("Helvetica", style="B", size=TITLE_SIZE)
    write_block(pdf, title, 10)
    pdf.set_font("Helvetica", style="I", size=BODY_SIZE)
    write_block(pdf, subtitle, LINE_HEIGHT)
    pdf.ln(4)

    for number, (heading, paragraphs) in enumerate(sections, start=1):
        pdf.set_font("Helvetica", style="B", size=HEADING_SIZE)
        write_block(pdf, f"{number}. {heading}", 8)
        pdf.set_font("Helvetica", size=BODY_SIZE)
        for paragraph in paragraphs:
            write_block(pdf, paragraph, LINE_HEIGHT)
            pdf.ln(2)
        pdf.ln(1)

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))
    print(f"wrote {path.relative_to(PROJECT_ROOT)}")


def employee_handbook() -> tuple[str, str, list[tuple[str, list[str]]]]:
    return (
        "Ninjascode Employee Handbook",
        "Internal policy document. Version 4.2, effective January 2026.",
        [
            (
                "Working Hours and Remote Work",
                [
                    "Standard working hours are 09:00 to 18:00 Pakistan Standard Time, "
                    "Monday through Friday, with a one hour lunch break. The company "
                    "operates a four and a half day week: Fridays end at 13:00.",
                    "Employees may work remotely up to three days per week. Remote days "
                    "must be agreed with the reporting manager at least one week in "
                    "advance and recorded in the shared team calendar.",
                    "Core collaboration hours are 10:00 to 16:00. During these hours all "
                    "engineers are expected to be reachable on the internal chat system.",
                ],
            ),
            (
                "Leave Entitlement",
                [
                    "Every full time employee receives 24 days of paid annual leave per "
                    "calendar year, accrued at 2 days per completed month of service.",
                    "Sick leave is capped at 10 days per year and requires a medical "
                    "certificate for absences longer than 2 consecutive days.",
                    "Unused annual leave may be carried over into the first quarter of "
                    "the following year, up to a maximum of 5 days. Any balance above "
                    "5 days is forfeited on 31 March.",
                ],
            ),
            (
                "Probation and Confirmation",
                [
                    "New hires serve a probation period of 3 months. Confirmation "
                    "decisions are made in a written review during the final two weeks "
                    "of probation.",
                    "Probation may be extended once, by a maximum of 2 months, when the "
                    "reviewing manager documents specific unmet objectives.",
                    "During probation the notice period is 1 week from either side. "
                    "After confirmation the notice period is 4 weeks.",
                ],
            ),
            (
                "Expenses and Equipment",
                [
                    "The company issues a laptop with a budget of up to 250,000 PKR. "
                    "Equipment remains company property and must be returned within "
                    "14 days of the final working day.",
                    "Home office reimbursement is available up to 60,000 PKR per "
                    "employee per year, covering monitors, chairs, and keyboards. "
                    "Receipts must be submitted through the finance portal.",
                    "Client entertainment expenses above 25,000 PKR require written "
                    "pre-approval from a director.",
                ],
            ),
        ],
    )


def security_policy() -> tuple[str, str, list[tuple[str, list[str]]]]:
    return (
        "Ninjascode IT Security Policy",
        "Internal policy document. Applies to all staff and contractors.",
        [
            (
                "Authentication",
                [
                    "All company accounts must use multi-factor authentication. "
                    "Authenticator applications are permitted; SMS codes are not.",
                    "Passwords must be at least 14 characters long and are rotated "
                    "every 180 days. Reuse of any of the previous 5 passwords is "
                    "blocked by the identity provider.",
                    "Shared service accounts are prohibited. Every automated system "
                    "must authenticate with its own named credential stored in the "
                    "company secret manager.",
                ],
            ),
            (
                "Devices and Data Handling",
                [
                    "Laptops must have full disk encryption enabled before any company "
                    "data is copied onto them. BitLocker and FileVault are the only "
                    "approved implementations.",
                    "Customer data classified as confidential may not be stored on "
                    "personal devices, personal cloud storage, or removable media.",
                    "Production database exports must be encrypted with AES-256 and are "
                    "deleted automatically after 30 days.",
                ],
            ),
            (
                "Incident Response",
                [
                    "Suspected security incidents must be reported to the security "
                    "channel within 30 minutes of discovery. Reporting is never "
                    "penalised, even when the report turns out to be a false alarm.",
                    "The security team acknowledges every report within 1 hour and "
                    "provides an initial severity classification within 4 hours.",
                    "Critical incidents require a written post-mortem within 5 working "
                    "days. Post-mortems are blameless and stored in the engineering "
                    "wiki.",
                ],
            ),
            (
                "Remote and Network Access",
                [
                    "Access to internal systems from outside the office requires the "
                    "company VPN. Split tunnelling is disabled.",
                    "Public Wi-Fi may only be used over the VPN. Connecting to "
                    "production servers from public networks is forbidden.",
                    "VPN sessions time out after 12 hours of continuous connection and "
                    "must be re-authenticated.",
                ],
            ),
        ],
    )


def product_manual() -> tuple[str, str, list[tuple[str, list[str]]]]:
    return (
        "Orbit Analytics - Product Manual",
        "Administrator guide for Orbit Analytics 5.1.",
        [
            (
                "Installation",
                [
                    "Orbit Analytics requires Python 3.11 or newer, 8 GB of RAM and "
                    "20 GB of free disk space on the application server.",
                    "Installation is performed with the command 'orbitctl install "
                    "--profile production'. The installer writes its configuration to "
                    "/etc/orbit/orbit.yaml.",
                    "The first administrator account is created by running 'orbitctl "
                    "admin create'. The command prints a one time setup token that "
                    "expires after 60 minutes.",
                ],
            ),
            (
                "Dashboards",
                [
                    "A dashboard may contain at most 24 widgets. Widgets are refreshed "
                    "every 5 minutes by default; the refresh interval can be lowered to "
                    "1 minute on the Enterprise plan.",
                    "Dashboard definitions can be exported as JSON and imported into "
                    "another workspace. Scheduled exports run daily at 06:00 local "
                    "time.",
                    "Deleting a dashboard moves it to the trash, where it is retained "
                    "for 90 days before permanent removal.",
                ],
            ),
            (
                "API and Limits",
                [
                    "The REST API is rate limited to 600 requests per minute per API "
                    "key. Requests above the limit receive HTTP 429 with a Retry-After "
                    "header.",
                    "A single API request may return at most 1000 records. Larger "
                    "result sets must be paginated with the cursor parameter.",
                    "API keys expire after 365 days and must be rotated before expiry. "
                    "Each workspace may hold a maximum of 10 active API keys.",
                ],
            ),
            (
                "Backups and Retention",
                [
                    "Automated backups run every 6 hours and are retained for 35 days.",
                    "Point in time recovery is available for the previous 7 days on the "
                    "Enterprise plan and the previous 24 hours on the Standard plan.",
                    "Restoring a backup requires the maintenance window to be scheduled "
                    "at least 48 hours in advance.",
                ],
            ),
        ],
    )


def support_faq() -> tuple[str, str, list[tuple[str, list[str]]]]:
    return (
        "Orbit Analytics - Support FAQ",
        "Customer facing support tiers, response targets and escalation paths.",
        [
            (
                "Support Tiers",
                [
                    "Orbit Analytics offers three support tiers: Standard, Business and "
                    "Premium.",
                    "Standard support is available by email on business days only and "
                    "targets an initial response within 24 hours.",
                    "Business support adds weekend coverage and targets an initial "
                    "response within 8 hours. Premium support is available 24 hours a "
                    "day, every day, and targets an initial response within 2 hours.",
                ],
            ),
            (
                "Severity Levels",
                [
                    "Severity 1 means the production service is unavailable or data "
                    "loss is occurring. Severity 1 is worked continuously until "
                    "resolved.",
                    "Severity 2 means a major function is degraded but a workaround "
                    "exists. Severity 2 targets a resolution within 3 business days.",
                    "Severity 3 covers cosmetic issues and questions; these are "
                    "answered within 10 business days.",
                ],
            ),
            (
                "Escalation",
                [
                    "A ticket that breaches its response target is escalated "
                    "automatically to the on-call support lead.",
                    "Customers may request manual escalation by replying with the word "
                    "ESCALATE in the ticket subject line.",
                    "Escalations are reviewed daily at 15:00 local time by the support "
                    "manager.",
                ],
            ),
            (
                "Billing and Accounts",
                [
                    "Invoices are issued on the first working day of each month and are "
                    "payable within 30 days.",
                    "Plan changes take effect at the start of the next billing cycle. "
                    "Downgrades do not generate refunds for the current period.",
                    "Accounts unpaid for more than 60 days are suspended; data is "
                    "retained for a further 30 days before deletion.",
                ],
            ),
        ],
    )


def main() -> None:
    documents = [
        employee_handbook(),
        security_policy(),
        product_manual(),
        support_faq(),
    ]
    for title, subtitle, sections in documents:
        slug = title.lower().replace(" - ", "_").replace(" ", "_")
        render_pdf(DOCS_DIR / f"{slug}.pdf", title, subtitle, sections)
    print(f"\n{len(documents)} sample documents written to {DOCS_DIR}")


if __name__ == "__main__":
    main()
