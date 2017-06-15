import sys
import getpass
from ldap3 import Server, Connection, ALL_ATTRIBUTES, SEARCH_SCOPE_WHOLE_SUBTREE

from ldap_config import *

def init_ldap():
    # Connect to LDAP
    curUser = getpass.getuser()
    passwd = getpass.getpass("Please enter password for user " + curUser + ": ")
    return connect_ldap(bindDN="uid=" + curUser + "," + LDAP_USER_SCOPE, passwd=passwd)

def connect_ldap(bindDN, passwd):
    s = Server(LDAP_URL, use_ssl=True, get_info=ALL_ATTRIBUTES)
    c = Connection(s, user=bindDN, password=passwd)
    if not c.bind():
        print('Error in bind: ', c.result['description'])
        sys.exit()
    return c


