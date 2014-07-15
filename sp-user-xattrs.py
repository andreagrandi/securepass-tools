#!/usr/bin/python
##
## SecurePass CLI tools utilities
## Extended attributes operations
##
## (c) 2013 Giuseppe Paterno' (gpaterno@gpaterno.com)
##          GARL Sagl (www.garl.ch)
##


import utils
import securepass
import logging
from optparse import OptionParser


parser = OptionParser(usage="""Operate on users' extended attributes in SecurePass

%prog [options] userid [list|set|get] """)


parser.add_option('-D', '--debug',
                  action='store_true', dest="debug_flag",
	              help="Enable debug output",)

opts, args = parser.parse_args()


## Set debug
FORMAT = '%(asctime)-15s %(levelname)s: %(message)s'
if opts.debug_flag:
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
else:
    logging.basicConfig(format=FORMAT, level=logging.INFO)


## Load config
config =  utils.loadConfig()

## Config the handler
sp_handler = securepass.SecurePass(app_id=config['app_id'],
                                   app_secret=config['app_secret'],
                                   endpoint=config['endpoint'])

## Check username
try:
    if args[0].strip() == "":
        print "Missing username. Try with --help"
        exit(1)

except IndexError:
    print "Missing username. Try with --help"
    exit(1)

## Check operation
try:
    if args[1].strip().lower() != "list" and \
       args[1].strip().lower() != "get" and  \
       args[1].strip().lower() != "set":
            print "Operation not valid. Try with --help"
            exit(1)

except IndexError:
    print "Operations not specifed. Try with --help"
    exit(1)



## If list operation specified
if args[1].strip().lower() == "list":

    ## Display info
    try:
        attributes = sp_handler.users_xattr_list(user=args[0])

        print "Extended attributes details for %s" % args[0]
        print "================================================\n"

        for attribute in attributes:
            print "%s: %s" % (attribute, attributes[attribute])


    except Exception as e:
        print e
