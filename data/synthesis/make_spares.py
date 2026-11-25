"""Synthetic spares catalogue and supplier documents, with planted hazards. All names are fictional.

Run from the repository root:  uv run --with fpdf2 python data/synthesis/make_spares.py
"""

import csv
import random
from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parent.parent / "spares"
NORDSEE, GULF = "Nordsee Marine Spares", "Gulfstream Pumpworks"
CURRENCY = {NORDSEE: "EUR", GULF: "USD"}
EQUIPMENT = [("BP200", "ballast pump BP-200"), ("CW150", "cooling water pump CW-150"),
             ("FT80", "fuel oil transfer pump FT-80"), ("BG40", "bilge pump BG-40"),
             ("AE6L", "auxiliary engine AE-6L"), ("ME5S", "main engine ME-5S"), ("PU30", "oil purifier PU-30")]
PUMP_PARTS = ["mechanical seal", "impeller", "wear ring", "shaft sleeve", "ball bearing", "casing gasket set",
              "O-ring kit", "coupling element", "pump shaft", "gland packing set"]
ENGINE_PARTS = ["fuel injector nozzle", "piston ring set", "exhaust valve", "inlet valve", "cylinder head gasket",
                "connecting rod bearing", "fuel pump plunger", "thermostat element", "lube oil filter element",
                "turbocharger bearing kit"]
PURIFIER_PARTS = ["bowl seal ring", "sliding bowl bottom seal", "disc stack O-ring", "friction clutch pad",
                  "vertical shaft bearing", "gravity disc", "worm wheel", "operating water valve kit",
                  "drive belt", "nozzle set"]
VARIANTS = {"mechanical seal": ["45 mm, carbon/ceramic", "45 mm, silicon carbide"],
            "impeller": ["bronze, 230 mm", "stainless steel, 230 mm"],
            "bowl seal ring": ["nitrile", "fluoroelastomer"]}


def catalogue():
    rng = random.Random(25)
    rows = []
    for code, equipment in EQUIPMENT:
        parts = (PURIFIER_PARTS if code == "PU30" else ENGINE_PARTS if code in ("AE6L", "ME5S") else PUMP_PARTS)
        for index, part in enumerate(parts):
            for variant_index, variant in enumerate(VARIANTS.get(part, [""])):
                base = round(rng.uniform(18, 900), 0)
                for supplier_index, supplier in enumerate((NORDSEE, GULF)):
                    if supplier_index and rng.random() < 0.1:  # some parts have one supplier only
                        continue
                    for grade in ("OEM", "aftermarket"):
                        price = base * (1.0 if grade == "OEM" else 0.7) * rng.uniform(0.9, 1.15)
                        moq = 10 if "O-ring" in part else 4 if part in ("ball bearing", "gland packing set") else 1
                        description = ", ".join(x for x in (part.capitalize(), variant, grade) if x)
                        rows.append({
                            "part_no": f"{supplier[0]}-{code}-{index + 1:02d}{variant_index}-{'OE' if grade == 'OEM' else 'AM'}",
                            "description": description, "equipment": equipment, "supplier": supplier,
                            "unit_price": f"{price:.2f}", "currency": CURRENCY[supplier],
                            "lead_time_days": rng.randint(3, 12) + (0 if grade == "aftermarket" else 6),
                            "moq": moq, "in_stock": rng.choice(["yes", "yes", "no"])})
    with (OUT / "catalogue.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def pdf(name: str, title: str, subtitle: str, sections: list[tuple[str, list[str]]]):
    doc = FPDF(format="A4")
    doc.set_auto_page_break(True, 20)
    doc.add_page()

    def line(text, size=11, style="", gap=1.5):
        doc.set_font("Helvetica", style, size)
        doc.multi_cell(0, size * 0.5, text, new_x="LMARGIN", new_y="NEXT")
        doc.ln(gap)

    line(title, 16, "B")
    line(subtitle, 9, "I", 4)
    for number, (heading, paragraphs) in enumerate(sections, 1):
        line(f"{number}. {heading}", 12, "B")
        for paragraph in paragraphs:
            line(paragraph)
        doc.ln(2)
    doc.output(OUT / name)


def nordsee(name, issued, payment, express, minimum, cancel, cutoff):
    pdf(name, f"{NORDSEE}: terms of supply", f"Issued {issued}. Synthetic demonstration document.", [
        ("Prices and currency", ["All prices are quoted in euros (EUR) and exclude freight and duties."]),
        ("Minimum order value", [f"The minimum order value is EUR {minimum}. Smaller orders are not accepted."]),
        ("Payment", [f"Invoices are payable within {payment} days of the invoice date."]),
        ("Lead time", [f"Catalogue lead times are calendar days counted from order confirmation. Orders received "
                       f"after {cutoff} Central European Time are confirmed on the next working day.",
                       "Delivery to the vessel adds 2 calendar days for port clearance."]),
        ("Express handling", [f"Express handling carries a surcharge of {express} percent of the goods value and "
                              "reduces the lead time by 3 calendar days. It is offered for stocked items only."]),
        ("Warranty", ["Parts are warranted for 12 months from delivery against defects in material."]),
        ("Cancellation", [f"A confirmed order may be cancelled with a fee of {cancel} percent of the order value."])])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    count = catalogue()
    nordsee("nordsee_terms_2025.pdf", "15 January 2025", 30, 15, 250, 10, "15:00")
    nordsee("nordsee_terms_2026.pdf", "1 June 2026", 45, 20, 400, 15, "12:00")
    pdf("gulfstream_terms_2026.pdf", f"{GULF}: conditions of sale",
        "Issued 3 March 2026. Synthetic demonstration document.", [
            ("Prices and currency", ["All prices are quoted in United States dollars (USD), ex works."]),
            ("Minimum order", ["The minimum order value is USD 500.", "Each part also carries a minimum order "
                               "quantity, shown in the catalogue. Quantities below it are raised to the minimum "
                               "and charged in full."]),
            ("Payment", ["Payment is due within 30 days of shipment."]),
            ("Lead time", ["Catalogue lead times are calendar days from receipt of a purchase order.",
                           "Add 3 calendar days for shipping to the port of delivery."]),
            ("Expedited orders", ["Expediting costs 10 percent of the goods value and saves 2 calendar days."]),
            ("Returns", ["Unused parts may be returned within 30 days with a 20 percent restocking fee."])])
    pdf("procurement_policy.pdf", "Fleet procurement policy",
        "Version 4, effective 1 April 2026. Synthetic demonstration document.", [
            ("Scope", ["This policy covers spare parts ordered for vessels in the fleet."]),
            ("Quotations", ["Compare at least two suppliers where two list the part.",
                            "Orders with a goods value above 5,000 in the order currency need two written "
                            "quotations."]),
            ("Approval", ["A purchaser may approve orders up to 2,000 in the order currency.",
                          "A technical superintendent approves orders above 2,000 and up to 10,000.",
                          "The fleet manager approves orders above 10,000."]),
            ("Currency", ["Each purchase order is raised in the currency quoted by the supplier."]),
            ("Part grade", ["Safety-critical parts for the main engine must be OEM grade.",
                            "Aftermarket parts may be used for pumps with superintendent agreement."]),
            ("Urgent orders", ["Express handling needs approval from a technical superintendent."]),
            ("Exceptions", ["Send any question this policy does not cover to the purchasing manager."])])
    print(f"wrote {count} catalogue rows and 4 PDFs to {OUT}")


if __name__ == "__main__":
    main()
