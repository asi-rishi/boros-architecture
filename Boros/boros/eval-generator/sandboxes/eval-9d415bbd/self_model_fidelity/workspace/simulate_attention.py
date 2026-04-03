
import json
import numpy as np
from collections import deque
import os

def linear_transform(input_matrix, weights, bias):
    return input_matrix @ weights + bias

def softmax(x):
    exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))  # Subtract max for numerical stability
    return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

def simulate_sliding_window_attention(input_json_path):
    with open(input_json_path, 'r') as f:
        data = json.load(f)

    d_model = data['d_model']
    d_k = data['d_k']
    context_window_size = data['context_window_size']
    q_weights = np.array(data['q_weights'])
    q_bias = np.array(data['q_bias'])
    k_weights = np.array(data['k_weights'])
    k_bias = np.array(data['k_bias'])
    v_weights = np.array(data['v_weights'])
    v_bias = np.array(data['v_bias'])
    token_stream = data['token_stream']

    context_window = deque()
    context_token_ids = deque()

    os.makedirs('outputs', exist_ok=True)

    for step_number, (token_id, embedding_vector) in enumerate(token_stream):
        context_window.append(np.array(embedding_vector))
        context_token_ids.append(token_id)

        if len(context_window) > context_window_size:
            context_window.popleft()
            context_token_ids.popleft()

        X_window = np.array(list(context_window))

        Q = linear_transform(X_window, q_weights, q_bias)
        K = linear_transform(X_window, k_weights, k_bias)
        V = linear_transform(X_window, v_weights, v_bias)

        attention_scores_unscaled = Q @ K.T
        attention_scores_scaled = attention_scores_unscaled / np.sqrt(d_k)
        softmax_scores = softmax(attention_scores_scaled)
        full_attention_output = softmax_scores @ V

        new_token_output_vector = full_attention_output[-1, :].tolist()

        results = {
            "step_number": step_number,
            "current_token_ids_in_window": list(context_token_ids),
            "Q_matrix": Q.tolist(),
            "K_matrix": K.tolist(),
            "V_matrix": V.tolist(),
            "attention_scores_unscaled": attention_scores_unscaled.tolist(),
            "softmax_scores": softmax_scores.tolist(),
            "full_attention_output": full_attention_output.tolist(),
            "new_token_output_vector": new_token_output_vector
        }

        output_filename = f"outputs/step_{step_number}_results.json"
        with open(output_filename, 'w') as outfile:
            json.dump(results, outfile, indent=2)

if __name__ == '__main__':
    simulate_sliding_window_attention("input.json")
