<!-- $Id: prova.php 666 2006-09-16 11:18:59Z abittau $ -->
<html>
<title>w00t</title>
<body>
<?
	$ldaphost = "ldaps://arkell.cs.ucl.ac.uk";
	$ldapuser = "cn=root,o=hen,dc=cs,dc=ucl,dc=ac,dc=uk";
	$ldapbase = "o=hen,dc=cs,dc=ucl,dc=ac,dc=uk";
	$url = $_SERVER['PHP_SELF'];

	import_request_variables("p", "p_");

	if (isset($p_password)) {
		own();
	}
	else {
		echo "<form action=\"$url\" method=\"post\">\n";
		echo "Password: <input type=text name=password>\n";
		echo "<input type=submit></form>\n";
	}

	function connect() {
		global $ldaphost, $ldapuser, $p_password;

		$s = ldap_connect($ldaphost);
		if (!$s) {
			echo "ldap_connect()";
			return false;
		}
		
		ldap_set_option($s, LDAP_OPT_PROTOCOL_VERSION, 3); 

		$r = ldap_bind($s, $ldapuser, $p_password);
		if (!$r) {
			echo "ldap_bind(): ";
			echo ldap_error($s);
			ldap_close($s);
			return false;
		}

		return $s;
	}

	function check_pass() {
		$s = connect();
		if (!$s)
			return false;
		
		ldap_close($s);
		return true;
	}

	function own() {
		global $p_password, $url;
		global $p_changep, $p_view, $p_edit, $p_mod, $p_add;
		global $p_doadd, $p_delete;

		if (!check_pass())
			return;

		if (isset($p_changep)) {
			if(!change_pass())
				return;
		}

		echo "<form action=\"$url\" method=\"post\">\n";
		echo "<input type=hidden name=\"password\" value=\"$p_password\">\n";
	
		if (isset($p_view)) {
			display_users();
		} else if (isset($p_edit)) {
			edit_dude();
		} else if (isset($p_mod)) {
			mod_dude();
		} else if (isset($p_add)) {
			add_dude();
		} else if (isset($p_doadd)) {
			do_add_dude();
		} else if (isset($p_delete)) {
			do_delete_dude();
		}
		else
			display_main();
		
		echo "</form>\n";
	}

	function do_delete_dude() {
		global $p_dn;

		echo "Deleting $p_dn<br>\n";

		$s = connect();
		if (!$s)
			return false;
	
		$r = ldap_delete($s, $p_dn);
		ldap_close($s);

		if (!$r) {
			echo "ldap_delete()";
			return false;
		}

		echo "Owned<br>\n";
		return true;
	}

	function fix_pass($pass) {
		$p = "{md5}".base64_encode(pack("H*",md5($pass)));

		return $p;
	}

	function do_add_dude() {
		global $ldapbase;
		global $p_login, $p_name, $p_uid, $p_gid; 
		global $p_shell, $p_home, $p_pass;
	
		$dn = "uid=$p_login" . ",ou=accounts," . $ldapbase;

		echo "Adding $dn<br>\n";
		
		$values["objectclass"][0] = "person";
		$values["objectclass"][1] = "posixAccount";
		$values["objectclass"][2] = "shadowAccount";
		$values["cn"] = $p_login;
		$values["uid"] = $p_login;
		$values["uidnumber"] = $p_uid;
		$values["loginshell"] = $p_shell;
		$values["sn"] = $p_name;
		$values["userpassword"] =  fix_pass($p_pass);
		$values["homedirectory"] = $p_home;
		$values["gidnumber"] = $p_gid;

		$s = connect();
		if (!$s)
			return false;

		$r = ldap_add($s, $dn, $values);
		if (!$r) {
			echo "ldap_add(): " . ldap_error($s);
			ldap_close($s);
			return false;
		}
		ldap_close($s);

		echo "Owned<br>\n";
		return true;
	}

	function add_dude() {
		echo "Login: <input type=text name=login><br>\n";
		echo "name: <input type=text name=name><br>\n";
		echo "UID: <input type=text name=uid><br>\n";
		echo "GID: <input type=text name=gid><br>\n";
		echo "shell: <input type=text name=shell><br>\n";
		echo "home: <input type=text name=home><br>\n";
		echo "pass: <input type=text name=pass><br>\n";
		echo "<input type=submit name=doadd><br>\n";
	}

	function mod_dude() {
		global $p_mod, $p_dn;

		$val = $GLOBALS["p_" . $p_mod]; 

		if ($p_mod == "userpassword")
			$val = fix_pass($val);

		echo "Modifying $p_dn: $p_mod to $val<br>\n";

		$s = connect();
		if (!$s)
			return false;
		$values["$p_mod"] = $val;

		$r = ldap_modify($s, $p_dn, $values);
		ldap_close($s);

		if (!$r) {
			echo "ldap_modify()";
			return false;
		}
		echo "Owned<br>\n";
		return true;
	}

	function edit_dude() {
		global $p_edit;
		global $ldapbase;

		$s = connect();
		if (!$s)
			return false;

		echo "Editing UID: $p_edit<br>\n";
		$r = ldap_search($s, $ldapbase, "(&(objectclass=posixAccount)(uidNumber=$p_edit))");
		if (!$r) {
			echo "ldap_search()";
			ldap_close($s);
			return false;
		}

		$info = ldap_get_entries($s, $r);
		ldap_close($s);
		if (!$info) {
			echo "ldap_get_entries()";
			return false;
		}	

		$entries = $info["count"];
	
		if ($entries != 1) {
			echo "Error: $entries entries found\n";
			return;
		}

		$attrs = $info[0]["count"];
		$dn = $info[0]["dn"];
		echo "Found $attrs attributes for $dn<br>\n";
		echo "<input type=hidden name=dn value=\"$dn\">\n";
		for ($i = 0; $i < $attrs; $i++) {
			$attrname = $info[0][$i];
			$val = $info[0]["$attrname"][0];

			echo "<input type=submit name=mod value=\"$attrname\">\n";
			echo "<input type=text name=\"$attrname\" value=\"$val\">\n";
			echo "<br>\n";
		}
		echo "<input type=submit name=delete value=delete>\n";

		return true;
	}

	function change_pass() {
		global $p_newp, $p_password;

		
		echo "sorry doesn't work...\n";
		return false;

		$s = connect();
		if (!$s)
			return false;
	
	
		ldap_close($s);
		$p_password = $p_newp;
		echo "Changed pass to: $p_password";
		return true;
	}

	function display_main() {
		echo "New pass: <input type=text name=newp>\n";
		echo "<input type=submit name=\"changep\" value=change><br>\n";
		echo "<input type=submit name=view value=\"View Users\">\n";
		echo "<input type=submit name=add value=\"Add Users\">\n";
	}

	function display_users() {
		global $ldapbase;

		$s = connect();
		if (!$s)
			return false;

		$r = ldap_search($s, $ldapbase, "(objectclass=posixAccount)");
		if (!$r) {
			echo "ldap_search()";
			ldap_close($s);
			return false;
		}

		$info = ldap_get_entries($s, $r);
		ldap_close($s);
		if (!$info) {
			echo "ldap_get_entries()";
			return false;
		}	

		$entries = $info["count"];
		echo "Got $entries entries<br>\n";
		
		for ($i = 0; $i < $entries; $i++) {
			$login = $info[$i]["uid"][0];
			$uid = $info[$i]["uidnumber"][0];
			echo "Login: $login, Uid: ";
			echo "<input type=submit name=edit value=$uid><br>\n";
		}

		return true;
	}
?>
</body>
</html>
