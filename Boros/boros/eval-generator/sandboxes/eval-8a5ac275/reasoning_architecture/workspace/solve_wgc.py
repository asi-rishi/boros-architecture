from collections import deque

def solve_wgc():
    initial_state = ('L', 'L', 'L', 'L')  # (F, W, G, C)
    goal_state = ('R', 'R', 'R', 'R')

    # Queue for BFS: (state, path_to_state)
    queue = deque([(initial_state, [])])
    visited = {initial_state}

    while queue:
        current_state, path = queue.popleft()
        
        if current_state == goal_state:
            return path

        farmer_bank = current_state[0]
        
        # Determine items on the current bank with the farmer
        items_on_farmer_bank = []
        if current_state[1] == farmer_bank: items_on_farmer_bank.append('W')
        if current_state[2] == farmer_bank: items_on_farmer_bank.append('G')
        if current_state[3] == farmer_bank: items_on_farmer_bank.append('C')
        
        possible_moves = ['F'] # Farmer can always cross alone

        for item in items_on_farmer_bank:
            possible_moves.append(item)
            
        for move_item in possible_moves:
            next_state_list = list(current_state)
            
            # Farmer always moves
            next_farmer_bank = 'R' if farmer_bank == 'L' else 'L'
            next_state_list[0] = next_farmer_bank
            
            # If an item is moved, update its bank
            if move_item == 'W': next_state_list[1] = next_farmer_bank
            elif move_item == 'G': next_state_list[2] = next_farmer_bank
            elif move_item == 'C': next_state_list[3] = next_farmer_bank
            
            next_state = tuple(next_state_list)

            if is_valid_state(next_state) and next_state not in visited:
                visited.add(next_state)
                queue.append((next_state, path + [move_item]))
    
    return None # No solution found

def is_valid_state(state):
    # Check both banks for invalid conditions
    farmer_bank = state[0]
    wolf_bank = state[1]
    goat_bank = state[2]
    cabbage_bank = state[3]

    for bank in ['L', 'R']:
        farmer_present_at_bank = (farmer_bank == bank)
        
        wolf_at_bank = (wolf_bank == bank)
        goat_at_bank = (goat_bank == bank)
        cabbage_at_bank = (cabbage_bank == bank)

        if not farmer_present_at_bank:
            # Check for W-G problem
            if wolf_at_bank and goat_at_bank:
                return False
            # Check for G-C problem
            if goat_at_bank and cabbage_at_bank:
                return False
    return True

if __name__ == "__main__":
    solution = solve_wgc()
    if solution:
        with open("solution.txt", "w") as f:
            for move in solution:
                f.write(move + "\n")
        print("Solution found and written to solution.txt")
    else:
        print("No solution found.")
