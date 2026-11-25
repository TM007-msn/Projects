# River crossing puzzle (novice version)
# 0 means this side of the river
# 1 means the other side of the river


# Subprogram to check if something has been eaten
# Returns True if the puzzle is lost, False if not
def wrong_move():
    # Selection: the farmer has left the fox and chicken on this side
    if farmer == 1 and fox == 0 and chicken == 0:
        print("The fox ate the chicken.")
        return True
    # Selection: the farmer has left the chicken and grain on this side
    if farmer == 1 and chicken == 0 and grain == 0:
        print("The chicken ate the grain.")
        return True
    # Selection: the farmer has left the fox and chicken on the other side
    if farmer == 0 and fox == 1 and chicken == 1:
        print("The fox ate the chicken.")
        return True
    # Selection: the farmer has left the chicken and grain on the other side
    if farmer == 0 and chicken == 1 and grain == 1:
        print("The chicken ate the grain.")
        return True
    return False


# Subprogram to check if everything is on the other side
# Returns True if the puzzle is solved, False if not
def puzzle_solved():
    # Selection: the fox, chicken and grain are all on the other side
    if fox == 1 and chicken == 1 and grain == 1:
        print("You solved the puzzle.")
        return True
    return False


# Main program
print("A fox, chicken and a bag of grain wait by the side of a river.")
fox = 0
chicken = 0
grain = 0
farmer = 0
playing = True

# Iteration: keep playing until the puzzle is lost or solved
while playing == True:
    print("Which item will you take in your rowboat to the other side?")
    print("fox, chicken, grain or farmer?")
    choice = input("Choose: ")

    # Selection: move the farmer and the chosen item across the river
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
    # Selection: move the farmer and the chosen item back again
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

    # Output what is on this side of the river
    print("-----------------------")
    print("This side of the river:")
    if farmer == 0:
        print("Farmer")
    if fox == 0:
        print("Fox")
    if chicken == 0:
        print("Chicken")
    if grain == 0:
        print("Grain")
    print()

    # Output what is on the other side of the river
    print("The other side of the river:")
    if farmer == 1:
        print("Farmer")
    if fox == 1:
        print("Fox")
    if chicken == 1:
        print("Chicken")
    if grain == 1:
        print("Grain")
    print("-----------------------")

    # Selection: stop the game if the puzzle is lost or solved
    if wrong_move() == True:
        playing = False
    elif puzzle_solved() == True:
        playing = False
