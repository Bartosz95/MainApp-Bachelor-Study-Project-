power = True

server_hostname = '192.168.0.10'
server_port = 22
server_username = 'root'
server_password = 'mampiernik'

video_path_on_server = "/var/www/FlaskApp/FlaskApp/static"  # zdefiniowana sciezka na serwerze
video_path_on_camera = "/home/pi/Documents/inzynierka/rasp0_cam"  # zdefiniowana sciezka na kamerze
video_format = 'h264'  # rozszerzenie pliku  'h264' lub 'mjpeg'
video_rotation = 0  # rotacja obrazu 0, 90, 180, lub 270.
video_time = 10  # czas nagrywania w sekundach
video_resolution_x = 640
video_resolution_y = 480
video_framerate = 30
video_start_stop = True

cam_name = 'CAM1'  # nazwa kamery
data_format = "%y-%m-%d_%H.%M.%S" # format daty (nazwy
