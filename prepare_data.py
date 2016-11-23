class Transaction:
    def __init__(self, id):
        self.id = id
        self.products = dict()


def transpose_data(input, output):
    inp = open(input, 'r')
    out = open(output, 'w')
    transactions = dict()

    for line in inp:
        row = line.strip().split(',')  # [id, kolejność produktu, nazwa produktu]
        if row[0] in transactions.keys():
            transactions[row[0]].products[row[1]] = row[2]
        else:
            t = Transaction(row[0])
            t.products[row[1]] = row[2]
            transactions[row[0]] = t

    result = []
    for t in transactions.values():
        line = ""
        for lp, product in t.products.items():
            line += product + ','
        line += "\n"
        result.append(line)
        print(line)

    out.writelines(result)


transpose_data(r"C:\Users\Ja\Downloads\Desktop\asocjacje.csv", r"C:\Users\Ja\Downloads\Desktop\out.csv")
