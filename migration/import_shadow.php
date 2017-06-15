#!/usr/bin/php
<?php
  echo "Please enter admin password: ";
  system('stty -echo');
  $admin_pw = trim(fgets(STDIN));
  system('stty echo');
  echo "\n";

  $ld_conn = ldap_connect('localhost', 389);
  ldap_set_option($ld_conn, LDAP_OPT_PROTOCOL_VERSION, 3);
  $bind = ldap_bind($ld_conn, "cn=admin,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de", $admin_pw);

  $sr     = ldap_search($ld_conn,"ou=People,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de","(uid=*)");
  $info   = ldap_get_entries($ld_conn,$sr);
  
  $users      = [];
  $passwords  = [];

  $file = fopen('shadow', 'r');
  while(($data = fgets($file)) !== false) {
    $items = explode(':', $data);
    $passwords[$items[0]] = $items[1];
  }
  fclose($file);

  $buffer = '';

  for ($i = 0; $i < $info['count']; $i ++) {
    $user = $info[$i]['uid'][0];
    if(!isset($passwords[$user])) {
      echo "No password found: ".$user."\n";
    }
    setUserPassword($user, $passwords[$user]);
  }

  $file = fopen('shadow.ldif', 'w');
  fwrite($file, $buffer);
  fclose($file);

  function setUserPassword($user, $pw) {
    global $buffer;
    $pass = "{crypt}".$pw;
    $buffer .= "dn: uid=".$user.",ou=People,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de\n";
    $buffer .= "changetype: modify\n";
    $buffer .= "add: userPassword\n";
    $buffer .= 'userPassword:: "'.base64_encode($pass).'"';
    $buffer .= "\n\n";
  }

?>
