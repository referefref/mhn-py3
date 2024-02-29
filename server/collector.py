To update collector.py for compatibility with Python 3, several changes are needed. These include syntax updates, changes to exception handling, and adjustments for library functions that may have changed between Python 2 and 3. Below are the necessary updates:

1. Exception Handling Syntax
Change the syntax of exception catching from Python 2's comma notation to the as keyword used in Python 3.

Before:

python
Copy code
except hpfeeds.FeedException, e:
After:

python
Copy code
except hpfeeds.FeedException as e:
2. Opening Files
Replace the Python 2 method of opening files with the open() function used in Python 3, which should be used with a context manager to ensure proper handling of file resources.

Before:

python
Copy code
cfg.update(json.load(file(sys.argv[1])))
After:

python
Copy code
with open(sys.argv[1], 'r') as f:
    cfg.update(json.load(f))
3. String and Bytes
In Python 3, strings and bytes are strictly differentiated. If hpfeeds expects byte strings, you may need to ensure that strings are encoded to bytes before sending. This script assumes hpfeeds handles strings correctly, but if you encounter issues with string encoding, you might need to explicitly encode strings to UTF-8.

4. basestring and str
Python 3 no longer has basestring; use str instead. Also, Python 3 strings are Unicode by default, so encoding to UTF-8 might only be necessary when interacting with binary data or APIs expecting byte strings.

Before:

python
Copy code
if isinstance(value, basestring):
After:

python
Copy code
if isinstance(value, str):
Additionally, any explicit encoding to UTF-8 should be examined to ensure it's still necessary.

Full Updated Script
python
Copy code
import sys
import datetime
import json
import hpfeeds
import logging

root = logging.getLogger()
root.setLevel(logging.ERROR)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)
logger = logging.getLogger("collector")

def hpfeeds_connect(host, port, ident, secret):
    try:
        connection = hpfeeds.new(host, port, ident, secret)
    except hpfeeds.FeedException as e:
        logger.error('feed exception: %s' % e)
        sys.exit(1)
    logger.info('connected to %s (%s:%s)' % (connection.brokername, host, port))
    return connection

def main():
    cfg = dict(
        HOST='localhost',
        PORT=10000,
        GEOLOC_CHAN='geoloc.events',
        IDENT='',
        SECRET='',
        RHOST='mhnbroker.threatstream.com',
        RPORT=10000,
        RCHANNEL='mhn-community.events',
        RIDENT='mhn-server',
        RSECRET='mhn-secret'
    )

    if len(sys.argv) > 1:
        logger.info("Parsing config file: %s" % sys.argv[1])
        with open(sys.argv[1], 'r') as f:
            cfg.update(json.load(f))

        for name, value in cfg.items():
            if isinstance(value, str):
                cfg[name] = value
    else:
        logger.warning("Warning: no config found, using default values for hpfeeds server")

    subscriber = hpfeeds_connect(cfg['HOST'], cfg['PORT'], cfg['IDENT'], cfg['SECRET'])
    publisher = hpfeeds_connect(cfg['RHOST'], cfg['RPORT'], cfg['RIDENT'], cfg['RSECRET'])

    def on_message(identifier, channel, payload):
        try:
            # validate JSON
            payload = str(payload)
            rec = json.loads(payload)

            # send payload (only if its JSON validation passed)
            publisher.publish(cfg['RCHANNEL'], payload)
        except Exception as e:
            logger.exception(e)

    def on_error(payload):
        logger.error(' -> errormessage from server: {0}'.format(payload))
        subscriber.stop()
        publisher.stop()

    subscriber.subscribe([cfg['GEOLOC_CHAN']])
    try:
        subscriber.run(on_message, on_error)
    except hpfeeds.FeedException as e:
        logger.error('feed exception: %s' % e)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(e)
    finally:
        subscriber.close()
        publisher.close()
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
