from app import app
from paths import PATH_DOWNLOAD_DUMP, PATH_CURRENT_PREVIEW

import os


if __name__ == '__main__':
	# make directories if they don't already exist
	if not os.path.exists(PATH_DOWNLOAD_DUMP.format('')):
		os.mkdir(PATH_DOWNLOAD_DUMP.format(''))
	if not os.path.exists(os.path.join(os.getcwd(), 'save_files')):
		os.mkdir(os.path.join(os.getcwd(), 'save_files'))
	if not os.path.exists(PATH_CURRENT_PREVIEW):
		os.mkdir(PATH_CURRENT_PREVIEW)
	
	app.run(host='0.0.0.0', port=5000, debug=True)
