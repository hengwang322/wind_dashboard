import os
from compress_pickle import load
import time

import numpy as np
import pandas as pd

from models import MODEL_FILE, transform_data
from data import FARM_LIST, update_db, connect_db, fetch_data
pd.options.mode.chained_assignment = None

MONGO_URI = os.environ['MONGO_URI']


def update_pred():
    time_start = time.time()
    client = connect_db(MONGO_URI)
    models = load(open(MODEL_FILE, 'rb'))

    for farm in FARM_LIST:
        print(f'Updating {farm}         ', end='\r', flush=True)
        df = fetch_data(client, farm, limit=None)
        X, _ = transform_data(df)
        model = models[farm]

        update_df = df[['time', 'prediction']].copy()
        update_df['prediction'] = np.clip(
            model.predict(X), a_min=0.0, a_max=None)
        update_db(farm, update_df, upsert=True)

    m, s = divmod(time.time()-time_start, 60)
    h, m = divmod(m, 60)
    runtime = '%03d:%02d:%02d' % (h, m, s)
    print(f'Done! Runtime: {runtime}')


if __name__ == '__main__':
    update_pred()
