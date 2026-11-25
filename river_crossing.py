# River crossing puzzle
# 0 = this side of the river, 1 = the other side of the river


# Subprogram to check whether the last move lost the puzzle.
# Something is eaten if two items are left on the same side without the farmer.
# Returns True if the puzzle is lost, or False if it is not.
def wrong_move():
    lost = False
    # Selection: farmer on the other side, fox and chicken left on this side
    if farmer == 1 and fox == 0 and chicken == 0:
        print("The fox ate the chicken.")
        lost = True
    # Selection: farmer on the other side, chicken and grain left on this side
    elif farmer == 1 and chicken == 0 and grain == 0:
        print("The chicken ate the grain.")
        lost = True
    # Selection: farmer on this side, fox and chicken left on the other side
    elif farmer == 0 and fox == 1 and chicken == 1:
        print("The fox ate the chicken.")
        lost = True
    # Selection: farmer on this side, chicken and grain left on the other side
    elif farmer == 0 and chicken == 1 and grain == 1:
        print("The chicken ate the grain.")
        lost = True
    return lost


# Subprogram to check whether the fox, chicken and grain are all on the other side.
# Returns True if the puzzle is solved, or False if not.
def puzzle_solved():
    solved = False
    # Selection: every item is on the other side of the river
    if fox == 1 and chicken == 1 and grain == 1:
        print("You solved the puzzle.")
        solved = True
    return solved


# Subprogram to show which items are on each side of the river
def show_river():
    print("-----------------------")
    print("This side of the river:")
    # Selection: output each item that is on this side (0)
    if farmer == 0:
        print("Farmer")
    if fox == 0:
        print("Fox")
    if chicken == 0:
        print("Chicken")
    if grain == 0:
        print("Grain")
    print()
    print("The other side of the river:")
    # Selection: output each item that is on the other side (1)
    if farmer == 1:
        print("Farmer")
    if fox == 1:
        print("Fox")
    if chicken == 1:
        print("Chicken")
    if grain == 1:
        print("Grain")
    print("-----------------------")


# Main program
# Initialise the variables: everything starts on this side of the river
print("A fox, chicken and a bag of grain wait by the side of a river.")
fox = 0
chicken = 0
grain = 0
farmer = 0
game_over = False

# Iteration: keep taking turns until the puzzle is lost or solved
while not game_over:
    # Ask the user which item to take
    print("Which item will you take in your rowboat to the other side?")
    print("fox, chicken, grain or farmer?")
    choice = input("Choose: ")

    # Selection: row across from this side to the other side
    if choice == "farmer" and farmer == 0:
        farmer = 1
    elif choice == "fox" and farmer == 0 and fox == 0:
        farmer = 1
        fox = 1
    elif choice == "chicken" and farmer == 0 and chicken == 0:
        farmer = 1
        chicken = 1
    elif choice == "grain" and farmer == 0 and grain == 0:
        farmer = 1
        grain = 1
    # Selection: row back from the other side to this side
    elif choice == "farmer" and farmer == 1:
        farmer = 0
    elif choice == "fox" and farmer == 1 and fox == 1:
        farmer = 0
        fox = 0
    elif choice == "chicken" and farmer == 1 and chicken == 1:
        farmer = 0
        chicken = 0
    elif choice == "grain" and farmer == 1 and grain == 1:
        farmer = 0
        grain = 0

    show_river()

    # Selection: end the game if the puzzle is lost or solved
    if wrong_move():
        game_over = True
    elif puzzle_solved():
        game_over = True
