import sys

from our_add.our_add import our_add
from our_sub.our_sub import our_sub
from our_mult.our_mult import our_mult
from our_div.our_div import our_div
from our_mod.our_mod import our_mod


def main():
    if len(sys.argv) != 4:
        print("Number of arguments must be exactly three")  # 'python' keyword can be ignored
    else:

        # Access and display individual arguments
        operation = sys.argv[1]
        first_arg = sys.argv[2]
        second_arg = sys.argv[3]
        print(f"operation: {operation}")
        print(f"first argument: {first_arg}")
        print(f"second argument: {second_arg}")

        # convert inputs to integers and perform the operation
        num1 = int(first_arg)
        num2 = int(second_arg)

        if operation == '+':
            print(f"{num1} + {num2} = {our_add(num1, num2)}")
            
        elif operation == '-':
            print(f"{num1} - {num2} = {our_sub(num1, num2)}")

        elif operation == '*':
            print(f"{num1} * {num2} = {our_mult(num1, num2)}")

        elif operation == '/':
            print(f"{num1} / {num2} = {our_div(num1, num2)}")

        elif operation == '%':
            print(f"{num1} and {num2} with mod operation = {our_mod(num1)}, {our_mod(num2)}")

        else:
            print(f"Invalid operation: {operation}")


if __name__ == "__main__":
    main()
