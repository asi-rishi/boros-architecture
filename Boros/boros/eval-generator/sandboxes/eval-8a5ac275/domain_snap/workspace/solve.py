
import json
from datetime import datetime, timedelta

def parse_datetime(dt_str):
    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))

def solve():
    with open('rules.json', 'r') as f:
        rules = json.load(f)
    with open('scenario.json', 'r') as f:
        scenario = json.load(f)

    legal_position = {
        "valid_contract_formed": {
            "status": False,
            "reasons": [],
            "overall_conclusion": ""
        },
        "breach_analysis": {
            "status": "N/A",
            "party_in_breach": "N/A",
            "type_of_breach": "N/A",
            "reasons": []
        },
        "available_remedies": {
            scenario["client_name"]: {
                "damages": 0,
                "specific_performance": False,
                "reasons": []
            },
            scenario["opponent_name"]: {
                "damages": 0,
                "specific_performance": False,
                "reasons": []
            }
        }
    }

    # --- 1. Offer Validity ---
    offer_info = scenario["offer"]
    offer_date = parse_datetime(offer_info["date"])
    acceptance_date = parse_datetime(scenario["acceptance"]["date"])
    offer_valid_at_acceptance = True
    offer_reasons = []

    # OFF_001: Offer Expiry
    off_001_rule = next((rule for rule in rules["offer"] if rule["id"] == "OFF_001"), None)
    if not offer_info["expiry_stated"]:
        expiry_time = offer_date + timedelta(hours=48)
        if acceptance_date > expiry_time:
            offer_valid_at_acceptance = False
            offer_reasons.append({
                "rule_id": "OFF_001",
                "description": f"Offer from {offer_info['party']} made on {offer_info['date']} had no stated expiry, so it defaulted to 48 hours (expired {expiry_time.isoformat()}). {scenario['acceptance']['party']}'s acceptance on {scenario['acceptance']['date']} was after this timeframe.",
                "conclusion": "Offer had expired."
            })
        else:
            offer_reasons.append({
                "rule_id": "OFF_001",
                "description": f"Offer from {offer_info['party']} made on {offer_info['date']} had no stated expiry, so it defaulted to 48 hours (expires {expiry_time.isoformat()}). {scenario['acceptance']['party']}'s acceptance on {scenario['acceptance']['date']} was within this timeframe.",
                "conclusion": "Offer was valid at time of acceptance."
            })
    else:
        # Assuming expiry_stated is a datetime string if present
        stated_expiry = parse_datetime(offer_info["expiry_stated"])
        if acceptance_date > stated_expiry:
            offer_valid_at_acceptance = False
            offer_reasons.append({
                "rule_id": "OFF_001",
                "description": f"Offer from {offer_info['party']} made on {offer_info['date']} had a stated expiry of {offer_info['expiry_stated']}. {scenario['acceptance']['party']}'s acceptance on {scenario['acceptance']['date']} was after this timeframe.",
                "conclusion": "Offer had expired."
            })
        else:
            offer_reasons.append({
                "rule_id": "OFF_001",
                "description": f"Offer from {offer_info['party']} made on {offer_info['date']} had a stated expiry of {offer_info['expiry_stated']}. {scenario['acceptance']['party']}'s acceptance on {scenario['acceptance']['date']} was within this timeframe.",
                "conclusion": "Offer was valid at time of acceptance."
            })

    # OFF_002: Offer Revocation
    off_002_rule = next((rule for rule in rules["offer"] if rule["id"] == "OFF_002"), None)
    if offer_info["revocation"]:
        revocation_date = parse_datetime(offer_info["revocation"]["date"])
        if revocation_date < acceptance_date:
            # Check revocation channel (simplified for now, assuming "same or more direct" is met if revocation exists and is before acceptance)
            offer_valid_at_acceptance = False
            offer_reasons.append({
                "rule_id": "OFF_002",
                "description": f"Offer from {offer_info['party']} was revoked on {offer_info['revocation']['date']} before {scenario['acceptance']['party']}'s acceptance on {scenario['acceptance']['date']}.",
                "conclusion": "Offer was revoked before acceptance."
            })
        else:
            offer_reasons.append({
                "rule_id": "OFF_002",
                "description": f"Offer from {offer_info['party']} was revoked on {offer_info['revocation']['date']}, which was after {scenario['acceptance']['party']}'s acceptance on {scenario['acceptance']['date']}.",
                "conclusion": "Revocation was ineffective as it occurred after acceptance."
            })
    else:
         offer_reasons.append({
            "rule_id": "OFF_002",
            "description": f"No revocation was made for the offer from {offer_info['party']}.",
            "conclusion": "Offer was not revoked."
        })

    # --- 2. Acceptance Validity ---
    acceptance_info = scenario["acceptance"]
    acceptance_valid = True
    acceptance_reasons = []

    # ACC_001: Acceptance Method
    acc_001_rule = next((rule for rule in rules["acceptance"] if rule["id"] == "ACC_001"), None)
    valid_channels = ["email", "physical letter", "video conference call"]
    if acceptance_info["channel"] not in valid_channels:
        acceptance_valid = False
        acceptance_reasons.append({
            "rule_id": "ACC_001",
            "description": f"Acceptance method was invalid. {acceptance_info['party']} accepted via '{acceptance_info['channel']}', which is explicitly disallowed by rule ACC_001. Only '{', '.join(valid_channels)}' are valid.",
            "conclusion": "Acceptance was invalid due to improper method."
        })
    else:
        acceptance_reasons.append({
            "rule_id": "ACC_001",
            "description": f"Acceptance method was valid. {acceptance_info['party']} accepted via '{acceptance_info['channel']}'.",
            "conclusion": "Acceptance method was valid."
        })

    # ACC_002: Mirror Image Rule
    acc_002_rule = next((rule for rule in rules["acceptance"] if rule["id"] == "ACC_002"), None)
    if offer_info["terms"] != acceptance_info["terms_accepted"]:
        acceptance_valid = False
        acceptance_reasons.append({
            "rule_id": "ACC_002",
            "description": f"Acceptance did not mirror the offer exactly. Offer terms: {offer_info['terms']}, Accepted terms: {acceptance_info['terms_accepted']}. This constitutes a counter-offer, not an acceptance.",
            "conclusion": "Acceptance was invalid as it deviated from the offer (counter-offer)."
        })
    else:
        acceptance_reasons.append({
            "rule_id": "ACC_002",
            "description": f"Acceptance mirrored the offer exactly. Offer terms: {offer_info['terms']}, Accepted terms: {acceptance_info['terms_accepted']}.",
            "conclusion": "Acceptance mirrored the offer."
        })

    # --- 3. Consideration Validity ---
    consideration_info = scenario["consideration_exchange"]
    consideration_valid = True
    consideration_reasons = []

    # CON_001: Valuable Consideration
    con_001_rule = next((rule for rule in rules["consideration"] if rule["id"] == "CON_001"), None)
    if consideration_info["currency"] != "USD" or consideration_info["amount"] <= 100 or consideration_info["type"] == "past":
        consideration_valid = False
        consideration_reasons.append({
            "rule_id": "CON_001",
            "description": f"Consideration was invalid. The consideration was {consideration_info['amount']} {consideration_info['currency']} of type '{consideration_info['type']}'. Rule CON_001 requires explicitly monetary consideration, greater than $100, and not past consideration.",
            "conclusion": "Consideration was invalid."
        })
    else:
        consideration_reasons.append({
            "rule_id": "CON_001",
            "description": f"Consideration was valid. The consideration was {consideration_info['amount']} {consideration_info['currency']} of type '{consideration_info['type']}'.",
            "conclusion": "Consideration was valid."
        })

    # --- 4. Contract Formation ---
    all_reasons = offer_reasons + acceptance_reasons + consideration_reasons
    if offer_valid_at_acceptance and acceptance_valid and consideration_valid:
        legal_position["valid_contract_formed"]["status"] = True
        legal_position["valid_contract_formed"]["overall_conclusion"] = "A valid contract was formed."
    else:
        legal_position["valid_contract_formed"]["status"] = False
        legal_position["valid_contract_formed"]["overall_conclusion"] = "No valid contract was formed due to one or more invalid elements."
    legal_position["valid_contract_formed"]["reasons"] = all_reasons

    # --- 5. Breach Analysis ---
    if legal_position["valid_contract_formed"]["status"]:
        legal_position["breach_analysis"]["status"] = "Analyzed"
        breach_found = False
        breach_reasons = []
        for perf in scenario["performance"]:
            if perf.get("constitutes_breach"):
                breach_found = True
                legal_position["breach_analysis"]["party_in_breach"] = perf["party"]
                
                # BRE_001: Material Breach Definition
                bre_001_rule = next((rule for rule in rules["breach"] if rule["id"] == "BRE_001"), None)
                if perf["breach_type_claimed_by_opponent"] == "material" or (bre_001_rule and perf["action"]): # Simplified for now, rule implies any failure to perform is material
                    legal_position["breach_analysis"]["type_of_breach"] = "material"
                    breach_reasons.append({
                        "rule_id": "BRE_001",
                        "description": f"Failure to perform by {perf['party']}: '{perf['action']}'. This is classified as a material breach according to rule BRE_001.",
                        "conclusion": f"{perf['party']} committed a material breach."
                    })
                else:
                    legal_position["breach_analysis"]["type_of_breach"] = "minor" # Or other types if defined in rules
                    breach_reasons.append({
                        "rule_id": None, # No specific rule for minor breach if not material
                        "description": f"Failure to perform by {perf['party']}: '{perf['action']}'. This is classified as a minor breach.",
                        "conclusion": f"{perf['party']} committed a minor breach."
                    })
                # Assuming only one breach for simplicity for now
                break 
        
        if not breach_found:
            legal_position["breach_analysis"]["overall_conclusion"] = "No breach identified."
            legal_position["breach_analysis"]["status"] = "No Breach"
        else:
            legal_position["breach_analysis"]["overall_conclusion"] = f"A breach was identified. {legal_position['breach_analysis']['party_in_breach']} is in breach."
        legal_position["breach_analysis"]["reasons"] = breach_reasons
    else:
        legal_position["breach_analysis"]["overall_conclusion"] = "No contract was formed, thus breach analysis is not applicable."


    # --- 6. Remedies Calculation ---
    client_name = scenario["client_name"]
    opponent_name = scenario["opponent_name"]

    if legal_position["valid_contract_formed"]["status"] and legal_position["breach_analysis"]["status"] == "Analyzed":
        party_in_breach = legal_position["breach_analysis"]["party_in_breach"]
        
        for party in [client_name, opponent_name]:
            damages_calc = 0
            remedy_reasons = []
            
            if party == party_in_breach:
                # The party in breach doesn't typically get damages for *their own* breach
                remedy_reasons.append({"rule_id": None, "description": f"{party} is the breaching party, therefore no damages are awarded to them for this breach.", "conclusion": "No damages for breaching party."})
            else:
                # Calculate damages for the non-breaching party
                if party == client_name:
                    incurred_damages = scenario["damages_incurred"].get(client_name, {})
                else:
                    incurred_damages = scenario["damages_incurred"].get(opponent_name, {})

                lost_profit = incurred_damages.get("lost_profit", 0)
                expenses_incurred = incurred_damages.get("expenses_incurred", 0)
                disruption_costs = incurred_damages.get("disruption_costs", 0)

                damages_calc = lost_profit + expenses_incurred + disruption_costs
                
                # REM_001: Damages Cap
                rem_001_rule = next((rule for rule in rules["remedies"] if rule["id"] == "REM_001"), None)
                if rem_001_rule:
                    original_contract_value = scenario["offer"]["terms"].get("price", 0) # Assuming 'price' is the contract value
                    damages_cap = 1.25 * original_contract_value
                    if damages_calc > damages_cap:
                        damages_calc = damages_cap
                        remedy_reasons.append({
                            "rule_id": "REM_001",
                            "description": f"Calculated damages for {party} ({lost_profit + expenses_incurred + disruption_costs}) exceeded the cap of 1.25 times the original contract value (${original_contract_value * 1.25}). Damages capped at ${damages_cap}.",
                            "conclusion": f"Monetary damages capped at ${damages_cap}."
                        })
                    else:
                        remedy_reasons.append({
                            "rule_id": "REM_001",
                            "description": f"Calculated damages for {party} (${lost_profit + expenses_incurred + disruption_costs}) are within the cap of 1.25 times the original contract value (${original_contract_value * 1.25}).",
                            "conclusion": f"Monetary damages not capped."
                        })
                
                remedy_reasons.append({"rule_id": None, "description": f"Calculated direct damages for {party}: ${damages_calc}", "conclusion": f"Damages awarded: ${damages_calc}"})

            # REM_002: Specific Performance
            rem_002_rule = next((rule for rule in rules["remedies"] if rule["id"] == "REM_002"), None)
            specific_performance_available = False
            if rem_002_rule and rem_002_rule["action"] == "DENY_SPECIFIC_PERFORMANCE":
                specific_performance_available = False
                remedy_reasons.append({
                    "rule_id": "REM_002",
                    "description": "Specific performance is never an available remedy under any circumstances, as per rule REM_002.",
                    "conclusion": "Specific performance denied."
                })
            else:
                 specific_performance_available = True
                 remedy_reasons.append({
                    "rule_id": "REM_002",
                    "description": "Specific performance is a potentially available remedy.",
                    "conclusion": "Specific performance is potentially available."
                })

            legal_position["available_remedies"][party]["damages"] = damages_calc
            legal_position["available_remedies"][party]["specific_performance"] = specific_performance_available
            legal_position["available_remedies"][party]["reasons"] = remedy_reasons

    else:
        # No contract or no breach, so no remedies
        for party in [client_name, opponent_name]:
            legal_position["available_remedies"][party]["damages"] = 0
            legal_position["available_remedies"][party]["specific_performance"] = False
            legal_position["available_remedies"][party]["reasons"].append({"rule_id": None, "description": "No contract was formed or no breach was identified, thus no remedies for breach are available.", "conclusion": "No remedies available."})


    with open('legal_position.json', 'w') as f:
        json.dump(legal_position, f, indent=2)

if __name__ == "__main__":
    solve()
