
import json
from itertools import chain, combinations

def find_counter_example():
    """
    Reads a list of companies, finds a counter-example to a logical argument,
    and writes the results to output files.
    """
    try:
        with open('companies.json', 'r') as f:
            companies = json.load(f)
    except FileNotFoundError:
        print("Error: companies.json not found.")
        return

    # Generate all non-empty subsets of companies
    all_subsets = list(chain.from_iterable(combinations(companies, r) for r in range(1, len(companies) + 1)))

    found_counter_example = False
    counter_example_company = None

    for subset in all_subsets:
        # Premise 1: All successful companies in the subset have strong cultures.
        premise_1_holds = True
        for company in subset:
            if company['is_successful'] and not company['has_strong_culture']:
                premise_1_holds = False
                break
        
        if premise_1_holds:
            # Look for a company X in the subset that satisfies the other conditions
            for company_x in subset:
                # Premise 2: Company X has a strong culture.
                premise_2_holds = company_x['has_strong_culture']
                
                # Conclusion is false: Company X is not successful.
                conclusion_is_false = not company_x['is_successful']

                if premise_2_holds and conclusion_is_false:
                    found_counter_example = True
                    counter_example_company = company_x
                    break # Found a counter-example company
            
        if found_counter_example:
            break # Found a counter-example scenario

    # Write the results to the output files
    if found_counter_example:
        with open('validation_result.txt', 'w') as f:
            f.write('ARGUMENT_IS_INVALID: True')
        with open('counter_example_company_name.txt', 'w') as f:
            f.write(counter_example_company['name'])
    else:
        with open('validation_result.txt', 'w') as f:
            f.write('ARGUMENT_IS_INVALID: False')
        with open('counter_example_company_name.txt', 'w') as f:
            # Empty file
            pass

if __name__ == "__main__":
    find_counter_example()
