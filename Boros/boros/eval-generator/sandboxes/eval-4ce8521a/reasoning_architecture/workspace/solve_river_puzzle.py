
import collections

def is_valid(state):
    """Checks if a state is valid."""
    F, W, G, C = state
    # Wolf eats Goat
    if W == G and F != W:
        return False
    # Goat eats Cabbage
    if G == C and F != G:
        return False
    return True

def get_next_states(state):
    """Generates all possible valid next states from the current state."""
    F, W, G, C = state
    next_states = []
    
    # Farmer crosses alone
    next_F = 1 - F
    next_states.append(((next_F, W, G, C), "None"))

    # Farmer crosses with Wolf
    if F == W:
        next_states.append(((next_F, 1 - W, G, C), "Wolf"))

    # Farmer crosses with Goat
    if F == G:
        next_states.append(((next_F, W, 1 - G, C), "Goat"))

    # Farmer crosses with Cabbage
    if F == C:
        next_states.append(((next_F, W, G, 1 - C), "Cabbage"))
        
    return [(s, item) for s, item in next_states if is_valid(s)]

def solve():
    """Solves the river crossing puzzle using BFS."""
    start_state = (0, 0, 0, 0)
    goal_state = (1, 1, 1, 1)

    queue = collections.deque([[(start_state, "Initial State")]])
    visited = {start_state}

    while queue:
        path = queue.popleft()
        current_state, _ = path[-1]

        if current_state == goal_state:
            return path

        for next_state, item in get_next_states(current_state):
            if next_state not in visited:
                visited.add(next_state)
                new_path = path + [(next_state, item)]
                queue.append(new_path)

    return None

def main():
    """Main function to solve the puzzle and write the solution to a file."""
    solution = solve()
    if solution:
        with open("solution.txt", "w") as f:
            for i, (state, item) in enumerate(solution):
                f.write(f"{i}: {state} (Carried: {item})\n")
    else:
        print("No solution found.")

if __name__ == "__main__":
    main()
