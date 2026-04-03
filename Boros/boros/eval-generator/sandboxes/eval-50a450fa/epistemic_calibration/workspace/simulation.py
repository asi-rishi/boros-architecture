
import numpy as np

# Define Simulation Parameters
population_size = 100000
biomarker_x_mean = 100
biomarker_x_std_dev = 15
biomarker_x_threshold = 110
prob_disease_progression_low_x = 0.10
prob_disease_progression_high_x = 0.25
prob_mortality_no_progression = 0.05
prob_mortality_with_progression = 0.40
drug_biomarker_reduction_factor = 0.70

# --- Simulate Control Group (No Drug) ---
control_biomarker_x_values = np.random.normal(biomarker_x_mean, biomarker_x_std_dev, population_size)
control_deaths = 0

for biomarker_x in control_biomarker_x_values:
    # Determine disease progression
    if biomarker_x <= biomarker_x_threshold:
        has_disease_progression = np.random.rand() < prob_disease_progression_low_x
    else:
        has_disease_progression = np.random.rand() < prob_disease_progression_high_x

    # Determine mortality
    if has_disease_progression:
        is_mortal = np.random.rand() < prob_mortality_with_progression
    else:
        is_mortal = np.random.rand() < prob_mortality_no_progression

    if is_mortal:
        control_deaths += 1

control_mortality_rate = control_deaths / population_size

# --- Simulate Treatment Group (Drug Administered) ---
initial_biomarker_x_values = np.random.normal(biomarker_x_mean, biomarker_x_std_dev, population_size)
treated_biomarker_x_values = initial_biomarker_x_values * drug_biomarker_reduction_factor
treatment_deaths = 0

for biomarker_x in treated_biomarker_x_values:
    # Determine disease progression
    if biomarker_x <= biomarker_x_threshold:
        has_disease_progression = np.random.rand() < prob_disease_progression_low_x
    else:
        has_disease_progression = np.random.rand() < prob_disease_progression_high_x

    # Determine mortality
    if has_disease_progression:
        is_mortal = np.random.rand() < prob_mortality_with_progression
    else:
        is_mortal = np.random.rand() < prob_mortality_no_progression

    if is_mortal:
        treatment_deaths += 1

treatment_mortality_rate = treatment_deaths / population_size

# --- Output Results ---
with open("mortality_results.txt", "w") as f:
    f.write(f"Control Mortality Rate: {control_mortality_rate:.4f}\n")
    f.write(f"Treatment Mortality Rate: {treatment_mortality_rate:.4f}\n")
