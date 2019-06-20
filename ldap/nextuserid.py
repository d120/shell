#!/usr/bin/env python2

import ldap
import ldap.modlist as modlist
import getpass
import sys
import crypt
import base64
import random
import string

LDAP_URL = "ldap://10.162.32.200";
#LDAP_URL = "ldap://127.0.0.1";
LDAP_USER_SCOPE = 'ou=People,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de';
LDAP_GROUP_SCOPE = 'ou=Group,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de';
DEFAULT_SHELL = '/bin/bash';

curUser = getpass.getuser();
try:
  password = getpass.getpass("Please enter password for user " + curUser + ": ");
except:
  print("");
  print("Aborted!");
  sys.exit();

ldap.set_option(ldap.OPT_PROTOCOL_VERSION, 3);
ld_con   = ldap.initialize(LDAP_URL);
try:
  ld_con.simple_bind_s("uid=" + curUser + "," + LDAP_USER_SCOPE, password);
except ldap.INVALID_CREDENTIALS:
    print("Wrong password");
    sys.exit();
except:
    raise
if not ld_con.whoami_s():
    print("Wrong password");
    sys.exit();

uuid     = 0;
gid      = 999;

ldap_out = ld_con.search_s(LDAP_USER_SCOPE,ldap.SCOPE_ONELEVEL,'(uidNumber=*)',['uidnumber']);

uids = [];
for x in ldap_out:
    tmp_obj = x[1];
    uidNumber = int(tmp_obj["uidNumber"][0])
    if(uidNumber < 10000):
        uids.append(uidNumber);
uids.sort(reverse=True);


uuid = uids[0]+1;
print(uuid)


