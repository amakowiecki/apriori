import tempfile
from collections import OrderedDict

from celery import Celery
from flask import Flask, render_template, request, url_for, redirect

# Celery Broker and Result backend config
flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379',
    CELERY_ACCEPT_CONTENT=['pickle']
)


# Configure celery to work with flask
def make_celery(app):
    task_manager = Celery(
        app.import_name,
        backend=app.config['CELERY_BROKER_URL'],
        broker=app.config['CELERY_BROKER_URL']
    )
    task_manager.conf.update(app.config)

    TaskBase = task_manager.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    task_manager.Task = ContextTask
    return task_manager


# Initialize celery app
celery_app = make_celery(flask_app)

#############################################################
from collections import defaultdict
from itertools import chain, combinations


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
        return self.get_confidence(item_set, item)/self.get_support(item)

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


def get_transactions_from_csv(filename):
    file = open(filename)
    return get_transactions_from_file(file)


def get_transactions_from_file(file):
    transactions = []
    for line in file:
        transaction = frozenset(line.strip().rstrip(',').split(','))
        transactions.append(transaction)
    return transactions


#############################################################

tasks = OrderedDict()


@celery_app.task()
def apriori(transactions, min_support=0.1, min_confidence=0.0, min_rel_elements=0):
    result = Apriori(transactions, min_support, min_confidence, min_rel_elements)
    return [result.get_relations(), result.get_rules()]


@flask_app.route('/')
def home():
    return render_template('index.html')


@flask_app.route('/run', methods=['GET', 'POST'])
def run():
    if request.method == 'GET':
        return render_template('run.html')

    if request.method == 'POST':
        name = request.form.get('name')
        min_support = request.form.get('min_support')
        min_confidence = request.form.get('min_confidence')
        min_rel_elements = request.form.get('min_rel_elements')
        file = request.files['file']

        if min_support is '' or min_confidence is '' or min_rel_elements is '':
            raise AttributeError()

        with tempfile.NamedTemporaryFile() as f:
            f.write(file.read())
            f.flush()
            task = apriori.delay(
                get_transactions_from_csv(f.name),
                float(min_support),
                float(min_confidence),
                float(min_rel_elements))
            task.name = name
            tasks[task.task_id] = task

        return redirect(url_for('tasks_list'))


@flask_app.route('/tasks')
def tasks_list():
    return render_template('tasks.html', data=[(k, v) for (k, v) in tasks.items()])


@flask_app.route('/task/<task_id>')
def task_by_id(task_id):
    return render_template('task.html', data=tasks[task_id])
