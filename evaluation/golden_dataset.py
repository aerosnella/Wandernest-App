"""Golden dataset for RAGAS: questions with reference answers that match data/ (sample PDFs).

Replace/extend these entries if you change the knowledge base.
"""

GOLDEN_DATASET = [
    {"question": "What is the checked baggage allowance for Economy passengers flying from BLR to London?",
     "ground_truth": "Economy passengers flying to LON may check in one bag of up to 23 kg."},
    {"question": "How much is charged per kg for excess baggage on routes to JFK?",
     "ground_truth": "Excess weight on routes to LON and JFK is charged at INR 1,500 per kg."},
    {"question": "Can I pack a power bank in my checked bag?",
     "ground_truth": "No. Power banks and spare lithium batteries up to 100 Wh must be carried in cabin baggage, "
                     "not in checked baggage."},
    {"question": "What is the cancellation fee if I cancel an international Economy ticket more than 72 hours "
                 "before departure?",
     "ground_truth": "Cancelling more than 72 hours before departure carries a fee of INR 3,500 per passenger "
                     "on international Economy tickets."},
    {"question": "How quickly must refunds be paid on US routes when the airline cancels my flight?",
     "ground_truth": "Under the US DOT mandate, refunds are paid within 7 business days for credit-card payments "
                     "and within 20 calendar days for other payment methods."},
    {"question": "Is the BLR-LON route affected by the new baggage rules?",
     "ground_truth": "The checked baggage allowance for BLR-LON is unchanged at 23 kg in Economy, but power banks "
                     "must travel in cabin baggage only and liquids must be in containers of 100 ml or less."},
    {"question": "How long does UK visa processing take at the moment?",
     "ground_truth": "Standard Visitor visa processing is currently about 4 weeks, so travellers should apply at "
                     "least 5 weeks before departure."},
    {"question": "What happens if a strike cancels my flight to JFK?",
     "ground_truth": "The passenger is entitled to a full refund, and under the DOT mandate it is paid within 7 "
                     "business days to credit cards and 20 calendar days otherwise; WanderNest also offers "
                     "rebooking or a voucher worth 110% of the unused fare."},
    {"question": "What do I get if my flight from Delhi is delayed by more than 6 hours because of fog?",
     "ground_truth": "For delays longer than 6 hours passengers may rebook free of charge or request a full "
                     "refund; a meal voucher is provided for delays longer than 3 hours."},
    {"question": "By how much did Air India increase the fuel surcharge on India-UK routes?",
     "ground_truth": "The fuel surcharge on India-UK sectors increased by INR 2,500 per passenger."},
    {"question": "When does online check-in open for international flights?",
     "ground_truth": "Online check-in opens 48 hours before departure and closes 60 minutes before departure."},
    {"question": "What is the cabin baggage limit?",
     "ground_truth": "One cabin bag of up to 7 kg with dimensions of at most 55 x 35 x 25 cm, plus one small "
                     "personal item."},
]
