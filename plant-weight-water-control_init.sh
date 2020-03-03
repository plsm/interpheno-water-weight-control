#!/bin/sh
# Start the plant weight water control daemon

DAEMON=/home/pi/pwwc
PIDFILE=/var/run/pwwcd.pid

. /lib/lsb/init-functions

case "$1" in
	start)
		log_daemon_msg "Starting the plant weight water control system" "pwwc"
		start_daemon -p $PIDFILE $DAEMON
      log_end_msg $?
		;;
	stop)
		log_daemon_msg "Stoping the plant weight water control system" "pwwc"
		killproc -p $PIDFILE $DAEMON
      RETVAL=$?
      [ $RETVAL -eq 0 ] && [ -e "$PIDFILE" ] && rm -f $PIDFILE
      log_end_msg $RETVAL
		;;
	*)
      log_action_msg "Usage: /etc/init.d/cron {start|stop|status|restart|reload|force-reload}"
      exit 2
      ;;
esac
