#!/usr/bin/php
<?php
  /* Converts passwd with gecos fields to ldif
     Adds new users mit class InetOrgPerson
  */
  header('Content-Type: text/plain');
  $file = fopen('passwd', 'r');
  while (($data = fgets($file)) !== false) {
    $obj = explode(':', trim($data));
    if ($obj[2] < 1000)
      continue;
    if ($obj[6] === "/bin/false")
      continue;
    getDn($obj[0]);
    echo "changetype: add\n";
    echo "objectclass: inetOrgPerson\n";
    echo "objectclass: posixAccount\n";
    echo "objectclass: shadowAccount\n";
    echo "objectclass: ldapPublicKey\n";
    echo "objectclass: top\n";
    echo "uid: ".$obj[0]."\n";
    echo "uidnumber: ".$obj[2]."\n";
    echo "gidnumber: 999\n";
    echo "homedirectory: ".$obj[5]."\n";
    parseGecos($obj[4]);
    echo "mail: ".$obj[0]."@fachschaft.informatik.tu-darmstadt.de\n";
    echo "loginshell: ".$obj[6]."\n";
    echo "\n";
  }

function parseGecos($data) {
  if(is_null($data))
    return false;
  $arr = explode(',', $data);
  echo "cn: ".$arr[0]."\n";
  echo "displayname: ".$arr[0]."\n";

  $name = preg_split('/ /', $arr[0]);
  $sn = $name[sizeof($name) - 1];
  $given = implode(array_slice($name, 0, sizeof($name) -1), ' ');
  echo "givenname: ".$given."\n";
  echo "sn: ".$sn."\n";


  parseNumber($arr[2]);
  parseNumber($arr[3]);

}

function getDn($name) {
  echo "dn: uid=".$name.",ou=People,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de\n";
}

function parseNumber($num) {
  $num = preg_replace('/[^0-9+]/', '', $num);
  $num = preg_replace('/^00/', '+', $num);
  $num = preg_replace('/^0/', '+49', $num);
  if(isMobile($num)) {
    echo "mobile: ".$num."\n";
  }
  if(strlen($num > 5) && !isMobile($num)) {
    echo "homephone: ".$num."\n";
  }
  
}

function isMobile($num) {
  return (preg_match('/^\+491/',$num) === 1);
}
