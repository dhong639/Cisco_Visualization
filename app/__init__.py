from .ns_scan_captures import Sections

from flask import Flask

app = Flask(__name__)

from app import routes
#from miscellaneous import get_accessVLAN, get_listTrunkVLAN, get_trunkNativeVLAN, get_voiceVLAN
#from paths import PATH_SAVES
