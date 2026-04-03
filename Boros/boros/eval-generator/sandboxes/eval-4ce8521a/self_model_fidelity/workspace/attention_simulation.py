import math

def dot_product(v1, v2):
    """Calculates the dot product of two vectors."""
    return sum(x * y for x, y in zip(v1, v2))

def softmax(x):
    """Calculates the softmax of a list of numbers."""
    if not x:
        return []
    if len(x) == 1:
        return [1.0]
    e_x = [math.exp(i) for i in x]
    sum_e_x = sum(e_x)
    return [j / sum_e_x for j in e_x]

def sqrt(n):
    """Calculates the square root of a number."""
    return math.sqrt(n)

def simulate_attention_window(tokens_stream, context_window_size, output_filepath):
    """
    Simulates a simplified self-attention mechanism with a sliding context window.
    """
    context_window = []
    dim_embedding = len(tokens_stream[0]) if tokens_stream else 0
    sqrt_dim = sqrt(dim_embedding) if dim_embedding > 0 else 1.0

    with open(output_filepath, 'w') as f:
        for i, incoming_token in enumerate(tokens_stream):
            f.write(f"Processing Token {i}\n")
            f.write(f"Incoming Token (Query): {incoming_token}\n")
            f.write(f"Context Window Before Update: {context_window if context_window else '[]'}\n")

            # Manage context window
            removed_token = None
            context_window.append(incoming_token)
            if len(context_window) > context_window_size:
                removed_token = context_window.pop(0)
            
            f.write(f"Oldest Token Removed: {removed_token if removed_token else 'None'}\n")
            f.write(f"Context Window After Update: {context_window}\n")

            # Self-attention calculation
            query = incoming_token
            keys = context_window
            values = context_window  # In this simplified setup, keys and values are the same

            f.write(f"Keys/Values for Attention (Current Window): {keys}\n")

            # Raw attention scores
            raw_scores = [dot_product(query, key) for key in keys]
            f.write(f"Raw Attention Scores (Dot Products): {raw_scores}\n")

            # Scaled attention scores
            scaled_scores = [score / sqrt_dim for score in raw_scores]
            f.write(f"Scaled Attention Scores (divided by sqrt(dim)): {scaled_scores}\n")

            # Softmax attention weights
            attention_weights = softmax(scaled_scores)
            f.write(f"Softmax Attention Weights: {attention_weights}\n")

            # Attended output vector
            attended_output = [0.0] * dim_embedding
            for weight, value_vector in zip(attention_weights, values):
                for j in range(dim_embedding):
                    attended_output[j] += weight * value_vector[j]
            
            f.write(f"Attended Output Vector: {attended_output}\n")
            f.write("---\n")

if __name__ == '__main__':
    tokens = [
        [1.0, 0.0],  # Token 0
        [0.0, 1.0],  # Token 1
        [1.0, 1.0],  # Token 2
        [0.5, 0.5],  # Token 3
        [2.0, 0.0]   # Token 4
    ]
    context_window_size = 3
    output_file = "attention_log.txt"
    
    simulate_attention_window(tokens, context_window_size, output_file)
    
    print(f"Attention simulation log written to {output_file}")
    
    # Optional: print the content of the file to verify
    # with open(output_file, 'r') as f:
    #     print("\n--- File Content ---")
    #     print(f.read())

