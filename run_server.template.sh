#!/bin/bash
FRONT_CMD="%(VENV_FOLDER)s/bin/daphne"
FRONT_PID_PATH="%(FRONT_PID_FILE)s"

cd "%(REPOSITORY_FOLDER)s"
sh "%(VENV_FOLDER)s/bin/activate"

start_server () {
  if [ -f ${PID_PATH} ]; then
    if [ "$(ps -p `cat ${PID_PATH}` | wc -l)" -gt 1 ]; then
       echo "A server is already running"
       return
    else
        echo "We have the PID but not the process deleting PID and restarting"
        rm ${PID_PATH}
    fi
  fi
  #cd $PROJECTLOC
  echo "starting Gunicorn"
  exec ${GUNICORN_CMD} ${GUNICORN_ARGS}
}

stop_server () {
  if [ -f ${PID_PATH} ] && [ "$(ps -p `cat ${PID_PATH}` | wc -l)" -gt 1 ]; then
    echo "Stopping Frontend server"
    kill `cat ${PID_PATH}`
    rm ${PID_PATH}
  else
    if [ -f ${PID_PATH} ]; then
      echo "server not running"
      rm ${PID_PATH}
    else
      echo "No pid file found for server"
    fi
  fi
}

case "$1" in
'start')
  start_server
  ;;
'stop')
  stop_server
  ;;
'restart')
  stop_server
  sleep 2
  start_server
  ;;
*)
  echo "Usage: $0 {{ start | stop | restart }}"
  ;;
esac

exit 0
