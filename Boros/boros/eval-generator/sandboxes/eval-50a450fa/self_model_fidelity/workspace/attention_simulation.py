
import numpy as np
from scipy.special import softmax

# 1. Define Constants and Data
d_model = 4
context_window_size = 3

np.random.seed(42) # For reproducibility
token_embeddings = {
    0: np.random.rand(d_model),
    1: np.random.rand(d_model),
    2: np.random.rand(d_model),
    3: np.random.rand(d_model),
    4: np.random.rand(d_model),
    5: np.random.rand(d_model),
    6: np.random.rand(d_model),
    7: np.random.rand(d_model),
    8: np.random.rand(d_model),
    9: np.random.rand(d_model),
}

document_sequences = [
    [1, 2],
    [3, 4, 5],
    [6, 7, 8, 9],
    [0, 1, 2, 3, 4]
]

# 2. Implement simulate_self_attention(embeddings_batch) function
def simulate_self_attention(embeddings_batch):
    """
    Simulates a simplified self-attention mechanism.

    Args:
        embeddings_batch (numpy.ndarray): A batch of token embeddings
                                          of shape (seq_len, d_model).

    Returns:
        tuple: (output, attention_weights)
               output (numpy.ndarray): The attention output.
               attention_weights (numpy.ndarray): The attention weights matrix.
    """
    Q = embeddings_batch
    K = embeddings_batch
    V = embeddings_batch

    # Calculate attention scores
    scores = Q @ K.T

    # Apply scaling
    scores = scores / np.sqrt(d_model)

    # Apply softmax row-wise
    attention_weights = softmax(scores, axis=1)

    # Calculate the attention output
    output = attention_weights @ V

    return output, attention_weights

# 3. Process Documents and Generate Outputs
for idx, doc_seq in enumerate(document_sequences):
    # Apply Context Window
    truncated_seq = doc_seq[-context_window_size:]

    # Convert token IDs to embeddings
    embeddings_list = [token_embeddings[token_id] for token_id in truncated_seq]
    embeddings_batch = np.array(embeddings_list)

    # Call simulate_self_attention
    output, attention_weights = simulate_self_attention(embeddings_batch)

    # Save output
    output_filename = f"document_{idx}_output.txt"
    np.savetxt(output_filename, output, fmt='%.6f')
    print(f"Saved {output_filename}")

    # Save attention_weights if truncated sequence length equals context_window_size
    if len(truncated_seq) == context_window_size:
        attention_weights_filename = f"document_{idx}_attention_weights.txt"
        np.savetxt(attention_weights_filename, attention_weights, fmt='%.6f')
        print(f"Saved {attention_weights_filename}")
