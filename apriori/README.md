celery -A apriori_web.celery_app worker
export FLASK_APP=apriori.py
flask run
celery flower -A apriori_web.celery_app --address=127.0.0.1 --port=5555