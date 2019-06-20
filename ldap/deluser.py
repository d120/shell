#!/usr/bin/env python3

import getpass
import sys
import crypt
import argparse
import subprocess
import datetime
from ldap_connection import init_ldap, LDAP_USER_SCOPE, LDAP_GROUP_SCOPE, LDAP_FORWARD_SCOPE
from ldap3 import SEARCH_SCOPE_WHOLE_SUBTREE, MODIFY_ADD, MODIFY_DELETE

DEFAULT_SHELL = '/bin/bash'
IGNORE_UIDNUMBERS_ABOVE = 4999
MAIL_DOMAINS = ["d120.de", "fachschaft.informatik.tu-darmstadt.de"]


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def findAliases(userAliases):
    aliases = []
    for userAlias in userAliases:
        aliasSearch = '(mailTarget=' + userAlias + ')'
        c.search(search_base=LDAP_FORWARD_SCOPE, search_filter=aliasSearch, search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['mailAlias', 'mailTarget'])
        for alias_obj in c.response:
            alias_alias = alias_obj['attributes']['mailAlias']
            if len(alias_alias) != 0:
                aliases.append((alias_alias[0], userAlias, len(alias_obj['attributes']['mailTarget'])))
    return aliases

def findLists(aliases):
    unflattened_addresses = [["{}@{}".format(alias,domain) for domain in MAIL_DOMAINS] for alias in aliases]
    addresses = [val for sublist in unflattened_addresses for val in sublist]
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
                list_memberships.append((line.strip(), mail))
    return list_memberships

def safe_delete_directory(directory):
    try:
        subprocess.check_call(["sudo", "ls", directory], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        print("Deleting {}...".format(directory))
        subprocess.call(["sudo", "rm", "-rf", directory])
    except subprocess.CalledProcessError as e:
        print("Skipping delete of {} because it does not exist".format(directory))


def main(args):
    print("Please authenticate using sudo...")
    subprocess.call(["sudo", "true"])
    global c
    c = init_ldap()
    uid = arg_data.uid[0]
    # Get User DN
    c.search(search_base=LDAP_USER_SCOPE, search_filter='(uid='+uid+')', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['mailAlias', 'uidNumber', 'displayName', 'homeDirectory', 'objectClass'])
    if len(c.response) == 0:
        print("Error: User {} not found!".format(uid))
        sys.exit()
    user_dn = c.response[0]['dn']
    attributes = c.response[0]['attributes']

    # Let admin verify DN
    print()
    if not query_yes_no("Is this DN correct for the user to be deleted? {}".format(user_dn)):
        sys.exit()

    # Get groups user is member of
    c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(member='+user_dn+')', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['cn'])
    groups = []
    for grp_obj in c.response:
        group_cn = grp_obj['attributes']['cn']
        if len(group_cn) != 0:
            groups.append (group_cn[0])

    # Get aliases and email addresses of the user
    objClasses = attributes['objectClass']
    if 'd120mailUser' in objClasses:
        addresses = attributes['mailAlias']
        aliases = findAliases(attributes['mailAlias'])
    else:
        addresses = []
        aliases = []

    # Get mailing lists user is a member of
    mailing_lists = findLists(addresses)

    print('This script will delete the following user:')
    print("username:\t {}".format(uid))
    print("displayName:\t {}".format(attributes['displayName'][0]))
    print("uid:\t\t {}".format(attributes['uidNumber'][0]))
    print("home:\t\t {}".format(attributes['homeDirectory'][0]))
    print("dn:\t\t {}".format(user_dn))
    print()
    if addresses:
        print("mail addresses:\t {}".format(", ".join(addresses)))
    if groups:
        print("groups:\t\t {}".format(", ".join(groups)))
    if aliases:
        print("aliases:\t {}".format(", ".join(["{} (total {})".format(alias, num) for (alias, target, num) in aliases])))
    if mailing_lists:
        print("mailing lists:\t {}".format(", ".join([mailing_list for (mailing_list, mail) in mailing_lists])))
    print()

    # Ask whether to create a mail forward
    if addresses:
        forwardAddress = input("This user has some email addresses. Enter a new address to create a forwarding. Empty address will not create any: ")
        print()

    # For aliases that would become empty, confirm that they will be deleted completely
    aliases_to_remove_user_from = []
    aliases_to_delete_completely = []
    if aliases:
        for (alias, target, num) in aliases:
            if num > 1:
                aliases_to_remove_user_from.append((alias, target, num))
            else:
                if query_yes_no("Alias {} would become empty, do you want to remove the alias object?".format(alias)):
                    aliases_to_delete_completely.append(alias)
                else:
                    print("Alias {} can not get empty. Aborting this script.".format(alias))
                    sys.exit()
        print()

    print("Looking for files belonging to the user...")
    files_to_adjust_filename = "/tmp/deluser-{}-files.txt".format(uid)
    with open(files_to_adjust_filename, "w") as f:
        subprocess.call(["sudo", "find", "/mnt/media", "-user",  uid], stdout=f)
    number_of_files = int(subprocess.check_output(["wc", "-l", files_to_adjust_filename]).decode().split(" ")[0])
    if number_of_files == 0:
        print("There are no files belonging to this user in /mnt/media")
    else:
        print("Found {} files belonging to {} in /mnt/media. Review them by looking at {}".format(number_of_files, uid, files_to_adjust_filename))
    print()

    # Let admin verify
    if not query_yes_no("Proceed to delete?", default="no"):
        sys.exit()
    print()

    # just as a safety precaution for the following rm commands, exit if uid is empty
    if not uid:
        sys.exit()

    # Remove user from groups
    if groups:
        for group in groups:
            print("Removing {} from group {}...".format(uid, group))
            c.modify('cn='+group+','+LDAP_GROUP_SCOPE, {'member': (MODIFY_DELETE, ['uid='+uid+','+LDAP_USER_SCOPE])})

    # Remove user from aliases
    if aliases_to_remove_user_from:
        for (alias, target, num) in aliases_to_remove_user_from:
            print("Removing {} from alias {}, {} members remaining...".format(target, alias, num-1))
            c.modify('mailAlias='+alias+','+LDAP_FORWARD_SCOPE, {'mailTarget': (MODIFY_DELETE, [target])})

    # Remove aliases that would get empty
    if aliases_to_delete_completely:
        for alias in aliases_to_delete_completely:
            print("Removing alias {}...".format(alias))
            c.delete('mailAlias='+alias+','+LDAP_FORWARD_SCOPE)

    # Remove user from mailing lists
    if mailing_lists:
        for (mailing_list, mail) in mailing_lists:
            print("Removing from mailing list {}...".format(mailing_list))
            subprocess.call(["sudo", "remove_members", mailing_list, mail])

    # Delete home directory
    safe_delete_directory("/home/{}".format(uid))

    # Delete public_html directory
    safe_delete_directory("/mnt/public_html/homes/{}".format(uid))

    # Delete maildir
    safe_delete_directory("/mnt/vmail/{}".format(uid))

    # Create LDAP mailForward object for all mail addresses
    if addresses and forwardAddress:
        print("Forwarding all email addresses to {}...".format(forwardAddress))
        firstAddress = addresses[0]
        attrs = {}
        attrs["mailAlias"] = addresses
        attrs["mailTarget"] = forwardAddress
        attrs["description"] = "Forwarding for former user {}, deleted at {}".format(uid, datetime.datetime.now().strftime("%Y-%m-%d"))
        c.add("mailAlias=" + firstAddress + "," + LDAP_FORWARD_SCOPE, ["d120mailForward"], attrs)
    else:
        print("Skipping creation of any forward objects")

    # Adjust file ownerships for any files that belong to this user
    if number_of_files > 0:
        print("Changing owners to root for {} files belonging to {}...".format(number_of_files, uid))
        subprocess.call(["sudo", "xargs", "--arg-file", files_to_adjust_filename, "-d", "\\n", "chown", "root"])
    else:
        print("Skipping ownership changes for any files")

    # Delete LDAP user object
    print("Deleting user object {}...".format(uid))
    c.delete('uid='+uid+','+LDAP_USER_SCOPE)

    print("\nMy job here is done. Have a super nice day :)")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='d120-deluser')
    parser.add_argument('uid', metavar='username', type=str, nargs=1, help='User to be deleted')
    arg_data = parser.parse_args()
    try:
        main(arg_data)
    except KeyboardInterrupt:
        print("\nAborted by user!")
        sys.exit()
