#!/usr/bin/env python3
# Copyright (c) 2016 Max Weller <mweller@d120.de>

from ldap_connection import connect_ldap, LDAP_BASE_DN, SYS_BIND_DN, SYS_BIND_PASSWORD
from ldap_config import MAILMAN_FORWARD_IGNORE_LISTS

from whitelist_config import HRZ_TARGET, SECRET_D120, SECRET_FACHSCHAFT, SECRET_LISTS

from ldap3 import SUBTREE, MODIFY_ADD
from subprocess import check_call, check_output
import requests

def get_whitelist_contents():
    c = connect_ldap(SYS_BIND_DN, SYS_BIND_PASSWORD)

    c.search(search_base=LDAP_BASE_DN, search_filter='(mailAlias=*)', search_scope=SUBTREE, attributes=['mailAlias'])

    whitelist_file = []

    for r in c.response:
        attrs = r['attributes']
        for alias in attrs['mailAlias']:
            whitelist_file.append(alias)

    if len(whitelist_file) < 1:
        print("WARNING: ldap whitelist is empty, no external mails to ldap users will be received!", file=sys.stderr)

    return whitelist_file


MAILMAN_SUFFIXES = ["", "-bounces", "-admin", "-request", "-confirm", "-join", "-leave", "-owner", "-subscribe", "-unsubscribe"]

def get_all_mailman_lists():
    result = check_output(['/usr/sbin/list_lists', '-b'])
    return str(result,"ascii").split('\n')

def get_mailman_whitelist_contents(suffixes):
    return [name+suffix
                     for name in get_all_mailman_lists()
                     for suffix in suffixes if name != ""]

def get_mailman_forward_contents(source_suffixes, target_suffix):
    return [name+src+' '+name+target_suffix
                     for name in get_all_mailman_lists()
                     for src in source_suffixes if name != "" and not name in MAILMAN_FORWARD_IGNORE_LISTS]

def upload_whitelist(api_url, emaildomain, password, emailliste):
    print('Updating whitelist with %d entries for %s ...' % (len(emailliste), emaildomain), end='')
    rq  = requests.post(api_url, files={
        'emailliste': ('whitelist.txt', "\n".join(emailliste))
    }, data={
        'emaildomain': emaildomain,
        'password': password,
    })
    if rq.text.strip() != "OK":
        print("WARNING: failed to update whitelist for "+emaildomain+", error response from hrz:", file=sys.stderr)
        print(rq.text, file=sys.stderr)
    else:
        print("OK")


# --- update whitelists with the HRZ ---------------------------------
whitelist = []
whitelist += get_whitelist_contents()
whitelist += get_mailman_whitelist_contents([""])

print("Whitelist contains %d entries" % (len(whitelist),))

upload_whitelist(HRZ_TARGET, "d120.de", SECRET_D120, whitelist)
upload_whitelist(HRZ_TARGET, "fachschaft.informatik.tu-darmstadt.de", SECRET_FACHSCHAFT, whitelist)


whitelist_mailman = get_mailman_whitelist_contents(MAILMAN_SUFFIXES)
upload_whitelist(HRZ_TARGET, "lists.d120.de", SECRET_LISTS, whitelist_mailman)


# --- generation of postfix forwarding file for mailman lists ------------------------

map_file ='/etc/postfix/virtual_maps'
print('Updating '+map_file, end=' ')

whitelist = get_mailman_forward_contents(
        source_suffixes=["@d120.de", "@fachschaft.informatik.tu-darmstadt.de"],
        target_suffix="@lists.d120.de",
        )

with open(map_file, 'w') as f:
    f.write("\n".join(whitelist))

check_call(['/usr/sbin/postmap', map_file])
print('OK')


