#!/usr/bin/bash
./ldap-enrich.py  --sLdap="ldap://127.0.0.1/" \
		--sBind="cn=admin,dc=phonax" \
		--sPass="Phonax01" \
        --sBaseDN="ou=source,ou=users,dc=phonax" \
		--sAttribs="loginShell, description" \
		--sFilter="(&(objectClass=posixAccount)(cn=user1))" \
		--dLdap=ldap://127.0.0.1 \
		--dBind="cn=admin,dc=phonax" \
		--dPass="Phonax01" \
        --dBaseDN="ou=dest,ou=users,dc=phonax" \
		--dAttribs="loginShell, description" \
		--dFilter="(&(objectClass=posixAccount)(cn=*))" \
        --simulate \  #remove simulate to run on the ldap 
        #--replace \  #would override attributes that have a different value in the dest than the source; this is generally unwanted