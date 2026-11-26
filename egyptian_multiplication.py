# Ancient Egyptian multiplication


# Subprogram to input the two numbers to be multiplied
# Returns a list containing the two numbers
def input_numbers():
    number1 = int(input("Enter the first number: "))
    number2 = int(input("Enter the second number: "))
    return [number1, number2]


# Subprogram to multiply two numbers using the ancient Egyptian method
# Takes a list containing the two numbers and returns their product
def mul(numbers):
    # Get the two numbers out of the list
    first_number = numbers[0]
    second_number = numbers[1]

    # First column: start with the first number
    column1 = [first_number]
    # Iteration: keep integer dividing by 2 until the number reaches 1
    while first_number > 1:
        first_number = first_number // 2
        column1.append(first_number)

    # Second column: start with the second number
    column2 = [second_number]
    # Iteration: keep multiplying by 2 until both columns are the same length
    while len(column2) < len(column1):
        second_number = second_number * 2
        column2.append(second_number)

    # Iteration: check every row of the first column
    for index in range(len(column1)):
        # Selection: if the first column number is even, cross out that row
        if column1[index] % 2 == 0:
            column2[index] = 0

    # Iteration: add up the numbers left in the second column
    total = 0
    for number in column2:
        total = total + number
    return total


# Main program
numbers = input_numbers()
print(mul(numbers))
