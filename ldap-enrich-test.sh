#!/usr/bin/bash
./ldap-enrich.py  --sLdap="ldap://127.0.0.1/" \
		--sBind="cn=admin,dc=phonax" \
		--sPass="Phonax01" \
        --sBaseDN="ou=source,ou=users,dc=phonax" \
		--sAttribs="loginShell, description, street, postalCode" \
		--sFilter="(&(objectClass=posixAccount)(cn=user1))" \
		--dLdap=ldap://127.0.0.1 \
		--dBind="cn=admin,dc=phonax" \
		--dPass="Phonax01" \
        --dBaseDN="ou=dest,ou=users,dc=phonax" \
		--dAttribs="loginShell, description, street, postalCode" \
		--dFilter="(&(objectClass=posixAccount)(cn=*))" \
        #--replace
