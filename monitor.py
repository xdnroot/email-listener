import eventlet
imapclient = eventlet.import_patched('imapclient')

from os import environ as env
import os.path as path
import sys
import traceback
import logging
from logging.handlers import RotatingFileHandler
import email
import requests
import json
from time import sleep

# Setup the log handlers to stdout and file.
log = logging.getLogger('imap_monitor')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s | %(message)s', "%d-%m-%Y %H:%M:%S"
    )
handler_stdout = logging.StreamHandler(sys.stdout)
handler_stdout.setLevel(logging.DEBUG)
handler_stdout.setFormatter(formatter)
log.addHandler(handler_stdout)
handler_file = RotatingFileHandler(
	'imap_monitor.log',
	mode='a',
	maxBytes=1048576,
	backupCount=9,
	encoding='UTF-8',
	delay=True
	)
handler_file.setLevel(logging.DEBUG)
handler_file.setFormatter(formatter)
log.addHandler(handler_file)

# TODO: Support SMTP log handling for CRITICAL errors.


def process_email(mail_, download_, log_):
	"""Email processing to be done here. mail_ is the Mail object passed to this
	function. download_ is the path where attachments may be downloaded to.
	log_ is the logger object.

	"""
	body = []
	if mail_.is_multipart():
		for payload in mail_.get_payload():
			body.append(payload.get_payload())
	else:
		body = mail_.get_payload()

	msg = {
		"from": mail_['From'],
		"date": mail_['Date'],
		"subject": mail_['Subject'],
		"body_plaintext": body[0],
		#"body_html": body[1] #uncomment this line to display html payload.
	}
	log.info(json.dumps(msg, indent=4))

	log.info("sending email to callback server")
	headers = {
		'Content-Type': 'application/json',
	}
	response = requests.request("POST", env['CALLBACK_URL'], headers=headers, data=json.dumps(msg))
	log.info(json.dumps(response.json(), indent=4))

	return 'return meaningful result here'

def main():
	log.info('... script started')
	while True:

		# Retrieve IMAP host - halt script if section 'imap' or value
		# missing
		try:
			host = env['IMAP_HOST']
		except:
			log.critical('variable "IMAP_HOST" not found')
			break

		# Retrieve IMAP username - halt script if missing
		try:
			username = env['IMAP_EMAIL']
		except:
			log.critical('variable "IMAP_EMAIL" not found')
			break

		# Retrieve IMAP password - halt script if missing
		try:
			password = env['IMAP_PASSWORD']
		except:
			log.critical('variable "IMAP_PASSWORD" not found')
			break

		# Retrieve IMAP SSL setting - warn if missing, halt if not boolean
		try:
			ssl = bool(env['IMAP_SSL'])
		except:
			log.critical('variable "IMAP_SSL" not found, use non-TLS communication')
			ssl = False

		# IMAP folder to monitor (option: INBOX, SPAM, SENT)
		folder = "INBOX"

		# Path for downloads
		download = "./download"
		download = download if (
				download and path.exists(download)
				) else path.abspath(__file__)
		log.info('setting path for email downloads - {0}'.format(download))

		while True:
			# <--- Start of IMAP server connection loop

			# Attempt connection to IMAP server
			log.info('connecting to IMAP server - {0}'.format(host))
			try:
				imap = imapclient.IMAPClient(host, use_uid=True, ssl=ssl)
			except Exception:
				# If connection attempt to IMAP server fails, retry
				etype, evalue = sys.exc_info()[:2]
				estr = traceback.format_exception_only(etype, evalue)
				logstr = 'failed to connect to IMAP server - '
				for each in estr:
					logstr += '{0}; '.format(each.strip('\n'))
				log.error(logstr)
				sleep(10)
				continue
			log.info('server connection established')

			# Attempt login to IMAP server
			log.info('logging in to IMAP server - {0}'.format(username))
			try:
				result = imap.login(username, password)
				log.info('login successful - {0}'.format(result))
			except Exception:
				# Halt script when login fails
				etype, evalue = sys.exc_info()[:2]
				estr = traceback.format_exception_only(etype, evalue)
				logstr = 'failed to login to IMAP server - '
				for each in estr:
					logstr += '{0}; '.format(each.strip('\n'))
				log.critical(logstr)
				break

			# Select IMAP folder to monitor
			log.info('selecting IMAP folder - {0}'.format(folder))
			try:
				result = imap.select_folder(folder)
				log.info('folder selected')
			except Exception:
				# Halt script when folder selection fails
				etype, evalue = sys.exc_info()[:2]
				estr = traceback.format_exception_only(etype, evalue)
				logstr = 'failed to select IMAP folder - '
				for each in estr:
					logstr += '{0}; '.format(each.strip('\n'))
				log.critical(logstr)
				break

			# Retrieve and process all unread messages. Should errors occur due
			# to loss of connection, attempt restablishing connection
			try:
				result = imap.search('UNSEEN')
			except Exception:
				continue
			log.warning('{0} unread messages seen - {1}'.format(
				len(result), result
				))
			for each in result:
				try:
					result = imap.fetch(each, ['RFC822'])
				except Exception:
					log.error('failed to fetch email - {0}'.format(each))
					continue
				mail = email.message_from_string(result[each][b'RFC822'])
				try:
					log.info("-----------------------------------------------")
					log.info('processing email {0} - {1}')
					process_email(mail, download, log)
					log.info("-----------------------------------------------")
				except Exception:
					log.error('failed to process email {0}'.format(each))
					raise
					continue

			while True:
				# <--- Start of mail monitoring loop

				# After all unread emails are cleared on initial login, start
				# monitoring the folder for new email arrivals and process
				# accordingly. Use the IDLE check combined with occassional NOOP
				# to refresh. Should errors occur in this loop (due to loss of
				# connection), return control to IMAP server connection loop to
				# attempt restablishing connection instead of halting script.
				imap.idle()
				# TODO: Remove hard-coded IDLE timeout; place in config file
				result = imap.idle_check(5*60)
				if result:
					imap.idle_done()
					result = imap.search('UNSEEN')
					log.warning('{0} new unread messages - {1}'.format(
						len(result),result
						))
					for each in result:
						fetch = imap.fetch(each, ['RFC822'])
						mail = email.message_from_bytes(
							fetch[each][b'RFC822']
							)
						try:
							log.info("-----------------------------------------------")
							log.info('processing email {0} - {1}')
							process_email(mail, download, log)
							log.info("-----------------------------------------------")
						except Exception:
							log.error(
								'failed to process email {0}'.format(each))
							raise
							continue
				else:
					imap.idle_done()
					imap.noop()
					log.warning('no new messages seen')
				# End of mail monitoring loop --->
				continue

			# End of IMAP server connection loop --->
			break

		# End of configuration section --->
		break
	log.info('script stopped ...')

if __name__ == '__main__':
	main()