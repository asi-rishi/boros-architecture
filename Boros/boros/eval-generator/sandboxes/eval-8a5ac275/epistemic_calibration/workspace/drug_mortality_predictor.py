
import sys
import random

def simulate_drug_effect(num_patients):
    reduced_mortality_count = 0

    for _ in range(num_patients):
        biomarker_x_reduced = random.random() < 0.80

        disease_progression_improved = False
        if biomarker_x_reduced:
            disease_progression_improved = random.random() < 0.60

        mortality_risk_reduced = False
        if disease_progression_improved:
            mortality_risk_reduced = random.random() < 0.75

        if mortality_risk_reduced:
            reduced_mortality_count += 1

    return reduced_mortality_count

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python drug_mortality_predictor.py <num_patients>")
        sys.exit(1)

    try:
        num_patients = int(sys.argv[1])
    except ValueError:
        print("Error: num_patients must be an integer.")
        sys.exit(1)

    if num_patients <= 0:
        print("Error: num_patients must be a positive integer.")
        sys.exit(1)

    reduced_mortality = simulate_drug_effect(num_patients)
    estimated_probability = reduced_mortality / num_patients

    with open("mortality_effect_estimate.txt", "w") as f:
        f.write(f"{estimated_probability:.2f}")

    print(f"Simulation complete. Estimated probability written to mortality_effect_estimate.txt")
