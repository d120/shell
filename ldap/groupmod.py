#!/usr/bin/env python3

import getpass
import sys
import argparse
import re
from ldap_connection import init_ldap, LDAP_USER_SCOPE, LDAP_GROUP_SCOPE

import tabulate
from ldap3 import Server, Connection, ALL_ATTRIBUTES, SUBTREE, MODIFY_ADD, MODIFY_DELETE


PROTECTED_GROUPS = ['fachschaft', 'fss']
IGNORE_GIDNUMBERS_ABOVE = 4999


def get_uid_by_dn(fqdn):
    pattern = r"uid=([0-9a-zA-Z_-]+),"
    match = re.search(pattern, fqdn)
    if match:
        return match.group(1)
    else:
        print("Error: uid not found in {}.".format(fqdn))
        pattern = r"cn=([0-9a-zA-Z_-]+),"
        match = re.search(pattern, fqdn)
        if match:
            return match.group(1)
        else:
            sys.exit()

def get_new_gidNumber(c):
    c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(objectClass=posixGroup)', search_scope=SUBTREE, attributes=['gidNumber'])
    gids = []
    gids.append(1000)
    for x in c.response:
        if 'gidNumber' not in x['attributes']:
            continue
        the_attrs = x['attributes']
        the_gid_number = int(the_attrs['gidNumber'][0])
        if the_gid_number > IGNORE_GIDNUMBERS_ABOVE:
            continue
        gids.append(the_gid_number)
    gids.sort(reverse=True)
    gid = gids[0]+1
    return gid

def block_protected_groups(group):
    if group in PROTECTED_GROUPS:
        print("Error: Modification of group {} is not allowed!".format(group))
        sys.exit()


def group_list(args, c):
    c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(cn='+args.group+')', search_scope=SUBTREE, attributes=['member'])
    if len(c.response) == 0:
        print("Error: Group {} not found!".format(args.group))
        sys.exit()
    user_list = c.response[0]['attributes']['member']
    table = []
    for user in user_list:
        table.append([get_uid_by_dn(user), user])
    table.sort(key=lambda x: x[0])
    print()
    print("The following users are in group {}:".format(args.group))
    print(tabulate.tabulate(table))


def group_create(args, c):
    block_protected_groups(args.group)
    c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(cn='+args.group+')', search_scope=SUBTREE, attributes=['member'])
    if len(c.response) != 0:
        print("Error: Group {} already exists!".format(args.group))
        sys.exit()
    if args.posix == True:
        print("Create posix group")
        gidNumber = get_new_gidNumber(c)
        print("New Group GID: {}".format(gidNumber))
        c.add('cn='+args.group+','+LDAP_GROUP_SCOPE, ['groupOfNames', 'posixGroup'], {'member': 'cn=dummy,ou=Services,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de', 'gidNumber': gidNumber})
    else:
        c.add('cn='+args.group+','+LDAP_GROUP_SCOPE, ['groupOfNames'], {'member': 'cn=dummy,ou=Services,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de'})
    print(c.result['description'])


def group_delete(args, c):
    block_protected_groups(args.group)
    c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(cn='+args.group+')', search_scope=SUBTREE, attributes=['member'])
    if len(c.response) == 0:
        print("Error: Group {} not found!".format(args.group))
        sys.exit()
    c.delete('cn='+args.group+','+LDAP_GROUP_SCOPE)
    print(c.result['description'])


def group_adduser(args, c):
    block_protected_groups(args.group)
    c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(cn='+args.group+')', search_scope=SUBTREE, attributes=['member'])
    if len(c.response) == 0:
        print("Error: Group {} not found!".format(args.group))
        sys.exit()
    add_list = []
    for user in args.users:
        c.search(search_base=LDAP_USER_SCOPE, search_filter='(uid='+user+')', search_scope=SUBTREE, attributes=['uid'])
        if len(c.response) == 0:
            print("Ignoring: "+user)
            continue
        c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(&(cn='+args.group+') (member=uid='+user+','+LDAP_USER_SCOPE+'))', search_scope=SUBTREE, attributes=['member'])
        if len(c.response) == 0:
            add_list.append('uid='+user+','+LDAP_USER_SCOPE)
            print("Adding: "+user)
        else:
            print("Skipping: "+user)
    if len(add_list) > 0:
        c.modify('cn='+args.group+','+LDAP_GROUP_SCOPE, {'member': (MODIFY_ADD, add_list)})
        print(c.result['description'])


def group_removeuser(args, c):
    c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(cn='+args.group+')', search_scope=SUBTREE, attributes=['member'])
    if len(c.response) == 0:
        print("Error: Group {} not found!".format(args.group))
        sys.exit()
    rem_list = []
    for user in args.users:
        c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(&(cn='+args.group+') (member=uid='+user+','+LDAP_USER_SCOPE+'))', search_scope=SUBTREE, attributes=['member'])
        if len(c.response) == 0:
            print("Skipping: "+user)
        else:
            rem_list.append('uid='+user+','+LDAP_USER_SCOPE)
            print("Removing: "+user)
    if len(rem_list) > 0:
        c.modify('cn='+args.group+','+LDAP_GROUP_SCOPE, {'member': (MODIFY_DELETE, rem_list)})
        print(c.result['description'])



if __name__ == '__main__':

    # define argument parser
    parser = argparse.ArgumentParser(description='D120 LDAP Group Modify Script')
    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = 'command'

    parser_list = subparsers.add_parser('list', help='List members of given group')
    parser_list.add_argument('group', type=str, help='Show members of that group')
    parser_list.set_defaults(func=group_list)

    parser_create = subparsers.add_parser('create', help='Create a group with the given name')
    parser_create.add_argument('group', type=str, help='Create group with that name')
    parser_create.add_argument('-p', '--posix', action='store_true', help='Create posix group');
    parser_create.set_defaults(func=group_create)

    parser_delete = subparsers.add_parser('delete', help='Delete the group with the given name')
    parser_delete.add_argument('group', type=str, help='Delete group with that name')
    parser_delete.set_defaults(func=group_delete)

    parser_adduser = subparsers.add_parser('adduser', help='Add users to the given group')
    parser_adduser.add_argument('group', type=str, help='Add users to that group')
    parser_adduser.add_argument('users', type=str, nargs='+', help='The users which should be added to the group')
    parser_adduser.set_defaults(func=group_adduser)

    parser_removeuser = subparsers.add_parser('removeuser', help='Remove users from the given group')
    parser_removeuser.add_argument('group', type=str, help='Remove users from that group')
    parser_removeuser.add_argument('users', type=str, nargs='+', help='The users which should be removed from the group')
    parser_removeuser.set_defaults(func=group_removeuser)

    # parse args and call appropriate function
    parsed_args = parser.parse_args()
    parsed_args.func(parsed_args, init_ldap())
