import os  # sciezka do pliku
import sys # wyjatki
import time  # funkcja zasypiajaca
import datetime  # czas zrobienia filmu
import threading   # wielowatkowosc

import picamera  # obsluga kamery
import paramiko  # wysylanie na server
import user_conf_file  # plik z informacjami od uzytkownika
import posixMutexFile

# nagrywanie filmu i zapisywanie w ./VIDEO/
class recording_video(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        try:
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
        except:
             raise "Blad nagrywania"


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


# wysylanie pojedynczego pliku na serwer
def send_file(file_path):

    if os.path.isfile(file_path):
        try:
            transport = paramiko.Transport((user_conf_file.server_hostname, user_conf_file.server_port))
            transport.connect(username=user_conf_file.server_username, password=user_conf_file.server_password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            path_on_server = user_conf_file.video_path + '/' + os.path.relpath(file_path, os.path.abspath('.'))
            mkdir_server(sftp, os.path.dirname(path_on_server))
            sftp.put(file_path, path_on_server)

            sftp.close()
            transport.close()
            return file_path
            print("send succesfully!")
        except:
            raise "Blad w wysylaniu pliku. Sprawdz polaczenie z serwerem lub sciezke uzytkownika"
    else:
        raise "Proba wyslania nie pliku"


def send_dir(dir_path):
    try:
        if os.path.isdir(dir_path):
            dir_list = os.listdir(dir_path)
            for new in dir_list:
                new_dir_path = dir_path + '/' + new
                send_dir(new_dir_path)
            os.rmdir(dir_path)
        if os.path.isfile(dir_path):
            os.unlink(send_file(dir_path))
    except Exception as ex:
        raise ex


class send_video_to_server(threading.Thread):
    def __init__(self,path):
        threading.Thread.__init__(self)
        self.dir_path = path
    def run(self):
        send_dir(self.dir_path)


#try:
thread_record = recording_video()
#thread_send = send_video_to_server(os.path.abspath('.') + '/VIDEO')

thread_record.start()
#thread_send.start()
#send_to_server(path_to_video)
"""
ONE= foo(2,by)
ONE.start()
except Exception as ex:
    print(ex)"""