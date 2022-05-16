from app import app
from paths import PATH_DOWNLOAD_DUMP

import os


if __name__ == '__main__':
	# make directories if they don't already exist
	if not os.path.exists(PATH_DOWNLOAD_DUMP.format('')):
		os.mkdir(PATH_DOWNLOAD_DUMP.format(''))
	if not os.path.exists(os.path.join(os.getcwd(), 'save_files')):
		os.mkdir(os.path.join(os.getcwd(), 'save_files'))
	
	app.run(host='0.0.0.0', port=5000, debug=True)
