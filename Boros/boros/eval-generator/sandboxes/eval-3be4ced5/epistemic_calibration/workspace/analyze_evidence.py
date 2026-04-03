
import json

def analyze_evidence_chain(input_file="input.json", output_file="output.json"):
    """
    Analyzes a chain of evidence from a JSON file to determine the overall effect
    on mortality and the confidence level.

    Args:
        input_file (str): The name of the input JSON file.
        output_file (str): The name of the output JSON file.
    """
    try:
        with open(input_file, 'r') as f:
            evidence_links = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return

    # Confidence and effect mappings
    confidence_map = {
        "low": 0.2,
        "mixed": 0.4,
        "moderate": 0.6,
        "high": 0.8
    }
    effect_multiplier_map = {
        "reduces": -1,
        "increases": 1,
        "correlates_positively": 1,
        "correlates_negatively": -1
    }

    # Reorder the chain
    chain = []
    next_source = "Drug"
    links_dict = {link['source']: link for link in evidence_links}

    while next_source in links_dict and next_source != "Mortality":
        link = links_dict[next_source]
        chain.append(link)
        next_source = link['target']

    # Calculate overall effect
    overall_effect_multiplier = 1
    for link in chain:
        effect_type = link.get("effect_type")
        multiplier = effect_multiplier_map.get(effect_type, 0)
        overall_effect_multiplier *= multiplier

    if overall_effect_multiplier == -1:
        overall_effect_on_mortality = "DECREASE"
    elif overall_effect_multiplier == 1:
        overall_effect_on_mortality = "INCREASE"
    else:
        overall_effect_on_mortality = "UNCLEAR"

    # Calculate overall confidence
    numeric_confidences = [confidence_map.get(link.get("confidence_qualitative"), 0) for link in chain]
    if not numeric_confidences:
        overall_numeric_confidence = 0
    else:
        overall_numeric_confidence = min(numeric_confidences)

    if overall_numeric_confidence <= 0.25:
        overall_confidence_level = "VERY_LOW"
    elif 0.25 < overall_numeric_confidence <= 0.5:
        overall_confidence_level = "LOW"
    elif 0.5 < overall_numeric_confidence <= 0.75:
        overall_confidence_level = "MODERATE"
    else:
        overall_confidence_level = "HIGH"
        
    # Prepare and write the output
    output_data = {
        "overall_effect_on_mortality": overall_effect_on_mortality,
        "overall_confidence_level": overall_confidence_level
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=4)

    print(f"Analysis complete. Output written to '{output_file}'.")

if __name__ == "__main__":
    analyze_evidence_chain()
