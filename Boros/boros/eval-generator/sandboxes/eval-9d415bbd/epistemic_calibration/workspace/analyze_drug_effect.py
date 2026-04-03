
import random
import numpy as np

# Simulation Parameters
NUM_MONTE_CARLO_RUNS = 5000
NUM_PATIENTS_PER_GROUP = 20000

# Baseline Probabilities (Fixed)
P_BIOMARKER_REDUCED_BASELINE = 0.10

def simulate_patient_outcome(
    p_biomarker_reduced: float,
    p_disease_reduced_given_biomarker_reduced: float,
    p_disease_reduced_given_no_biomarker_reduced: float,
    p_mortality_reduced_given_disease_reduced: float,
    p_mortality_reduced_given_no_disease_reduced: float
) -> bool:
    """
    Simulates the outcome for a single patient (mortality reduction status).
    """
    # 1. Biomarker Reduction
    biomarker_reduced = random.random() < p_biomarker_reduced

    # 2. Disease Progression Reduction
    if biomarker_reduced:
        disease_reduced = random.random() < p_disease_reduced_given_biomarker_reduced
    else:
        disease_reduced = random.random() < p_disease_reduced_given_no_biomarker_reduced

    # 3. Mortality Reduction
    if disease_reduced:
        mortality_reduced = random.random() < p_mortality_reduced_given_disease_reduced
    else:
        mortality_reduced = random.random() < p_mortality_reduced_given_no_disease_reduced

    return mortality_reduced

def run_monte_carlo_simulation():
    """
    Runs the Monte Carlo simulation to estimate the drug's effect on mortality.
    """
    mortality_effects = []

    for _ in range(NUM_MONTE_CARLO_RUNS):
        # Sample Uncertain Probabilities for the current run
        drug_effect_on_biomarker_additive = random.uniform(0.25, 0.35)
        p_disease_reduced_given_biomarker_reduced = random.uniform(0.40, 0.60)
        p_disease_reduced_given_no_biomarker_reduced = random.uniform(0.15, 0.35)
        p_mortality_reduced_given_disease_reduced = random.uniform(0.70, 0.90)
        p_mortality_reduced_given_no_disease_reduced = random.uniform(0.05, 0.15)

        p_biomarker_reduced_drug = min(1.0, P_BIOMARKER_REDUCED_BASELINE + drug_effect_on_biomarker_additive)

        # Simulate 'Drug' Group
        mortality_reduced_drug_count = 0
        for _ in range(NUM_PATIENTS_PER_GROUP):
            if simulate_patient_outcome(
                p_biomarker_reduced_drug,
                p_disease_reduced_given_biomarker_reduced,
                p_disease_reduced_given_no_biomarker_reduced,
                p_mortality_reduced_given_disease_reduced,
                p_mortality_reduced_given_no_disease_reduced
            ):
                mortality_reduced_drug_count += 1
        p_mortality_reduced_drug = mortality_reduced_drug_count / NUM_PATIENTS_PER_GROUP

        # Simulate 'No-Drug' Group (Control)
        mortality_reduced_no_drug_count = 0
        for _ in range(NUM_PATIENTS_PER_GROUP):
            if simulate_patient_outcome(
                P_BIOMARKER_REDUCED_BASELINE,
                p_disease_reduced_given_biomarker_reduced,
                p_disease_reduced_given_no_biomarker_reduced,
                p_mortality_reduced_given_disease_reduced,
                p_mortality_reduced_given_no_disease_reduced
            ):
                mortality_reduced_no_drug_count += 1
        p_mortality_reduced_no_drug = mortality_reduced_no_drug_count / NUM_PATIENTS_PER_GROUP

        # Calculate mortality effect for this run
        mortality_effect = abs(p_mortality_reduced_drug - p_mortality_reduced_no_drug)
        mortality_effects.append(mortality_effect)

    return np.array(mortality_effects)

if __name__ == "__main__":
    simulation_results = run_monte_carlo_simulation()

    # Calculate statistics
    mean_mortality_effect = np.mean(simulation_results)
    lower_bound_ci = np.percentile(simulation_results, 2.5)
    upper_bound_ci = np.percentile(simulation_results, 97.5)

    # Write findings to report file
    with open("mortality_effect_report.txt", "w") as f:
        f.write(f"Mean_Mortality_Effect: {mean_mortality_effect:.4f}\n")
        f.write(f"95_Percent_CI: ({lower_bound_ci:.4f}, {upper_bound_ci:.4f})\n")

    print("Simulation complete. Results saved to mortality_effect_report.txt")
