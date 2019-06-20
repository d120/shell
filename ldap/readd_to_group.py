from sys import argv, exit
from ldap_connection import init_ldap, LDAP_USER_SCOPE, LDAP_GROUP_SCOPE
from ldap3 import Server, Connection, ALL_ATTRIBUTES, SEARCH_SCOPE_WHOLE_SUBTREE, MODIFY_ADD, MODIFY_DELETE
from groupmod import get_uid_by_dn

if len(argv) != 2:
    print("Wrong number of parameters,  group name needed")
    exit(-1)

group = argv[1]

c = init_ldap()
c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(cn='+group+')', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['member'])    
if len(c.response) == 0:
    print("Error: Group {} not found!".format(group))
    exit()
user_list = c.response[0]['attributes']['member']
user_list_dn = [get_uid_by_dn(user) for user in user_list]
print(user_list_dn)
print("Removing users")
for user in user_list_dn:
    rem_list = []
    c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(&(cn='+group+') (member=uid='+user+','+LDAP_USER_SCOPE+'))', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['member'])
    if len(c.response) == 0:
        print("Skipping: "+user)
    else:
        rem_list.append('uid='+user+','+LDAP_USER_SCOPE)
        print("Removing: "+user)
    if len(rem_list) > 0:
        c.modify('cn='+group+','+LDAP_GROUP_SCOPE, {'member': (MODIFY_DELETE, rem_list)})
        print(c.result['description'])
    
    print("Adding users again")
    add_list = []
    c.search(search_base=LDAP_USER_SCOPE, search_filter='(uid='+user+')', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['uid'])
    if len(c.response) == 0:
        print("Ignoring: "+user)
        continue
    c.search(search_base=LDAP_GROUP_SCOPE, search_filter='(&(cn='+group+') (member=uid='+user+','+LDAP_USER_SCOPE+'))', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['member'])
    if len(c.response) == 0:
        add_list.append('uid='+user+','+LDAP_USER_SCOPE)
        print("Adding: "+user)
    else:
        print("Skipping: "+user)
    if len(add_list) > 0:
        c.modify('cn='+group+','+LDAP_GROUP_SCOPE, {'member': (MODIFY_ADD, add_list)})
        print(c.result['description'])
