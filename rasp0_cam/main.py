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

# tworzenie sciezki na serwerze
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



def send_to_server(video_data):

    transport = paramiko.Transport((user_conf_file.server_hostname, user_conf_file.server_port))
    transport.connect(username=user_conf_file.server_username, password=user_conf_file.server_password)
    sftp = paramiko.SFTPClient.from_transport(transport)


    end_of_path = '/VIDEO/' + video_data.strftime("%y.%m.%d") + '/' + user_conf_file.cam_name + \
				  '/' + video_data.strftime(user_conf_file.data_format) + '.' + user_conf_file.video_format

    dir_path = os.path.dirname(user_conf_file.video_path + end_of_path)

    mkdir_server(sftp, dir_path)

    sftp.put(os.path.abspath('.') + end_of_path, user_conf_file.video_path + end_of_path)

    sftp.close()
    transport.close()
    print("send succesfully!")






try:
    video_data = recording_video()
    send_to_server(video_data)

except Exception as ex:
    print(ex)
