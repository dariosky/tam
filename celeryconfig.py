# ******************* CELERY & RABBITMQ
# RabbitMQ info
rmquser = "tam"
rmqpass = "tamRMQ"
rmqhost = "localhost"
rmqvhost = "tamvhost"

""" To configure RMQ:
$ rabbitmqctl add_user tam tamRMQ
$ rabbitmqctl add_vhost tamvhost
$ rabbitmqctl set_permissions -p tamvhost tam ".*" ".*" ".*"
"""
BROKER_URL = "amqp://%(user)s:%(password)s@%(host)s:5672/%(vhost)s" % {"user":rmquser,
															  "password":rmqpass,
															  "host":rmqhost,
															  "vhost":rmqvhost}
#BROKER_URL = "django://"

CELERY_RESULT_BACKEND = "cache"
#CELERY_RESULT_DBURI = "sqlite:///mydatabase.db"
CELERY_CACHE_BACKEND = 'memcached://localhost:11211/'
