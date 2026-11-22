"""Generates SAMPLE knowledge-base PDFs into data/ (illustrative content - replace with real documents).

Static policy files use descriptive names; real-time update files start with ``update_``.
Run:  python scripts/generate_sample_data.py
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
NOTE = "SAMPLE DOCUMENT for demonstration purposes - figures are illustrative, not official airline policy."

DOCS = {
    "baggage_policy_international.pdf": {
        "title": "WanderNest Baggage Policy - International Routes",
        "sections": [
            ("Checked baggage allowance (Economy)",
             "Economy passengers flying from BLR, DEL or BOM to LON or JFK may check in one bag of up to 23 kg. "
             "To DXB the Economy allowance is one bag of up to 25 kg, and to BKK it is one bag of up to 20 kg. "
             "Business class passengers on all routes may check in two bags of up to 32 kg each."),
            ("Cabin baggage",
             "Every passenger may carry one cabin bag of up to 7 kg with maximum dimensions of 55 x 35 x 25 cm, "
             "plus one small personal item such as a handbag or laptop bag. Liquids in cabin baggage must be in "
             "containers of 100 ml or less."),
            ("Excess and extra baggage",
             "Excess weight is charged at INR 1,500 per kg on routes to LON and JFK and INR 1,000 per kg on routes "
             "to DXB and BKK. An additional pre-booked bag costs a flat INR 6,000 when added at least 24 hours "
             "before departure; at the airport the excess rate applies. No single bag may exceed 32 kg."),
            ("Restricted items",
             "Power banks and spare lithium batteries (up to 100 Wh) must be carried in cabin baggage and never "
             "in checked baggage. Sharp objects, flammable liquids and aerosols above 100 ml are not permitted "
             "in the cabin."),
        ],
    },
    "refund_cancellation_policy.pdf": {
        "title": "WanderNest Refund and Cancellation Policy",
        "sections": [
            ("Free cancellation window",
             "Bookings made at least 7 days before departure can be cancelled free of charge within 24 hours of "
             "booking and receive a full refund."),
            ("Customer-initiated cancellations",
             "Cancelling more than 72 hours before departure carries a fee of INR 3,500 per passenger on "
             "international Economy tickets. Cancelling between 72 and 24 hours before departure forfeits 50% of "
             "the base fare. Cancelling within 24 hours of departure is non-refundable, except government taxes "
             "and airport fees which are always returned."),
            ("Airline-initiated cancellations and significant changes",
             "If the airline cancels a flight or changes the schedule significantly, the passenger may choose a "
             "full refund to the original form of payment, free rebooking on the next available flight, or a "
             "WanderNest travel voucher. For flights to or from the United States, refunds follow the US DOT "
             "mandate: within 7 business days for credit-card payments and within 20 calendar days for other "
             "payment methods."),
            ("Refund timelines",
             "Approved refunds are returned to the original payment method within 7 to 10 working days. "
             "Vouchers are issued immediately by email and are valid for 12 months."),
        ],
    },
    "visa_immigration_policy.pdf": {
        "title": "WanderNest Visa and Immigration Guide",
        "sections": [
            ("General guidance",
             "Passengers are responsible for holding valid travel documents. The passport must be valid for at "
             "least six months beyond the date of arrival and have at least two blank pages."),
            ("Requirements by destination for Indian passport holders",
             "LON (United Kingdom): a Standard Visitor visa is required before travel; allow about 3 weeks for "
             "processing. JFK (United States): a B1/B2 visitor visa is required; appointment wait times vary. "
             "DXB (UAE): a visa or e-visa must be obtained before travel. BKK (Thailand): requirements change "
             "often - always check the latest WanderNest visa bulletin before booking."),
            ("Denied boarding",
             "Airlines may deny boarding when documents are missing or invalid. Tickets denied for missing visas "
             "are treated as customer-initiated cancellations under the Refund and Cancellation Policy."),
        ],
    },
    "route_guide_BLR_DEL_BOM.pdf": {
        "title": "WanderNest Route Guide - Indian Hubs to International Destinations",
        "sections": [
            ("Routes served",
             "WanderNest sells flights from three Indian hubs - Bengaluru (BLR), Delhi (DEL) and Mumbai (BOM) - to "
             "four international destinations: London (LON), New York (JFK), Dubai (DXB) and Bangkok (BKK). "
             "All twelve hub-to-destination combinations are bookable."),
            ("Typical flight times",
             "BLR-LON about 10.5 hours, DEL-LON about 9 hours, BOM-LON about 9.5 hours; DEL-JFK about 15 hours "
             "non-stop; BLR-DXB about 4 hours; DEL-DXB about 3.5 hours; BOM-DXB about 3.5 hours; BLR-BKK about "
             "3.5 hours; DEL-BKK about 4 hours; BOM-BKK about 4.5 hours."),
            ("Busiest periods",
             "Demand peaks in May-June and December. Book at least 6 weeks ahead for the lowest fares on LON and "
             "JFK routes."),
        ],
    },
    "faq_general.pdf": {
        "title": "WanderNest Frequently Asked Questions",
        "sections": [
            ("Online check-in",
             "Online check-in opens 48 hours before departure and closes 60 minutes before departure for "
             "international flights. Arrive at the airport at least 3 hours before an international departure."),
            ("Changing a name or date",
             "Name corrections of up to three characters are free within 24 hours of booking. Date changes cost "
             "INR 2,500 per passenger plus any fare difference."),
            ("Special assistance",
             "Wheelchair, unaccompanied-minor and medical assistance can be requested at no charge up to 48 hours "
             "before departure from the My Trips page."),
            ("Travel vouchers",
             "When a flight is disrupted and the passenger accepts a voucher instead of a refund, WanderNest issues "
             "a voucher worth 110% of the unused fare. Vouchers can be used on any WanderNest route."),
            ("Contacting an agent",
             "Human agents are available 24 hours a day through the app. Typical response time is under 15 minutes."),
        ],
    },
    "safety_advisory_health_security.pdf": {
        "title": "WanderNest Travel Safety and Health Advisory",
        "sections": [
            ("Before you travel",
             "Check your government's official travel advisory for your destination, carry prescription medicines "
             "in their original packaging with a doctor's letter, and keep digital copies of your passport and "
             "visa."),
            ("Health requirements",
             "Some destinations may require proof of vaccination. Confirm requirements with the destination "
             "country's official health authority at least 4 weeks before departure."),
            ("Security at airports",
             "Arrive early to allow for security screening. Never leave baggage unattended and report suspicious "
             "items to airport staff."),
        ],
    },
    "update_fare_increase_air_india.pdf": {
        "title": "REAL-TIME UPDATE - Air India Fare and Surcharge Increase",
        "sections": [
            ("What changed",
             "Air India has increased the fuel surcharge on India-UK sectors (BLR, DEL and BOM to LON) by INR 2,500 "
             "per passenger for tickets issued from the effective date. Tickets issued before the effective date "
             "are not affected."),
            ("What passengers can do",
             "Passengers who have not yet paid can lock the previous fare for 24 hours using a WanderNest fare "
             "hold. Travellers who prefer a lower fare can compare alternative airlines on the same route or shift "
             "travel dates by a few days. The surcharge appears as a separate line on the invoice to avoid "
             "confusion and disputes."),
        ],
    },
    "update_weather_delay_advisory_del.pdf": {
        "title": "REAL-TIME UPDATE - Dense Fog Delays at Delhi (DEL)",
        "sections": [
            ("Situation",
             "Dense fog at Delhi airport is causing departure delays of 2 to 5 hours and some cancellations on "
             "flights from DEL to LON, JFK, DXB and BKK. Passengers should check flight status before leaving "
             "for the airport."),
            ("Passenger entitlements",
             "For delays longer than 3 hours WanderNest provides a meal voucher. For delays longer than 6 hours "
             "passengers may rebook free of charge or request a full refund. If the airline cancels the flight, "
             "the Airline-initiated cancellation rules in the Refund and Cancellation Policy apply."),
        ],
    },
    "update_strike_dot_refund_notice.pdf": {
        "title": "REAL-TIME UPDATE - Airline Staff Strike and Refund Rights",
        "sections": [
            ("Situation",
             "A strike by airline cabin and ground staff is disrupting flights on transatlantic and European "
             "routes, including some services to JFK and LON. Further cancellations are possible."),
            ("Refund rights",
             "Passengers whose flights are cancelled because of the strike are entitled to a full refund even if "
             "they were offered an alternative flight. For US routes the DOT refund mandate applies: refunds "
             "within 7 business days to credit cards and within 20 calendar days for other payment methods. "
             "WanderNest will also offer a rebooking on the next available flight or a voucher worth 110% of the "
             "unused fare."),
        ],
    },
    "update_visa_policy_shift_uk.pdf": {
        "title": "REAL-TIME UPDATE - UK Visa Processing and Baggage Rule Notice for LON Routes",
        "sections": [
            ("UK visa processing",
             "Standard Visitor visa processing times for Indian applicants are currently about 4 weeks, longer "
             "than the usual 3 weeks. Travellers booking BLR, DEL or BOM to LON are advised to apply at least 5 "
             "weeks before departure. Bookings can be changed free of charge if a visa is delayed beyond the "
             "travel date and the traveller provides the application receipt."),
            ("Baggage rules on LON routes",
             "New cabin security guidance applies on flights to London: power banks must travel in cabin "
             "baggage only and liquids must be in containers of 100 ml or less. The checked baggage allowance "
             "for BLR-LON, DEL-LON and BOM-LON is unchanged: 23 kg in Economy."),
        ],
    },
}


def build_pdf(path: Path, title: str, sections: list[tuple[str, str]]) -> None:
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Paragraph(NOTE, styles["Italic"]), Spacer(1, 0.5 * cm)]
    for heading, body in sections:
        story += [Paragraph(heading, styles["Heading2"]), Paragraph(body, styles["BodyText"]), Spacer(1, 0.3 * cm)]
    if path.name.startswith("baggage_policy"):
        table = Table([["Cabin", "Route", "Checked allowance"],
                       ["Economy", "BLR/DEL/BOM - LON, JFK", "1 bag, 23 kg"],
                       ["Economy", "BLR/DEL/BOM - DXB", "1 bag, 25 kg"],
                       ["Economy", "BLR/DEL/BOM - BKK", "1 bag, 20 kg"],
                       ["Business", "All routes", "2 bags, 32 kg each"]])
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                   ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue)]))
        story += [Paragraph("Allowance summary", styles["Heading2"]), table]
    SimpleDocTemplate(str(path), pagesize=A4, title=title, author="WanderNest Travels").build(story)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    for name, spec in DOCS.items():
        build_pdf(DATA_DIR / name, spec["title"], spec["sections"])
        print("wrote", name)


if __name__ == "__main__":
    main()
