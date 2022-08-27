#! /bin/sh
# /etc/init.d/skrypt.sh
 
### BEGIN INIT INFO
# Provides:          Skrypt
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Skrypt
# Description:       Skrypt
### END INIT INFO

case "$1" in
  start)
    echo "Starting skrypt.sh"
    # run application you want to start
    python /usr/local/sbin/main.py &
    ;;
  stop)
    echo "Stopping skrypt_sensor.sh"
    # kill application you want to stop
    killall python
    ;;
  *)
    echo "Usage: /etc/init.d/skrypt.sh{start|stop}"
    exit 1
    ;;
esac

exit 0
