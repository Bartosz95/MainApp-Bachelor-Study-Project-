#!/usr/bin/python

import os  # sciezka do pliku
import sys # wyjatki
import time  # funkcja zasypiajaca
import datetime  # czas zrobienia filmu
import threading   # wielowatkowosc

import picamera  # obsluga kamery
import paramiko  # wysylanie na server
import user_conf_file  # plik z informacjami od uzytkownika
import subprocess # konvertowanie pliku video

import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server

MUTEX = ""
MUTEX_CONVERT = ""
START = True
output = ""
PAGE="""\
<html>
<body>
<p>raz</p>
<img src="stream.mjpg" />
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    global output

    def do_GET(self):
        if self.path == '/agsfihasbfahjfsbisaubasifjbiasfbisfaifaubjsankasnj.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class streaming_video(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.address = ('', 8000)
        self.server = StreamingServer(self.address, StreamingHandler)

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()


'''------------------------------------------------------------------------------------------------------------------'''


def start_recording(camera, video_data):
    global MUTEX
    global output
    file_name = video_data.strftime(user_conf_file.data_format) + '.' + user_conf_file.video_format

    folder = "VIDEO"
    path_to_video = os.path.join(user_conf_file.video_path_on_camera, folder)
    folder = video_data.strftime("%y-%m-%d")
    path_to_video = os.path.join(path_to_video, folder)
    folder = user_conf_file.cam_name
    path_to_video = os.path.join(path_to_video, folder)
    path_to_video = os.path.join(path_to_video, file_name)
    MUTEX = path_to_video

    if os.path.isdir(os.path.dirname(path_to_video)) == False: os.makedirs(os.path.dirname(path_to_video))

    camera.resolution = (user_conf_file.video_resolution_x, user_conf_file.video_resolution_y)
    camera.framerate = user_conf_file.video_framerate
    camera.rotation = user_conf_file.video_rotation
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    camera.start_recording(path_to_video, splitter_port=2)
    print("START ------ ", path_to_video)


def stop_recording(camera):
    global MUTEX
    camera.stop_recording(splitter_port=2)
    camera.stop_recording()
    MUTEX = ""
    print("STOP -------")


# zmiana formatu z h264 na mp4
def convert_recording(path_to_video):
    global MUTEX_CONVERT
    head, tail = os.path.split(path_to_video)
    video_name = os.path.splitext(tail)[0] + ".mp4"
    new_path_to_video = os.path.join(head, video_name)
    MUTEX_CONVERT = new_path_to_video
    command = "MP4Box -add {} {}".format(path_to_video, new_path_to_video)
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        os.remove(path_to_video)
        MUTEX_CONVERT = ""
        return new_path_to_video
    except subprocess.CalledProcessError as e:
        print('FAIL:\ncmd:{}\noutput:{}'.format(e.cmd, e.output))


# nagrywanie filmu i zapisywanie w ./VIDEO/
class recording_video(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.camera = picamera.PiCamera()
        self.video_data = datetime.datetime.now()
        self.output = StreamingOutput()
        self.START = True

    def run(self):
        self.video_data = datetime.datetime.now()
        start_recording(self.camera, self.video_data)
        while self.START:
            try:
                if self.video_data + datetime.timedelta(seconds=user_conf_file.video_time) < datetime.datetime.now():
                    stop_recording(self.camera)
                    self.video_data = datetime.datetime.now()
                    start_recording(self.camera, self.video_data)
            except Exception as ex:
                print(ex)
            time.sleep(3)
        stop_recording(self.camera)

    def stop(self):
        self.START = False



'''------------------------------------------------------------------------------------------------------------------'''


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


# przeszukuje i wysyla pliki z podanej biblioteki
def send_dir(dir_path):

    try:
        global MUTEX
        global START
        global MUTEX_CONVERT
        if os.path.isdir(dir_path):
            dir_list = os.listdir(dir_path)
            for new in dir_list:
                if START == False : break
                new_dir_path = dir_path + '/' + new
                send_dir(new_dir_path)
        if os.path.isfile(dir_path):
            if MUTEX != dir_path:
                new_dir_path = convert_recording(dir_path)
                MUTEX_CONVERT = new_dir_path
                send_file(new_dir_path)
                os.remove(new_dir_path) # usuwanie wyslanego pliku
                print("SEND ------- ", new_dir_path)
                MUTEX_CONVERT = ""
            else:
                print("MUTEX ------ ", dir_path)
    except Exception as e:
        raise e


# watek wysylajacy na serwer
class send_video_to_server(threading.Thread):

    def __init__(self, path):
        threading.Thread.__init__(self)
        self.START = True
        self.dir_path = path

    def run(self):
        while self.START:
            try:
                send_dir(self.dir_path)
            except Exception as ex:
                print(ex)
            time.sleep(3)
    def stop(self):
        self.START = False

'''------------------------------------------------------------------------------------------------------------------'''

#  usuwa foldery wraz z plikami w srodku gdy sa starsze niz argument funkcji podany w godzinach
def rm_dir(dir_path, time):
    try:
        global MUTEX
        global START
        global MUTEX_CONVERT
        time = int(time)
        if os.path.isdir(dir_path):
            dir_list = os.listdir(dir_path)
            for new in dir_list:
                if START == False : break

                else:
                    new_dir_path = os.path.join(dir_path, new)
                    rm_dir(new_dir_path, time)
                    try:
                        os.rmdir(new_dir_path)
                        print("REMOVE ----- ", new_dir_path)
                    except: pass

        if os.path.isfile(dir_path):
            if ((MUTEX != dir_path) and (MUTEX_CONVERT != dir_path)):
                basename = os.path.basename(dir_path)
                filename, file_extension = os.path.splitext(basename)
                data_file = datetime.datetime.strptime(filename, '%y-%m-%d_%H.%M.%S')
                data_now = datetime.datetime.now()
                if ((data_now - data_file).total_seconds()/3600) > time:
                    os.remove(dir_path)
                    print("REMOVE ----- ", dir_path)
    except Exception as ex:
        raise ex


# watek usuwajacy przestarzale
class rm_old_dir(threading.Thread):

    def __init__(self, path, time):
        threading.Thread.__init__(self)
        self.START = True
        self.dir_path = path
        self.time = time

    def run(self):
        while self.START:
            try:
                rm_dir(self.dir_path, self.time)
            except Exception as ex:
                print(ex)
            time.sleep(3)
    def stop(self):
        self.START = False

'''------------------------------------------------------------------------------------------------------------------'''


try:

    thread_record = recording_video()
    thread_stream = streaming_video()
    thread_send = send_video_to_server(os.path.join(user_conf_file.video_path_on_camera, 'VIDEO'))
    thread_rm_old_dir = rm_old_dir(os.path.join(user_conf_file.video_path_on_camera, 'VIDEO'), 15)


    thread_record.start()
    thread_stream.start()
    thread_send.start()
    time.sleep(3)
    thread_rm_old_dir.start()

    while 1:
        x = int(input())
        if x == 0:
            START = False
            thread_send.stop()
            thread_rm_old_dir.stop()
            thread_stream.stop()
            thread_record.stop()
            exit(0)
        time.sleep(5)
        thread_stream.restart()
except Exception as ex:
    print(ex)
