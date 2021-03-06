# coding: utf-8
from collections import defaultdict
from itertools import chain, combinations
from optparse import OptionParser


# noinspection PyMethodMayBeStatic
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

    def get_confidence(self, item_set, item):
        return self.get_support(item_set) / self.get_support(item)

    def get_lift(self, item_set, item):
        return self.get_confidence(item_set, item) / self.get_support(item)

    def gen_candidates(self, items_set, length):
        return frozenset([i.union(j) for i in items_set for j in items_set if len(i.union(j)) == length])

    def get_subsets(self, arg):
        return chain(*[combinations(arg, i + 1) for i, a in enumerate(arg)])

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
        """Zwraca relacje w formacie ((elementy), wsparcie)"""
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

        relations = []
        for count, items_set in self.rel_items_set.items():
            if count < self.min_rel_elements:
                continue
            relations.extend([(tuple(items), self.get_support(items)) for items in items_set])
        return relations

    def get_rules(self):
        """Zwraca listę reguł w formacie ((poprzedniki reguły), (następniki reguły), pewność, lift) """
        rules = []  # lista reguł w formacie ((item1),  )
        for count, item_sets in self.rel_items_set.items():
            if count < self.min_rel_elements:
                continue
            for item_set in item_sets:
                subsets = map(frozenset, [i for i in self.get_subsets(item_set)])
                for item in subsets:
                    remain = item_set.difference(item)
                    if len(remain):
                        confidence = self.get_confidence(item_set, item)
                        if confidence >= self.min_confidence:
                            lift = self.get_lift(item_set, item)
                            rules.append((tuple(item), tuple(remain), confidence, lift))
        return rules


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
    opt_parser.add_option("-s", "--support", dest="min_support", default=0.1, help="minimalna wartość wsparcia (support)")
    opt_parser.add_option("-c", "--confidence", dest="min_confidence", default=0.2, help="minimalna wartość pewności (confidence)")
    opt_parser.add_option("-e", "--elements", dest="min_rel_elements", default=2, help="minimalna liczba elementów w relacji")
    opt_parser.add_option("-o", "--output", dest="out", default=False, help="sciezka pliku wyjsciowego, jesli nie podana wyjscie na konsole")
    (options, args) = opt_parser.parse_args()
    if not options.filepath:
        print("Nie podano ścieżki pliku wejściowego")
        return
    transactions = get_transactions_from_csv(options.filepath)
    apriori = Apriori(transactions, options.min_support, options.min_confidence, options.min_rel_elements)
    relations = apriori.get_relations()
    rules = apriori.get_rules()
    formated_rules = format_rules(rules)
    output = options.out
    if output:
        outfile = open(output, 'w')
        outfile.write(formated_rules)
        outfile.close()
    else:
        print(formated_rules)


def format_rules(rules):
    result = "              ==REGUŁY==\n"
    result += "(poprzedniki) ==> (następniki), pewność, lift\n"
    result += "-----------------------------------------------\n"

    for rule in rules:
        result += "("
        for element in rule[0]:
            result += element + ", "
        result = result[:-2]
        result += ") ==> ("
        for element in rule[1]:
            result += element + ", "
        result = result[:-2]
        result += "), {0:.3}, {1:.3}\n".format(rule[2], rule[3])
    return result


def test():
    # filepath = "tesco.csv"
    filepath = r"asoc_l.csv"
    transactions = get_transactions_from_csv(filepath)
    apriori = Apriori(transactions, 0.1, 0.2, 7)
    relations = apriori.get_relations()
    rules = apriori.get_rules()
    # print("    ==RELACJE==")
    # print("(elementy), wsparcie")
    # print("----------------------")
    # for rel in relations:
    #     print(rel)
    # print("\n        ==REGUŁY==")
    # print("(poprzedniki) => (następniki), pewność,lift")
    # print("---------------------------------------")
    # for r in rules:
    #     print(r)
    formated_rules = format_rules(rules)
    print(formated_rules)


# test()
if __name__ == "__main__":
    main()
