#Write a Python program that asks the user to enter a mark (a number between 0 and 100) and then
#prints the matching letter grade. The program runs in the terminal — there is no website or app
#interface. You will set up a clean Python environment, write your code in a .py file, run it, and
#confirm it produces the correct output. Use pure Python only — no frameworks or external
#packages

marks= int(input("Enter your mark (0-100) "))
#print("Your mark is ",marks)

while (marks >=0 and marks <= 100):
    if (marks <=60):
        print("Mark :",marks," -> Grade: 'E' ")
        break
    elif marks >=60 and marks <=69:
        print("Mark :",marks," -> Grade: 'D' ")
        break
    elif marks >=70 and marks <=79:
        print("Mark :",marks," -> Grade: 'C' ")
        break
    elif marks >=80 and marks <=89:
        print("Mark :",marks," -> Grade: 'B' ")
        break
    elif marks >=90 and marks  <=100:
        print("Mark :",marks," -> Grade: 'A' ")
        break
    else:
        print("Enter mark range between 0 to 100")

 
    
