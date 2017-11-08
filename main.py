#!/usr/bin/python

import os  # sciezka do pliku
import sys # wyjatki
import time  # funkcja zasypiajaca
import datetime  # czas zrobienia filmu
import threading   # wielowatkowosc

import picamera  # obsluga kamery
import paramiko  # wysylanie na server
import user_conf_file  # plik z informacjami od uzytkownika
import posixMutexFile
import subprocess # konvertowanie pliku video
import datetime as dt

MUTEX = ""
START = True


def start_recording(camera, video_data):
    global MUTEX
    file_name = video_data.strftime(user_conf_file.data_format) + '.' + user_conf_file.video_format

    folder = "VIDEO"
    path_to_video = os.path.join(user_conf_file.video_path_on_camera, folder)
    folder = video_data.strftime("%y-%m-%d")
    path_to_video = os.path.join(path_to_video, folder)
    folder = user_conf_file.cam_name
    path_to_video = os.path.join(path_to_video, folder)
    path_to_video = os.path.join(path_to_video, file_name)
    print(path_to_video)
    MUTEX = path_to_video

    if os.path.isdir(os.path.dirname(path_to_video)) == False: os.makedirs(os.path.dirname(path_to_video))

    camera.resolution = (user_conf_file.video_resolution_x, user_conf_file.video_resolution_y)
    camera.framerate = user_conf_file.video_framerate
    camera.start_recording(path_to_video)


def stop_recording(camera):
    global MUTEX
    camera.stop_recording()
    MUTEX = ""


# zmiana formatu z h264 na mp4
def convert_recording(path_to_video):
    head, tail = os.path.split(path_to_video)
    video_name = os.path.splitext(tail)[0]+ ".mp4"
    new_path_to_video = os.path.join(head, video_name)
    command = "MP4Box -add {} {}".format(path_to_video, new_path_to_video)
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        os.remove(path_to_video)
        return new_path_to_video
    except subprocess.CalledProcessError as e:
        print('FAIL:\ncmd:{}\noutput:{}'.format(e.cmd, e.output))


# nagrywanie filmu i zapisywanie w ./VIDEO/
class recording_video(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        global START
        self.camera = picamera.PiCamera()
        self.video_data = datetime.datetime.now()

    def run(self):
        self.video_data = datetime.datetime.now()
        start_recording(self.camera, self.video_data)
        while START:
            try:
                if self.video_data + datetime.timedelta(seconds=user_conf_file.video_time) < datetime.datetime.now():
                    stop_recording(self.camera)
                    self.video_data = datetime.datetime.now()
                    start_recording(self.camera, self.video_data)
            except Exception as ex:
                print(ex)
            time.sleep(2)
        stop_recording(self.camera)



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

            path_on_server = user_conf_file.video_path_on_server + '/' + os.path.relpath(file_path, os.path.abspath('.'))
            mkdir_server(sftp, os.path.dirname(path_on_server))
            sftp.put(file_path, path_on_server)

            sftp.close()
            transport.close()
        except Exception as e:
            raise e
    else:
        raise "U try send not file"


# przeszukuje i wysyla pliki z podanej biblioteki
def send_dir(dir_path):

    try:
        global MUTEX
        global START
        if os.path.isdir(dir_path):
            dir_list = os.listdir(dir_path)
            for new in dir_list:
                if START == False : break
                new_dir_path = dir_path + '/' + new
                send_dir(new_dir_path)
        if os.path.isfile(dir_path):
            if MUTEX != dir_path:
                print(dir_path)
                new_dir_path = convert_recording(dir_path)
                print(new_dir_path)

                send_file(new_dir_path)
                os.unlink(new_dir_path) # usuwanie wyslanego pliku
            else:
                print("MUTEX ------ ", dir_path)
    except Exception as e:
        raise e


# watek wysylajacy na serwer
class send_video_to_server(threading.Thread):

    def __init__(self,path):
        threading.Thread.__init__(self)
        global START
        self.dir_path = path

    def run(self):
        while START:
            try:
                send_dir(self.dir_path)
            except Exception as ex:
                print(ex)
            print("all send")
            time.sleep(user_conf_file.video_time*0.5)

try:
    thread_record = recording_video()
    thread_send = send_video_to_server(os.path.join(user_conf_file.video_path_on_camera, 'VIDEO'))

    thread_record.start()
    thread_send.start()
    while 1:
        x = int(input())
        if x == 0:
            START = False
            exit(0)

except Exception as ex:
    print(ex)
