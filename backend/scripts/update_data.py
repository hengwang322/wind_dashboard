import os
from compress_pickle import load
import time

import arrow
import pandas as pd
import numpy as np

from models import MODEL_FILE, transform_data
from data import FARM_LIST, update_db, get_weather, get_power
pd.options.mode.chained_assignment = None

MONGO_URI = os.environ['MONGO_URI']


def update_data():
    time_start = time.time()
    models = load(open(MODEL_FILE, 'rb'))
    tz = 'Australia/Sydney'
    dt_format = 'YYYY-MM-DD HH:00:00'  # round to hour
    today = arrow.utcnow().to(tz).format(dt_format)
    yesterday = arrow.utcnow().to(tz).shift(days=-1).format(dt_format)
    dayafter = arrow.utcnow().to(tz).shift(days=+2).format(dt_format)

    for farm in FARM_LIST:
        print(f'Updating {farm}         ', end='\r', flush=True)
        weather_update = get_weather(farm, yesterday, dayafter)
        X, _ = transform_data(weather_update)
        model = models[farm]
        weather_update['prediction'] = np.clip(
            model.predict(X), a_min=0.0, a_max=None)
        update_db(farm, weather_update, upsert=True)

        power_update = get_power(farm, yesterday, today)
        update_db(farm, power_update, upsert=True)

    m, s = divmod(time.time()-time_start, 60)
    h, m = divmod(m, 60)
    runtime = '%03d:%02d:%02d' % (h, m, s)
    print(f'Done! Runtime: {runtime}')


if __name__ == '__main__':
    update_data()
