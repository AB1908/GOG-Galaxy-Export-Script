
# PRINTS NUMBERED LIST OF GAMES FROM CSV FILE TO TEXT FILE

import csv

# String that contains all the games.
my_games = ""

# Index for the game.
i = 0

# Open csv file to reader
with open('../gameDB.csv', 'r', encoding='utf-8') as csv_file:
    reader = csv.reader(csv_file)

    # The name of the game is on the first part of the row
    for row in reader:
        row_string = ' '.join([str(elem) for elem in row])

        name = row[0].split('\t')

        # Add the index to the game.
        if i > 0:
            my_games += str(i) + ". " + name[0] + "\n"
        print(name[0])
        i += 1

# Write the string to file.
with open('my_games.txt', 'w', encoding='utf-8') as games_file:
    games_file.write(my_games)

# Close the file.
games_file.close()
