import json

# Define e for the exp function
E = 2.718281828459045

def transpose(matrix):
    """Transposes a matrix (list of lists)."""
    if not matrix:
        return []
    return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0]))]

def matrix_multiply(A, B):
    """Multiplies two matrices A (M x N) and B (N x P)."""
    if not A or not B or not A[0] or not B[0] or len(A[0]) != len(B):
        # Handle cases with empty matrices or dimension mismatch
        raise ValueError("Matrix dimensions are not compatible for multiplication.")

    M, N = len(A), len(A[0])
    P = len(B[0])
    
    # Initialize result matrix with zeros
    C = [[0.0] * P for _ in range(M)]

    for i in range(M):
        for j in range(P):
            for k in range(N):
                C[i][j] += A[i][k] * B[k][j]
    return C

def softmax_rows(matrix):
    """Applies the softmax function to each row of a matrix."""
    result = []
    for row in matrix:
        # Numerically stable softmax: subtract max from row before exp
        max_val = max(row) if row else 0
        exp_row = [E**(x - max_val) for x in row]
        sum_exp_row = sum(exp_row)
        if sum_exp_row == 0:
            # Handle case where all elements are extremely small
            softmax_row = [0.0] * len(row)
        else:
            softmax_row = [x / sum_exp_row for x in exp_row]
        result.append(softmax_row)
    return result

def main():
    """Main function to execute the self-attention mechanism."""
    # 1. Read Inputs
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        with open('input_features.txt', 'r') as f:
            input_features = [[float(val) for val in line.strip().split()] for line in f if line.strip()]

    except FileNotFoundError as e:
        print(f"Error: {e.filename} not found.")
        return
    except json.JSONDecodeError:
        print("Error: config.json is not a valid JSON file.")
        return

    max_context_length = config['max_context_length']
    d_k = config['d_k']
    q_proj_matrix = config['q_proj_matrix']
    k_proj_matrix = config['k_proj_matrix']
    v_proj_matrix = config['v_proj_matrix']

    # 2. Context Truncation
    if len(input_features) > max_context_length:
        truncated_features = input_features[-max_context_length:]
    else:
        truncated_features = input_features

    # 3. Projection
    Q_matrix = matrix_multiply(truncated_features, q_proj_matrix)
    K_matrix = matrix_multiply(truncated_features, k_proj_matrix)
    V_matrix = matrix_multiply(truncated_features, v_proj_matrix)

    # 4. Scaled Dot-Product Attention
    # Calculate Attention Scores
    K_matrix_T = transpose(K_matrix)
    attention_scores = matrix_multiply(Q_matrix, K_matrix_T)

    # Scale scores
    scaling_factor = d_k**0.5
    scaled_attention_scores = [[score / scaling_factor for score in row] for row in attention_scores]

    # Apply softmax
    attention_weights = softmax_rows(scaled_attention_scores)

    # Calculate final output
    output_matrix = matrix_multiply(attention_weights, V_matrix)

    # 5. Output
    with open('output_attended_features.txt', 'w') as f:
        for row in output_matrix:
            # Format each float to 4 decimal places
            formatted_row = [f"{val:.4f}" for val in row]
            f.write(" ".join(formatted_row) + '\n')

if __name__ == "__main__":
    main()
