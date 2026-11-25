"""Synthetic company crew handbook, with planted hazards. The company is fictional.

Run from the repository root:  uv run python data/synthesis/make_handbook.py
"""

from pathlib import Path

from docx import Document

OUT = Path(__file__).resolve().parent.parent / "mlc" / "company_crew_handbook.docx"
SECTIONS = [
    ("Who to ask", ["The Master is responsible for day-to-day crew matters on board.",
                    "The crewing officer ashore handles contracts, leave, wages and travel.",
                    "The Designated Person Ashore (DPA) receives complaints that cannot be settled on board."]),
    ("Hours of rest", ["Every crew member receives at least 10 hours of rest in any 24-hour period and at least "
                       "77 hours in any seven-day period.",
                       "Daily rest may be split into no more than two periods, one of which is at least 6 hours.",
                       "Each crew member signs the record of rest hours at the end of every month and keeps a copy.",
                       "Rest lost because of a drill or an emergency is made up with compensatory rest."]),
    ("Annual leave", ["Crew members accrue paid annual leave at 2.0 calendar days for each month of service.",
                      "Leave requests go to the crewing officer at least 30 days before sign-off."]),
    ("Wages", ["Wages are paid by bank transfer no later than the 5th day of the following month.",
               "A crew member may send one allotment each month to a nominated person.",
               "A monthly wage account shows wages, additional payments and exchange rates used.",
               "Overtime worked is recorded on the monthly work record and confirmed by the head of department."]),
    ("Repatriation", ["The company arranges and pays for travel home when a contract ends.",
                      "The longest period of continuous service on board is 11 months.",
                      "A crew member who wants to leave early gives the Master 7 days written notice."]),
    ("Medical care", ["Report illness or injury to the Master or the officer in charge of medical care at once.",
                      "Medical care on board and ashore during the contract is free of charge to the crew member.",
                      "A crew member may visit a qualified doctor or dentist in port without delay when practicable."]),
    ("Complaints", ["Raise a complaint first with your head of department.",
                    "If it is not settled within 7 days, take it to the Master.",
                    "If the Master cannot settle it within 14 days, contact the DPA ashore.",
                    "A crew member may be accompanied by another crew member and must not be victimised for "
                    "complaining."]),
]


def main():
    document = Document()
    document.add_heading("Meridian Fleet Crew Handbook (synthetic demonstration document)", 0)
    document.add_paragraph("Edition 3, effective 1 February 2026.")
    for number, (heading, paragraphs) in enumerate(SECTIONS, 1):
        document.add_heading(f"{number}. {heading}", 1)
        for paragraph in paragraphs:
            document.add_paragraph(paragraph)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
