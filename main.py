import picamera  # obsluga kamery
import user_conf_file  # plik z informacjami od uzytkownika
import os  # sciezka do pliku
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
    return path_to_video


def server_connect(localpath, remotepath):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=user_conf_file.server_hostname,
                port=user_conf_file.server_port,
                username=user_conf_file.server_username,
                password=user_conf_file.server_password)
    sftp = ssh.open_sftp()
    print(localpath)
    sftp.put(localpath, remotepath)
    sftp.close()
    ssh.close()
    print("connect succesfully!")


try:
    path_to_video = recording_video()
    server_connect(path_to_video, user_conf_file.video_path)
except Exception as ex:
    print(ex)
