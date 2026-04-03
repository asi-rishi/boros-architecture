
import numpy as np

def run_simulation(N=100000):
    mortality_reductions = []

    for _ in range(N):
        # 1. Drug's effect on Biomarker X reduction
        biomarker_X_reduction = np.random.normal(0.30, 0.03)
        biomarker_X_reduction = np.clip(biomarker_X_reduction, 0.20, 0.40)

        # 2. Biomarker X's impact on Disease Progression reduction
        X_to_DP_factor = np.random.uniform(0.05, 0.60)

        # 3. Disease Progression's impact on Mortality reduction
        DP_to_mortality_factor = np.random.uniform(0.40, 0.90)

        # Calculate overall proportional mortality reduction
        mortality_reduction = biomarker_X_reduction * X_to_DP_factor * DP_to_mortality_factor
        mortality_reductions.append(mortality_reduction)

    # Convert to numpy array for easier calculations
    mortality_reductions = np.array(mortality_reductions)

    # Calculate statistics
    mean_reduction = np.mean(mortality_reductions)
    median_reduction = np.median(mortality_reductions)
    percentile_2_5 = np.percentile(mortality_reductions, 2.5)
    percentile_97_5 = np.percentile(mortality_reductions, 97.5)

    return mean_reduction, median_reduction, percentile_2_5, percentile_97_5

if __name__ == "__main__":
    mean, median, p2_5, p97_5 = run_simulation()

    with open("mortality_simulation_results.txt", "w") as f:
        f.write(f"{mean:.4f}\n")
        f.write(f"{median:.4f}\n")
        f.write(f"{p2_5:.4f}\n")
        f.write(f"{p97_5:.4f}\n")
