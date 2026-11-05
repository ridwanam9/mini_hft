output = []
count = 0
for i in range(2, 101):
    for j in range(2, 101):
        c = i**j
        if c in output:
            continue
        else:
            output.append(c)
            count += 1

print(count)

