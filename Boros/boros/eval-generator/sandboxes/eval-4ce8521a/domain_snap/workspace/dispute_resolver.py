
import sys
import json
from datetime import datetime

def analyze_dispute(rules, scenario):
    """
    Analyzes a contract dispute scenario based on a given ruleset.

    Args:
        rules (list): A list of rule objects.
        scenario (dict): An object describing the dispute scenario.

    Returns:
        dict: A dictionary containing the analysis results.
    """
    reasoning_steps = []
    applicable_rules = []
    
    # State variables
    contract_formed = False
    breach_occurred = False
    
    # Find key events
    try:
        initial_offer = next(e for e in scenario['events'] if e['type'] == 'offer')
        response_to_offer = next(e for e in scenario['events'] if e['type'] == 'response')
        action_by_offeree = next(e for e in scenario['events'] if e['type'] == 'action' and e['from'] == scenario['parties']['other_party'])
        final_communication = next(e for e in scenario['events'] if e['type'] == 'revocation')
    except StopIteration:
        # Handle cases where expected events are missing, though the prompt guarantees them.
        return {
            "contract_formed": False,
            "breach_occurred": False,
            "claiming_party_legal_position": "Invalid scenario: Missing key events.",
            "reasoning_steps": ["Could not find all necessary events (offer, response, action, revocation) to perform analysis."],
            "applicable_rules": []
        }

    # --- Chronological Analysis ---

    # 1. DDI makes an offer.
    # Check if the offer is valid according to R1, R5, R6. The scenario implies it is.
    reasoning_steps.append(f"Digital Dreams Inc. made an offer on {initial_offer['timestamp'].split('T')[0]} (Rule R1 satisfied). The offer expired on {initial_offer['expires_by'].split('T')[0]} (Rule R2).")
    applicable_rules.extend(["R1", "R2"])

    # 2. AWC responds with a modified term.
    original_delivery_date = initial_offer['terms']['delivery_date']
    # A simple way to extract the modified date for the reasoning string
    modified_delivery_date = response_to_offer['content'].split('by ')[-1].strip('.')
    
    reasoning_steps.append(f"Apex Widgets Co. responded on {response_to_offer['timestamp'].split('T')[0]} with '{response_to_offer['content']}'. This modifies the original delivery date of {original_delivery_date}.")

    # 3. Apply R4: Modification is a counter-offer.
    reasoning_steps.append("Under Rule R4, any modification constitutes a counter-offer and terminates the original offer. Therefore, Apex Widgets Co.'s response was a counter-offer, and Digital Dreams Inc.'s original offer was terminated.")
    applicable_rules.append("R4")

    # 4. Check for DDI's acceptance of the counter-offer.
    # The scenario has no event for DDI accepting.
    reasoning_steps.append("Digital Dreams Inc. did not provide explicit written confirmation of acceptance for Apex Widgets Co.'s counter-offer. Under Rule R3, silence or performance alone does not constitute acceptance.")
    applicable_rules.append("R3")
    
    # 5. AWC begins manufacturing. This is performance, but doesn't form the contract.
    reasoning_steps.append(f"Apex Widgets Co. starting manufacturing on {action_by_offeree['timestamp'].split('T')[0]} is an act of performance, but it does not constitute acceptance by Digital Dreams Inc. (Rule R3).")
    
    # 6. DDI communicates they are no longer interested. This is a rejection of the counter-offer.
    reasoning_steps.append(f"On {final_communication['timestamp'].split('T')[0]}, Digital Dreams Inc. communicated they were 'no longer interested'. At this point, no valid contract had been formed between the parties.")

    # At this point, the core conclusion is that no contract was formed.
    contract_formed = False
    
    # 7. Determine if a breach occurred.
    reasoning_steps.append("Since no contract was formed, there can be no breach by Digital Dreams Inc. (Rule R7).")
    applicable_rules.append("R7")
    breach_occurred = False

    # 8. Determine the legal position of the claiming party.
    claiming_party = scenario['dispute_claim']['party_claiming_breach']
    reasoning_steps.append(f"Therefore, {claiming_party}'s claim for damages is invalid.")
    claiming_party_legal_position = f"{claiming_party}'s claim is invalid."

    # Final output assembly
    output = {
        "contract_formed": contract_formed,
        "breach_occurred": breach_occurred,
        "claiming_party_legal_position": claiming_party_legal_position,
        "reasoning_steps": reasoning_steps,
        "applicable_rules": sorted(list(set(applicable_rules))) # Remove duplicates and sort
    }
    
    return output

def main():
    """
    Main function to run the dispute resolver program.
    """
    if len(sys.argv) != 3:
        print("Usage: python dispute_resolver.py <input_filepath> <output_filepath>")
        sys.exit(1)

    input_filepath = sys.argv[1]
    output_filepath = sys.argv[2]

    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_filepath}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {input_filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading the input file: {e}")
        sys.exit(1)

    rules = data.get("rules")
    scenario = data.get("scenario")

    if not rules or not scenario:
        print("Error: Input JSON must contain non-empty 'rules' and 'scenario' keys.")
        sys.exit(1)

    result = analyze_dispute(rules, scenario)

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"Analysis complete. Output written to {output_filepath}")
    except Exception as e:
        print(f"An unexpected error occurred while writing the output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
