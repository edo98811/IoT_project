import time
from schedule import every,run_pending

class Prova:
    def __init__(self):
        print('inizializzata')
    
    def job(self):
        print('working')

if __name__ == "__main__":

    pr = Prova()
    time.sleep(1)
    every().thursday.at('23:14').do(pr.job)
    time.sleep(1)

    while True:
        run_pending()
        time.sleep(1)