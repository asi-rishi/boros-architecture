
def is_safe(state):
    """
    Checks if a given state is safe (no one gets eaten).
    A state is unsafe if:
    - Wolf and Goat are on the same bank, and the Farmer is not.
    - Goat and Cabbage are on the same bank, and the Farmer is not.
    """
    F, W, G, C = state
    if W == G and F != W:
        return False
    if G == C and F != G:
        return False
    return True

def get_next_states(state):
    """
    Generates all possible next states from the current state.
    The farmer can cross alone or with one item from his current bank.
    """
    F, W, G, C = state
    next_states = []
    
    # Farmer crosses alone
    next_states.append((1 - F, W, G, C))
    
    # Farmer crosses with Wolf
    if F == W:
        next_states.append((1 - F, 1 - W, G, C))
        
    # Farmer crosses with Goat
    if F == G:
        next_states.append((1 - F, W, 1 - G, C))
        
    # Farmer crosses with Cabbage
    if F == C:
        next_states.append((1 - F, W, G, 1 - C))
        
    return next_states

def solve():
    """
    Finds a solution to the river puzzle using Breadth-First Search (BFS).
    """
    initial_state = (0, 0, 0, 0)
    goal_state = (1, 1, 1, 1)
    
    # The queue will store paths (lists of states)
    queue = [[initial_state]]
    visited = {initial_state}
    
    while queue:
        path = queue.pop(0)
        current_state = path[-1]
        
        if current_state == goal_state:
            return path
            
        for next_state in get_next_states(current_state):
            if is_safe(next_state) and next_state not in visited:
                visited.add(next_state)
                new_path = list(path)
                new_path.append(next_state)
                queue.append(new_path)
                
    return None

if __name__ == "__main__":
    solution_path = solve()
    
    if solution_path:
        with open("solution.txt", "w") as f:
            for state in solution_path:
                f.write(str(state) + "\n")
        print("Solution found and written to solution.txt")
    else:
        print("No solution found.")

