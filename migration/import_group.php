#!/usr/bin/env php
<?php
  $file = fopen('group', 'r');
  while (($data = fgets($file)) !== false) {
    $obj = explode(':', trim($data));
    if (strlen(trim($obj[3])) == 0)
      continue;
    echo getDn($obj[0]);
    echo "changetype: add\n";
    echo "objectclass: groupOfNames\n";
    echo "objectclass: posixGroup\n";
    echo "objectclass: top\n";
    echo "cn: ".$obj[0]."\n";
    echo "gidNumber: ".$obj[2]."\n";
    parseMembers($obj[3]);
    echo "\n";
  }

function parseMembers($data) {
  $members = explode(",", $data);
  foreach ($members as $member) {
    $member = trim($member);
    if (empty($member))
      continue;
    echo "member: ".getFQN($member)."\n";
  }
}

function getDn($name) {
  return "dn: cn=".$name.",ou=Group,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de\n";
}

function getFQN($name) {
  return "uid=".$name.",ou=People,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de";
}
