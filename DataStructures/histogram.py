import re

# Get the handle to the file
try:
    f = open('data.txt','r')
except FileNotFoundError:
    print('Unable to find the file')
    quit()

# Build histogram of words
counts = dict()
for line in f:
    words = line.split()
    for word in words:
        counts[word] = counts.get(word, 0) + 1

# Print top five words with highest frequency
histogram = list()
for word, count in counts.items():
    newTuple = (count, word)
    histogram.append(newTuple)

histogram = sorted(histogram, reverse=True)
for count, word in histogram[:5]:
    print(word, count)

# Close the file
f.close()
