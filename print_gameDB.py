import csv
import re

# String that contains all the games.
my_games = ""

# Index for the game.
i = 0

dates = []
games = []

# Open csv file to reader
with open('gameDB.csv', 'r', encoding='utf-8') as csv_file:
    reader = csv.reader(csv_file)

    # The name of the game is on the first part of the row
    for row in reader:
        row_string = ' '.join([str(elem) for elem in row])
        new_list_from_row = re.split(" |\t", row_string)
        for item in new_list_from_row:
            if len(item) == 10 and "-" in item:
                numbers = item.replace("-", "")
                if numbers.isnumeric():
                    dates.append(numbers)
                    print(numbers)
                    break

        name = row[0].split('\t')

        # Add the index to the game.
        if i > 0:
            my_games += str(i) + ". " + name[0] + "\n"
        games.append(name[0])
        print(name[0])
        i += 1

games.pop(0)

print(f"dates length: {len(dates)}")
print(f"games length: {len(games)}")

zipped_pairs = zip(dates, games)
sorted_games = [x for _, x in sorted(zipped_pairs)]

i = 1
my_games_sorted = ""
for item in sorted_games:
    my_games_sorted += str(i) + ". " + item + "\n"
    i += 1


# Write the string to file.
with open('my_games.txt', 'w', encoding='utf-8') as games_file:
    games_file.write(my_games)

# Close the file.
games_file.close()

with open('my_games_sorted.txt', 'w', encoding='utf-8') as games_file_sorted:
    games_file_sorted.write(my_games_sorted)

games_file_sorted.close()
