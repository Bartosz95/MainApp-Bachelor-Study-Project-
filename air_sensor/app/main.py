import os  # sciezka do pliku
import sys # wyjatki
import time  # funkcja zasypiajaca
import datetime  # czas zrobienia filmu
import MySQLdb  # bazadanych
import threading   # wielowatkowosc
from sense_hat import SenseHat  # czujniki
import user_conf_file  # plik konfiguracyjny uzytkownika


def update_sense(host, user, password, database, table, data):
    try:
        sense = SenseHat()
        sense.set_imu_config(False, False, False)  # desactive compass gyro accel
        temp = sense.get_temperature()
        pressure = sense.get_pressure()
        humidity = sense.get_humidity()

        db = MySQLdb.connect(host=host, user=user, passwd=password, db=database)
        cur = db.cursor()
        cur.execute("""INSERT INTO {} (data, temp, press, hum) VALUES (%s, %s, %s, %s)""".format(table), (data, float(temp), float(pressure), float(humidity)))
        db.commit()
    except Exception as ex:
        raise ex


# watek uaktualniajacy pomiary z czujnikow w bazie danych (czas w min)
class thread_update_sense(threading.Thread):
    def __init__(self, host, user, password, database, table, time):
        threading.Thread.__init__(self)
        self.START = True
        self.time = time
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.table = table
        self.time_last = datetime.datetime.now()
        self.time_now = datetime.datetime.now()

    def run(self):
        update_sense(host=self.host, user=self.user, password=self.password, database=self.database, table=self.table, data=self.time_now)
        while self.START:
            try:
                self.time_now = datetime.datetime.now()
                if ((self.time_now - self.time_last).total_seconds()/60) > self.time:
                    try:
                        update_sense(host=self.host, user=self.user, password=self.password, database=self.database, table=self.table, data=self.time_now)
                        self.time_last = datetime.datetime.now()
                    except Exception as ex:
                        raise ex
            except Exception as ex:
                print(ex)
            time.sleep(3)

    def stop(self):
        self.START = False


us = thread_update_sense(host=user_conf_file.host, user=user_conf_file.user, password=user_conf_file.password, database=user_conf_file.database, table=user_conf_file.table, time=user_conf_file.time)
us.start()
