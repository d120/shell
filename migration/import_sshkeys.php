#!/usr/bin/php
<?php
  echo "Please enter LDAP admin password: ";
  system('stty -echo');
  $admin_pw = trim(fgets(STDIN));
  system('stty echo');
  echo "\n";

  $ld_conn = ldap_connect('glados', 389);
  ldap_set_option($ld_conn, LDAP_OPT_PROTOCOL_VERSION, 3);
  $bind = ldap_bind($ld_conn, "cn=admin,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de", $admin_pw);

  $sr     = ldap_search($ld_conn,"ou=People,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de","(uid=*)");
  $info   = ldap_get_entries($ld_conn,$sr);

  $buffer = '';

  for ($i = 0; $i < $info['count']; $i ++) {
    $user = $info[$i]['uid'][0];
    $file = @file_get_contents('/home/'.$user.'/.ssh/authorized_keys');
    if (!$file)
      continue;
    $keys = explode("\n", trim($file));
    setUserKeys($user, $keys);
  }

  $file = fopen('keys.ldif', 'w');
  fwrite($file, $buffer);
  fclose($file);

  function setUserKeys($user, $keys) {
    global $buffer;
    $buffer .= "dn: uid=".$user.",ou=People,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de\n";
    $buffer .= "changetype: modify\n";
    $buffer .= "add: sshPublicKey\n";
    foreach ($keys as $key) {
      $buffer .= "sshPublicKey:: \"".base64_encode($key)."\"\n";
    }
    $buffer .= "\n";
  }

?>
