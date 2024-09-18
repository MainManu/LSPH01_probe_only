import time

log_initialized = False
def to_csv(humidity, temperature, path=f'log_dht22_{time.asctime()}.csv'):
    global log_initialized
    with open(path, 'a') as f:
        if log_initialized == False:
            f.write('time,humidity,temperature\n')
            log_initialized = True
        f.write(f'{time.asctime()},{humidity},{temperature}\n')

