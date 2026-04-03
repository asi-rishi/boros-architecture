
import collections

def is_safe(state):
    f, w, g, c = state
    # Unsafe if Wolf and Goat are together without farmer
    # This means farmer is on one bank, and wolf and goat are on the other bank together.
    # The condition (f != w and w == g) checks if the farmer is not with the wolf AND
    # the wolf and goat are on the same bank (meaning they are together).
    if (f != w and w == g):
        return False
    # Unsafe if Goat and Cabbage are together without farmer
    # This means farmer is on one bank, and goat and cabbage are on the other bank together.
    # The condition (f != g and g == c) checks if the farmer is not with the goat AND
    # the goat and cabbage are on the same bank (meaning they are together).
    if (f != g and g == c):
        return False
    return True

def get_next_states(current_state):
    f, w, g, c = current_state
    next_possible_states = []

    # Farmer moves alone
    next_possible_states.append((1-f, w, g, c))

    # Farmer takes Wolf (only if Wolf is on the same bank as Farmer)
    if f == w:
        next_possible_states.append((1-f, 1-w, g, c))

    # Farmer takes Goat (only if Goat is on the same bank as Farmer)
    if f == g:
        next_possible_states.append((1-f, w, 1-g, c))

    # Farmer takes Cabbage (only if Cabbage is on the same bank as Farmer)
    if f == c:
        next_possible_states.append((1-f, w, g, 1-c))

    safe_next_states = []
    for state in next_possible_states:
        if is_safe(state):
            safe_next_states.append(state)
    return safe_next_states

def solve_puzzle():
    initial_state = (0, 0, 0, 0)
    goal_state = (1, 1, 1, 1)

    queue = collections.deque([(initial_state, [initial_state])])
    visited = {initial_state} # Use a set for O(1) average time complexity for lookups

    while queue:
        current_state, path = queue.popleft()

        if current_state == goal_state:
            return path

        for next_state in get_next_states(current_state):
            # Convert tuple to immutable type if necessary for set, though tuples are hashable.
            # Using tuple as state representation directly works for `set` and `dict` keys.
            if next_state not in visited:
                visited.add(next_state)
                new_path = path + [next_state]
                queue.append((next_state, new_path))
    return None # No solution found

# Main execution
if __name__ == "__main__":
    solution_path = solve_puzzle()

    if solution_path:
        with open("solution.txt", "w") as f:
            for state in solution_path:
                f.write(','.join(map(str, state)) + '\n')
        print("Solution found and written to solution.txt")
    else:
        print("No solution found.")
