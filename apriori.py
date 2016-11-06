# coding: utf-8
from collections import defaultdict
from optparse import OptionParser


class Apriori:
    def __init__(self, transactions, min_support, min_confidence, min_rel_elements):
        self.min_rel_elements = min_rel_elements
        self.min_confidence = min_confidence
        self.min_support = min_support
        self.transactions = transactions
        self.tran_count = len(transactions)
        self.frequency = defaultdict(int)  # {item: frequency}
        self.rel_items_set = dict()  # zbiór zbiorów elementów powiązanych o poszczególnych licznościach {liczność: elementy}

    def get_support(self, item):
        return self.frequency[item] / self.tran_count

    def gen_candidates(self, items_set, length):
        return frozenset([i.union(j) for i in items_set for j in items_set if len(i.union(j)) == length])

    def get_items_from_transations(self):
        items = set()
        for transaction in self.transactions:
            for item in transaction:
                items.add(item)
        return items

    def get_items_with_min_support(self, items_set):
        tran_count = len(self.transactions)  # liczba wszystkich transakcji
        item_count = defaultdict(int)
        result = set()
        for item in items_set:
            for t in self.transactions:
                if item.issubset(t):
                    self.frequency[item] += 1
                    item_count[item] += 1
        for item, count in item_count.items():
            support = count / tran_count
            if support >= self.min_support:
                result.add(item)
        return result

    def get_relations(self):
        items = self.get_items_from_transations()
        item_set = [frozenset([i]) for i in items]
        candidates = self.get_items_with_min_support(item_set)

        k = 2
        while len(candidates) > 0:
            self.rel_items_set[k - 1] = candidates
            candidates = self.gen_candidates(candidates, k)
            new_candidates = self.get_items_with_min_support(candidates)
            candidates = new_candidates
            k += 1
        return self.rel_items_set

def get_transactions_from_csv(filepath):
    file = open(filepath)
    transactions = list()
    for line in file:
        transaction = frozenset(line.strip().rstrip(',').split(','))
        transactions.append(transaction)
    return transactions


def main():
    opt_parser = OptionParser()
    opt_parser.add_option("-f", "--filepath", dest="filepath", help="ścieżka do pliku wejściowego")
    opt_parser.add_option("-s", "--support", dest="min_support", default=0.0, help="minimalna wartość wsparcia (support)")
    opt_parser.add_option("-c", "--confidence", dest="min_confidence", default=0.0, help="minimalna wartość pewności (confidence)")
    opt_parser.add_option("-e", "--elements", dest="min_rel_elements", default=2, help="minimalna liczba elementów w relacji")
    (options, args) = opt_parser.parse_args()

    transactions = get_transactions_from_csv(options.filepath)
    apriori = Apriori(transactions, options.min_support, options.min_confidence, options.min_rel_elements)


def test():
    filepath = r"C:\Users\Ja\Downloads\Apriori-master\Apriori-master\tesco.csv"
    transactions = get_transactions_from_csv(filepath)
    apriori = Apriori(transactions, 0.0, 0.0, 2)
    apriori.run()
    print(apriori.rel_items_set)


test()
