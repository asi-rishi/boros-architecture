
import collections

def is_safe(state):
    farmer_bank, wolf_bank, goat_bank, cabbage_bank = state

    # Check West bank
    if farmer_bank == 'E':  # Farmer is on East, West bank is unattended
        if wolf_bank == 'W' and goat_bank == 'W':
            return False  # Wolf eats Goat
        if goat_bank == 'W' and cabbage_bank == 'W':
            return False  # Goat eats Cabbage

    # Check East bank
    if farmer_bank == 'W':  # Farmer is on West, East bank is unattended
        if wolf_bank == 'E' and goat_bank == 'E':
            return False  # Wolf eats Goat
        if goat_bank == 'E' and cabbage_bank == 'E':
            return False  # Goat eats Cabbage
    return True

def get_next_states(current_state):
    farmer_bank, wolf_bank, goat_bank, cabbage_bank = current_state
    
    items_on_farmer_bank = []
    if wolf_bank == farmer_bank:
        items_on_farmer_bank.append('Wolf')
    if goat_bank == farmer_bank:
        items_on_farmer_bank.append('Goat')
    if cabbage_bank == farmer_bank:
        items_on_farmer_bank.append('Cabbage')

    next_bank = 'E' if farmer_bank == 'W' else 'W'
    possible_moves = []

    # Farmer moves alone
    new_state_alone = (next_bank, wolf_bank, goat_bank, cabbage_bank)
    if is_safe(new_state_alone):
        move_description = f"Farmer takes alone from {farmer_bank} to {next_bank}."
        possible_moves.append((new_state_alone, move_description))

    # Farmer moves with an item
    for item in items_on_farmer_bank:
        new_wolf_bank = next_bank if item == 'Wolf' else wolf_bank
        new_goat_bank = next_bank if item == 'Goat' else goat_bank
        new_cabbage_bank = next_bank if item == 'Cabbage' else cabbage_bank
        
        new_state_with_item = (next_bank, new_wolf_bank, new_goat_bank, new_cabbage_bank)
        if is_safe(new_state_with_item):
            move_description = f"Farmer takes {item} from {farmer_bank} to {next_bank}."
            possible_moves.append((new_state_with_item, move_description))
            
    return possible_moves

def solve_puzzle():
    initial_state = ('W', 'W', 'W', 'W')  # (Farmer, Wolf, Goat, Cabbage)
    goal_state = ('E', 'E', 'E', 'E')

    queue = collections.deque([(initial_state, [])])  # (state, list_of_moves_to_reach_this_state)
    visited = set([initial_state])

    while queue:
        current_state, path = queue.popleft()

        if current_state == goal_state:
            return path

        for next_state, move_description in get_next_states(current_state):
            if next_state not in visited:
                visited.add(next_state)
                new_path = path + [move_description]
                queue.append((next_state, new_path))
    
    return None # No solution found

if __name__ == "__main__":
    solution_path = solve_puzzle()

    if solution_path:
        with open("solution.txt", "w") as f:
            for move in solution_path:
                f.write(move + "\n")
        print("Solution found and written to solution.txt")
    else:
        print("No solution found.")
