#!/usr/local/bin/bash

LDAPHOST="henldap"
GROUP="group"
MASTER="master.passwd"
OUTPUT="output.ldif"
LDAPPASSWD="setthis"
LDAPMODIFY="ldapmodify -w $LDAPPASSWD "
LDAPADD="ldapadd -w $LDAPPASSWD "
LDAPSEARCHGROUP="ldapsearch -h $LDAPHOST -b \"ou=Groups,dc=cs,dc=ucl,dc=ac,dc=uk\" "
LDAPSEARCHUSER="ldapsearch -h $LDAPHOST -b \"ou=People,dc=cs,dc=ucl,dc=ac,dc=uk\" "

extract_user() {

    line=`grep \^$user: $MASTER`
    id=`echo $line | cut -f1 -d':'`
    pass=`echo $line | cut -f2 -d':'`
    gid=`echo $line | cut -f3 -d':'`
    uid=`echo $line | cut -f4 -d':'`
    fullname=`echo $line | cut -f8 -d':'`
    firstname=`echo $fullname | cut -f1 -d' '`
    surname=`echo $fullname | cut -f2 -d' '`
    homedir=`echo $line | cut -f9 -d':'`
    shell=`echo $line | cut -f10 -d':'`

    #echo $id $pass $uid $gid $fullname $homedir $shell


    if [[ `echo $pass | grep "\\$1"` == $pass ]]
	then
	type="{SHA1}"
    else
	type="{CRYPT}"
    fi

    echo "# $id, People, cs.ucl.ac.uk" >> $OUTPUT
    echo "dn: uid=$id,ou=People, dc=cs,dc=ucl,dc=ac,dc=uk" >> $OUTPUT
    echo "givenName: $firstname" >> $OUTPUT
    echo "sn: $surname" >> $OUTPUT
    echo "loginShell: $shell" >> $OUTPUT
    echo "gidNumber: $uid" >> $OUTPUT
    echo "uidNumber: $gid" >> $OUTPUT
    #mail: a.greenhalgh@cs.ucl.ac.uk"
    echo "objectClass: top" >> $OUTPUT
    echo "objectClass: person" >> $OUTPUT
    echo "objectClass: organizationalPerson" >> $OUTPUT
    echo "objectClass: inetorgperson" >> $OUTPUT
    echo "objectClass: posixAccount" >> $OUTPUT
    echo "uid: $id" >> $OUTPUT
    echo "cn: $fullname" >> $OUTPUT
    echo "preferredLanguage: en" >> $OUTPUT
    echo "homeDirectory: $homedir" >> $OUTPUT
    echo "userpassword: $type$pass" >> $OUTPUT
}

extract_general_group() {
    line=`grep ^$group: $GROUP`
    id=`echo $line | cut -f1 -d':'`
    gid=`echo $line | cut -f3 -d':'`
    members=`echo $line | cut -f4 -d':'`
    echo "# $id, Group, cs.ucl.ac.uk" >> $OUTPUT
    echo "dn: cn=$id,ou=Groups, dc=cs,dc=ucl,dc=ac,dc=uk" >> $OUTPUT
    echo "objectClass: posixGroup" >> $OUTPUT
    echo "objectClass: groupofuniquenames" >> $OUTPUT
    echo "objectClass: top" >> $OUTPUT
    echo "cn: $id" >> $OUTPUT
    echo "userPassword: {crypt}*" >> $OUTPUT
    echo "gidNumber: $gid" >> $OUTPUT
    for guser in `echo $members | sed 's/,/ /g'`
    do
      echo "memberUid: $guser" >> $OUTPUT
    done
}

check_user_ldap() {
    res=`ldapsearch -h henldap -b "dc=cs,dc=ucl,dc=ac,dc=uk" uid=$user | grep  numEntries | cut -f3 -d' '`
    #echo "res : "$res
    if [[ $res -eq 1 ]]; then
	#echo "current person"
	return 1
    else
	#echo "new person"
	return 0
    fi
}

check_group_ldap() {
    
    ldapsearch -h henldap -b "ou=Groups,dc=cs,dc=ucl,dc=ac,dc=uk"  cn=$group  > search.tmp
    grep -q numEntries search.tmp
    if [[ $? -eq 1 ]]; then
	#echo "new group"
	return 0
    else
	#echo "current group"
	return 1
    fi
}

check_user_passwd() {
    grep -q ^$user: $MASTER
    if [[ $? -eq 0 ]]; then
      return 0
    else
      return 1
    fi
}

check_group_exists() {
    grep -q ^$group: $GROUP
    if [[ $? -eq 0 ]]; then
      return 0
    else
      return 1
    fi
}

add_user() {
    rm -f $OUTPUT
    touch $OUTPUT

    check_user_passwd
    if [[ $? -eq 0 ]]; then 
	extract_user
	echo "Adding user "$user
	check_user_ldap
	if [[ $? -eq 0 ]]; then
	    #echo "ldapadd"
	    $LDAPADD -D"cn=Directory Manager" -f $OUTPUT
	else
	    #echo "ldapmodify"
    	    $LDAPMODIFY -D"cn=Directory Manager" -f $OUTPUT
	fi
	group=$user
        add_group
    else
	echo "Failed to add user "$user
    fi
}

add_group() {
    rm -f $OUTPUT
    touch $OUTPUT

    check_group_exists
    if [[ $? -eq 0 ]]; then 
	extract_general_group
	echo "Adding group "$group
	echo "" >> $OUTPUT
	check_group_ldap
	if [[ $? -eq 0 ]]; then
	    echo "ldapadd"
	    $LDAPADD -D"cn=Directory Manager" -f $OUTPUT
	else
	    $LDAPMODIFY -D"cn=Directory Manager" -f $OUTPUT
	fi
    else
	echo "Failed to add group "$group
    fi
}


usage_msg() {
    echo "syntax: $0 -u user user -g group group"
}

SN="NONE"
SU="USER"
SG="GROUP"

state=$SN

if [[ $# -eq 0 ]]; then
    usage_msg
    exit 1
fi

for i in $@ 
do
  #echo $i $state
  user=""
  group=""
  if [[ $i == "-u" ]]; then
      #echo "user start"
      state=$SU
  elif [[ $i == "-g" ]]; then 
      state=$SG
  else
      if [[ $state == $SU ]]; then
	  user=$i
	  add_user
      elif [[ $state == $SG ]]; then
	  group=$i
	  add_group
      else
	  usage_msg
	  exit 1
      fi
  fi      
done