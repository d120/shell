# ldap-scripts
Serveral ldap management scripts

## Zu Beachten beim Anlegen/Ändern von Mailadressen
nach Aktionen, bei denen eine Mailadresse angelegt, geändert oder
gelöscht wird, auf der wir Mails empfangen, muss auf Glados "sudo
update-mail-stuff" ausgeführt werden.

Dieses Skript aktualisiert derzeit folgende Listen:

* die Whitelist für eingehende Mails beim HRZ
* die Weiterleitungen von mailingliste@d120.de und mailingliste@lists.d120.de


Es muss ausgeführt werden unter anderem in folgenden Fällen:
* nach dem Anlegen eines Users
* nach dem Anlegen einer Mailingliste
* ...

chsh.sh:
A script to change your ldap shell used as your login shell
