#!/usr/bin/env python3

import getpass
import sys
import crypt
import argparse
import subprocess
from ldap_connection import init_ldap, LDAP_USER_SCOPE, LDAP_GROUP_SCOPE, LDAP_FORWARD_SCOPE
from ldap3 import SEARCH_SCOPE_WHOLE_SUBTREE, MODIFY_ADD

DEFAULT_SHELL = '/bin/bash'
IGNORE_UIDNUMBERS_ABOVE = 4999
MAIL_DOMAINS = ['d120.de', 'fachschaft.informatik.tu-darmstadt.de']

def findAliases(userAliases):
  aliasSearch = '(|'
  for alias in userAliases:
    aliasSearch+= '(mailTarget=' + alias + ')'
  aliasSearch+=')'
  c.search(search_base=LDAP_FORWARD_SCOPE, search_filter=aliasSearch, search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['mailAlias'])
  aliases = []
  for alias_obj in c.response:
    alias_alias = alias_obj['attributes']['mailAlias']
    if len(alias_alias) != 0:
      aliases.append(alias_alias[0])
  return aliases

def findLists(addresses):
    list_memberships = []
    for mail in addresses:
        cmd_output = subprocess.check_output(["sudo", "find_member", mail]).decode('ascii')
        if not cmd_output:
            continue
        lines = cmd_output.split('\n')
        for line in lines:
            if not line:
                continue
            if line[0] == ' ':
                list_memberships.append(line.strip())
    print(list_memberships)

def main(args):
    global c
    c = init_ldap()
    uid = arg_data.uid[0]
    # Get User DN
    c.search(search_base=LDAP_USER_SCOPE, search_filter='(uid='+uid+')', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['mailAlias', 'uidNumber', 'displayName', 'homeDirectory', 'objectClass'])
    if len(c.response) == 0:
        print("Error: User {} not found!".format(uid))
        sys.exit()
    print (c.response)
    user_dn = c.response[0]['dn']
    attributes = c.response[0]['attributes']
    # Let admin verify DN
    # Get Groups user is member of
    c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(member='+user_dn+')', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['cn'])
    groups = []
    for grp_obj in c.response:
        group_cn = grp_obj['attributes']['cn']
        if len(group_cn) != 0:
            groups.append (group_cn[0])

    objClasses = attributes['objectClass']
    if 'd120mailUser' in objClasses:
        addresses = []
        for alias in attributes['mailAlias']:
            for domain in MAIL_DOMAINS:
                addresses.append(alias+"@"+domain)

        aliases = findAliases(attributes['mailAlias'])

    print('This script will delete following user:')
    print("username:\t {}".format(uid))
    print("displayName:\t {}".format(attributes['displayName'][0]))
    print("uid:\t\t {}".format(attributes['uidNumber'][0]))
    print("home:\t\t {}".format(attributes['homeDirectory'][0]))
    print("dn:\t\t {}".format(user_dn))
    for group in groups:
        print("group:\t\t",group)
    for mail in addresses:
        print("mailAddress:\t",mail)
    for alias in aliases:
        print("alias:\t\t", alias)
    findLists(addresses)
    #subprocess.call(["sudo", "find", "/mnt/media/", "-user",  uid])
    # Let admin verify
    # Get user mail aliases
    # Get mailing lists user is member of!!!
    # Todo
    # * Matrix
    # * KDV
    # * DjangoCMS
    # * Maildir
    # * Atlas?
    # * Padman benutzer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='d120-deluser')
    parser.add_argument('uid', metavar='username', type=str, nargs=1, help='User to be delted')
    arg_data = parser.parse_args()
    try:
        main(arg_data)
    except KeyboardInterrupt:
        print("\nAborted by user!")
        sys.exit()
