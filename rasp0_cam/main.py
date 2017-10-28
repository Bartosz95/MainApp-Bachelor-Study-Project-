import picamera  # obsluga kamery
import user_conf_file  # plik z informacjami od uzytkownika
import os  # sciezka do pliku
import sys # wyjatki
import datetime
import paramiko


def recording_video():
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
    return video_data

def server_connect(video_data, remotepath):
    end_of_path = '/VIDEO/' + video_data.strftime("%y.%m.%d") + '/' + user_conf_file.cam_name + \
				  '/' + video_data.strftime(user_conf_file.data_format) + '.' + user_conf_file.video_format
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=user_conf_file.server_hostname,
                port=user_conf_file.server_port, 
                username=user_conf_file.server_username, 
                password=user_conf_file.server_password)
    ssh.close()
    print("connect succesfully!")


def mkdir_server(sftp,directory):
    try:
        sftp.mkdir(directory)
    except IOError:
        head, tail = os.path.split(directory)
        print(head)
        print (tail)
        mkdir_server(sftp,head)
        sftp.mkdir(directory)



try:
    video_data = recording_video()
    end_of_path = '/VIDEO/' + video_data.strftime("%y.%m.%d") + '/' + user_conf_file.cam_name + \
                  '/' + video_data.strftime(user_conf_file.data_format) + '.' + user_conf_file.video_format

    transport = paramiko.Transport((user_conf_file.server_hostname, user_conf_file.server_port))
    transport.connect(username = user_conf_file.server_username, password = user_conf_file.server_password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    dir_path = os.path.dirname(user_conf_file.video_path + end_of_path)

    print(dir_path)
    mkdir_server(sftp,dir_path)

    """
    try:
        sftp.chdir(dir_path)
    except IOError:
        sftp.mkdir(dir_path)
        sftp.chdir(dir_path)

    #sftp.put(os.path.abspath('.') + end_of_path, remotepath + end_of_path)

    transport.close()
    sftp.close()"""

#server_connect(video_data, user_conf_file.video_path)
except Exception as ex:
    print(ex)
