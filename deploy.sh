#!/bin/bash
# Based on https://community.webfaction.com/questions/12718/installing-flask
# First, fill in these variables with your Application Name and URL Path:

APPNAME="duffel"
URLPATH="/"

# Step 2
# deploy the app
cd $HOME
mkdir -p $HOME/lib/python2.7
easy_install-2.7 flask
rm -r $HOME/webapps/$APPNAME/htdocs
mkdir $HOME/webapps/$APPNAME/$APPNAME
touch $HOME/webapps/$APPNAME/$APPNAME/__init__.py
touch $HOME/webapps/$APPNAME/$APPNAME/index.py
echo "import sys" > $HOME/webapps/$APPNAME/wsgi.py
echo "sys.path.insert(0, '$HOME/webapps/$APPNAME')" >> $HOME/webapps/$APPNAME/wsgi.py
echo -e "from $APPNAME import app as application\n" >> $HOME/webapps/$APPNAME/wsgi.py
sed -i "s^WSGILazyInitialization On^WSGILazyInitialization On\nWSGIScriptAlias / $HOME/webapps/$APPNAME/wsgi.py^" $HOME/webapps/$APPNAME/apache2/conf/httpd.conf
sed -i "s^AddHandler wsgi-script .py^AddHandler wsgi-script .py\n    RewriteEngine on\n    RewriteBase /\n    WSGIScriptReloading On^" $HOME/webapps/$APPNAME/apache2/conf/httpd.conf
sed -i "s/htdocs/$APPNAME/g" $HOME/webapps/$APPNAME/apache2/conf/httpd.conf


DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp $DIR/duffel.py $HOME/webapps/$APPNAME/$APPNAME/__init__.py

# Step 3
$HOME/webapps/$APPNAME/apache2/bin/restart
