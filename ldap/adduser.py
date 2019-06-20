#!/usr/bin/env python3

import getpass
import sys
import crypt
import argparse
from ldap_connection import init_ldap, LDAP_USER_SCOPE, LDAP_GROUP_SCOPE
from ldap3 import SEARCH_SCOPE_WHOLE_SUBTREE, MODIFY_ADD

DEFAULT_SHELL = '/bin/bash'
IGNORE_UIDNUMBERS_ABOVE = 4999

def replace_umlauts(s):
    return s.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')


def main(args):
    c = init_ldap()

    if len(args.group) == 0:
        args.group.append("fachschaft")
    # Template for Ophase Users
    # No real account will be created
    elif len(args.group) == 1 and args.group[0] == 'ophase':
        args.nomail = True
        args.noposix = True
    print("Groups: " + ', '.join(args.group));
    if args.nomail:
        print("No Mail Account");
    if args.noposix:
        print("No Posix Account");

    print("#########################################")
    print("##                                     ##")
    print("##          Create new User            ##")
    print("##                                     ##")
    print("#########################################")
    print("")
    print("Please enter the following details:")
    print("")

    while "given_name" not in locals() or not given_name:
        given_name = input("Given name: ")
    while "surname" not in locals() or not surname:
        surname = input("Name: ")
    mobile   = input("Mobile [+49 (151) 12345]: ")
    phone    = input("Home phone [+49 (6151) 16-1234]: ")
    if args.nomail:
        mail_input = input("E-mail address: ")

    uuid     = 0
    gid      = 1099

    c.search(search_base=LDAP_USER_SCOPE, search_filter='(uid=*)', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['uidNumber'])

    uids = []
    uids.append(1000)
    for x in c.response:
        if 'uidNumber' not in x['attributes']:
            continue
        the_attrs = x['attributes']
        the_uid_number = int(the_attrs["uidNumber"][0])
        if the_uid_number > IGNORE_UIDNUMBERS_ABOVE:
            continue
        uids.append(the_uid_number)
    uids.sort(reverse=True)

    uuid = uids[0]+1
    uid = (given_name[0] + surname).lower()
    uid = replace_umlauts(uid)

    print("")

    while True:
        c.search(search_base=LDAP_USER_SCOPE, search_filter='(uid=' + uid + ')', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['uidnumber'])
        if len(c.response) == 0:
            break
        print("UID " + uid + " is already in use")
        uid = input("Login name: ")

    home = "/home/" + uid
    if not args.nomail:
        maildrop = "/mnt/vmail/" + uid
        long_mail_prefix = replace_umlauts((given_name + "." + surname).lower())
        mail = long_mail_prefix + "@fachschaft.informatik.tu-darmstadt.de"
        mailaliases = [uid, long_mail_prefix]
    else:
        mail = mail_input

    print("")
    print("Following fields will be set:")
    print("uid:\t\t" + uid)
    print("givenName:\t" + given_name)
    print("sn:\t\t" + surname)
    print("cn:\t\t" + uid)
    print("displayname:\t" + given_name + " " + surname)
    if not args.noposix:
        print("uidnumber:\t" + str(uuid))
        print("gidnumber:\t" + str(gid))
        print("homeDirectory:\t" + home)
    if mobile:
        print("mobile:\t\t" + mobile)
    if phone:
        print("telephoneNumber:\t" + phone)
    print("mail:\t" + mail)
    if not args.nomail:
        for maddr in mailaliases:
            print("mailAlias:\t\t" + maddr)
    if not args.noposix:
        print("loginShell:\t" + DEFAULT_SHELL)

    cont = input("Continue? (YES/no): ")
    if (cont[0:1]).lower() == "n":
        sys.exit()

    objectClasses   = ["top","d120person","ldapPublicKey"]
    attrs = {}
    attrs['cn']            = uid
    attrs['displayName']   = given_name + " " + surname
    if not args.noposix:
        attrs['gidNumber']     = gid
        attrs['homeDirectory'] = home
        attrs['uidNumber']     = str(uuid)
        attrs['loginShell']    = DEFAULT_SHELL
        objectClasses.append("posixAccount")
    attrs['sn']            = surname
    attrs['uid']           = uid
    attrs['givenName']     = given_name
    attrs['mail']          = mail
    if not args.nomail:
        attrs['mailAlias']     = mailaliases
        objectClasses.append("d120mailUser")

    if mobile:
        attrs['mobile']    = mobile
    if phone:
        attrs['telephoneNumber'] = phone

    c.add("uid=" + uid + "," + LDAP_USER_SCOPE, objectClasses, attrs)
    print(c.result);
    if c.result['result'] != 0:
        print("User creation FAILED, error code %d" % (c.result.result,))
        sys.exit(1)


    for grp in args.group:
        c.modify('cn=' + grp + ',' + LDAP_GROUP_SCOPE, {'member': (MODIFY_ADD, ['uid=' + uid + ',' + LDAP_USER_SCOPE])})

    print(c.result);
    print("User " + uid + " created.")

    userpw = "1"
    userpw2 = "2"
    while userpw != userpw2:
        userpw = getpass.getpass("Please type new password: ")
        userpw2 = getpass.getpass("Please retype password: ")

    passfield = "{crypt}" + crypt.crypt(userpw)
    c.modify("uid=" + uid + "," + LDAP_USER_SCOPE, {'userPassword': (MODIFY_ADD, [passfield])})
    if c.result['result'] != 0:
        print("Passwort change FAILED, error code %d" % (c.result.result,))
        sys.exit(1)
    #ld_con.unbind_s()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='d120-adduser')
    parser.add_argument('--group', '-g', action='append', default=[])
    parser.add_argument('--nomail', action='store_true')
    parser.add_argument('--noposix', action='store_true')
    arg_data = parser.parse_args()
    try:
        main(arg_data)
    except KeyboardInterrupt:
        print("\nAborted by user!")
        sys.exit()
