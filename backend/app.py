import os
import time

from scripts.retrain_models import retrain_models
from scripts.update_data import update_data
from scripts.update_pred import update_pred

MONGO_URI = os.environ['MONGO_URI']


def handler(event, context):
    action = event.get('action')
    time_start = time.time()
    if action == 'updatePred':
        update_pred()
    elif action == 'retrain':
        retrain_models()
    else:
        update_data()
    m, s = divmod(time.time()-time_start, 60)
    h, m = divmod(m, 60)
    runtime = '%03d:%02d:%02d' % (h, m, s)

    return {
        'statusCode': 200,
        'runtime': runtime
    }