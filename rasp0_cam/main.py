import os  # sciezka do pliku
import sys # wyjatki
import time  # funkcja zasypiajaca
import datetime  # czas zrobienia filmu
import threading   # wielowatkowosc

import picamera  # obsluga kamery
import paramiko  # wysylanie na server
import user_conf_file  # plik z informacjami od uzytkownika


# nagrywanie filmu i zapisywanie w ./VIDEO/
def recording_video():
    while user_conf_file.video_start_stop:
        video_data = datetime.datetime.now()
        path_to_video = os.path.abspath('.') + '/VIDEO/' + video_data.strftime("%y.%m.%d") + '/' + user_conf_file.cam_name + \
                         '/' + video_data.strftime(user_conf_file.data_format) + '.' + user_conf_file.video_format

        if os.path.isdir(os.path.dirname(path_to_video)) == False: os.makedirs(os.path.dirname(path_to_video))

        camera = picamera.PiCamera()
        camera.resolution = (user_conf_file.video_resolution_x, user_conf_file.video_resolution_y)
        camera.start_recording(path_to_video)
        camera.wait_recording(user_conf_file.video_time)
        camera.stop_recording()
        print("recording succesfully!")


# tworzenie sciezki na serwerze (funkcja rekurencyjna)
def mkdir_server(sftp,directory):
    try:
        sftp.chdir(directory)
    except IOError:
        try:
          sftp.mkdir(directory)
        except IOError:
            head, tail = os.path.split(directory)
            mkdir_server(sftp,head)
            sftp.mkdir(directory)


#wysylanie na serwer
def send_to_server(file_path):

    transport = paramiko.Transport((user_conf_file.server_hostname, user_conf_file.server_port))
    transport.connect(username=user_conf_file.server_username, password=user_conf_file.server_password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    path_on_server = user_conf_file.video_path + '/' + os.path.relpath(file_path, os.path.abspath('.'))
    mkdir_server(sftp, os.path.dirname(path_on_server))
    sftp.put(file_path, path_on_server)

    sftp.close()
    transport.close()
    print("send succesfully!")


def list_dir(dir_path):
    if os.path.isdir(dir_path):
        dir_list = os.listdir(dir_path)
        for x in dir_list:
            new_dir_path = dir_path + '/' + x
            list_dir(new_dir_path)

    if os.path.isfile(dir_path):
        send_to_server(dir_path)



class foo(threading.Thread):

    def __init__(self,get_time,path):
        threading.Thread.__init__(self)
        self.my_time = get_time
        self.path_to_file=path

    def run(self):
        self.path_list = os.path.split(self.path_to_file)
        print (self.path_list)
        while self.my_time >= 0:
            print self.my_time
            time.sleep(1)
            self.my_time -= 1




#try:

list_dir(os.path.abspath('.')+ '/VIDEO')
#send_to_server(path_to_video)
"""
ONE= foo(2,by)
ONE.start()
except Exception as ex:
    print(ex)"""