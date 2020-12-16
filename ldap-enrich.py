#!/usr/bin/python2

#This program selects a single source object, from which the attribues sAttributes are copied over to the found destination objects
#When replace option is False then existing destination attributes are not updated

from optparse import OptionParser
import sys
import ldap
import ldap.modlist as modlist  
import six

#LDAP connection wrapper
def connectLdap(url, binddn, password):
    try:
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        l = ldap.initialize(url)
        l.set_option(ldap.OPT_REFERRALS ,0)
        l.set_option(ldap.OPT_REFERRALS, 0)
        l.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        l.set_option(ldap.OPT_X_TLS,ldap.OPT_X_TLS_DEMAND)
        l.set_option(ldap.OPT_X_TLS_DEMAND, True)
        l.set_option(ldap.OPT_DEBUG_LEVEL, 255)
        l.simple_bind_s(binddn, password)
        return l
    except ldap.LDAPError as e:
        print("LDAP error: %s -- executution halted" % e)
        sys.exit(2)

# Do searches until we run out of "pages" to get from the LDAP server.
def pagedSearch(connect, basedn, filter, attribs):
    page_control = ldap.controls.libldap.SimplePagedResultsControl(True, size=1000, cookie='')
    response = connect.search_ext(basedn, ldap.SCOPE_SUBTREE, filter, attribs, serverctrls=[page_control])
    result = {}
    pages = 0
    while True:
        pages += 1
        rtype, rdata, rmsgid, serverctrls = connect.result3(response)

        for r in rdata:
          result[r[0]] = r[1]

        controls = [control for control in serverctrls if control.controlType == ldap.controls.libldap.SimplePagedResultsControl.controlType]
        if not controls:
            print('The server ignores RFC 2696 control')
            break
        if not controls[0].cookie:
            break
        page_control.cookie = controls[0].cookie
        response = connect.search_ext(basdn, ldap.SCOPE_SUBTREE, filter, attribs, serverctrls=[page_control])
    return result

#Parse the options
def options():
    parser = OptionParser()
    parser.add_option("--sLdap", dest="source", help="LDAP url of source")
    parser.add_option("--sBind", dest="sourceBind", help="source bind")
    parser.add_option("--sPass", dest="sourcePass", help="source password")
    parser.add_option("--sBaseDN", dest="sBaseDN", help="source password")
    parser.add_option("--sAttribs", dest="sAttribs", help="comma seperated attributes to copy") 
    parser.add_option("--sFilter", dest="sFilter", help="source filter which objects to select")

    parser.add_option("--dLdap", dest="dest", help="LDAP url of destination")
    parser.add_option("--dBind", dest="destBind", help="dest bind")
    parser.add_option("--dPass", dest="destPass", help="dest password")
    parser.add_option("--dBaseDN", dest="dBaseDN", help="source password")
    parser.add_option("--dFilter", dest="dFilter", help="destination filter which objects to get receive the attributes")
    parser.add_option("--dAttribs", dest="dAttribs", help="comma seperated attributes to be copied (matching 1 to 1 with sAttrib)") 

    parser.add_option("-r", "--replace", action="store_true", dest="replace", help="replace destination attributes when they differ between source and dest, default is false", default=False) 
    parser.add_option("-t", "--simulate", action="store_true", dest="simMode", help="Only print output do not update", default=False) 

    return parser.parse_args()

#Split a comma seperated string into an array and strip leading and trailing spaces
def splitComma(data):
    return [x.strip() for x in data.split(',')]

if __name__ == "__main__":
    options, remainder = options()

    source = connectLdap(options.source, options.sourceBind, options.sourcePass)
    dest = connectLdap(options.dest, options.destBind, options.destPass)

    #Find the source object where to copy the attributes from
    try:
        srcData = pagedSearch(source, options.sBaseDN, options.sFilter, splitComma(options.sAttribs))
        if len(srcData) > 1:
            print("More than one source objects found, we require one unique source object\nrefine your search filter")
            sys.exit(2)
    except:
        print(sys.exc_info()[0])
        sys.exit(2)

    #Find the destination objects that will be encriched
    try:
        dstData = pagedSearch(dest, options.dBaseDN, options.dFilter, splitComma(options.dAttribs))
    except:
        print(sys.exc_info()[0])
        sys.exit(2)

    #Using six for Python2 compatability, getting just the attribute values
    sAttribs = six.next(six.itervalues(srcData))
    
    #loop through the dst objects and update if required
    for dn in dstData:
        ldif = ""    

        #we iterate through the attributes as an indexed array so that we can match the source and destination attributes by index, this allows us to
        #copy the source attribute value to a different destination attribute
        #Which means that options.sAttribs[0] will be copied to options.dAttribs[0], options.sAttribs[1] will be copied to options.dAttribs[1]... etc
        i = 0
        ldAttribs = splitComma(options.dAttribs)
        lsAttribs = splitComma(options.sAttribs)

        for sAttrib in lsAttribs:
            #if source attr doesn't exist in target attr then add it
            if not dn in dstData or not ldAttribs[i] in dstData[dn]: 
                ldif += "add: %s\n%s: %s\n-\n" % (ldAttribs[i], ldAttribs[i], sAttribs[sAttrib][0])
                if not options.simMode:
                    dest.modify_s(dn, [(ldap.MOD_ADD, ldAttribs[i], sAttribs[sAttrib][0])] )

            #if source attr exists in target attr and replace is true, then update it otherwise do nothing 
            elif dstData[dn][ldAttribs[i]] != sAttribs[sAttrib] and options.replace:
                    
                ldif += "replace: %s\n%s: %s\n-\n" % (ldAttribs[i], ldAttribs[i], sAttribs[sAttrib][0])
                if not options.simMode:
                    dest.modify_s(dn, [(ldap.MOD_REPLACE, ldAttribs[i], sAttribs[sAttrib][0])])
            i+=1

        if len(ldif) > 0:
             print("dn: %s\nchangetype: modify\n%s" % (dn, ldif))
