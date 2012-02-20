#!/usr/local/bin/python
import cgi, commands, sys, urllib, urllib2

theurl = 'http://power1/'
posturl = 'http://power1/rack.html'

username = 'planetlab'
password = 'planetlab'

# Set up HTTP access
passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
# this creates a password manager
passman.add_password(None, theurl, username, password)
# because we have put None at the start it will always use 
# this username/password combination
authhandler = urllib2.HTTPBasicAuthHandler(passman)
opener = urllib2.build_opener(authhandler)
# you can use the opener directly to open URLs
# *or* you can install it as the default opener so that all calls to
# urllib2.urlopen use this opener
urllib2.install_opener(opener)

exitButton = "no"
formStorage = cgi.FieldStorage()
if (len(formStorage) != 0):
    for x in formStorage:
        port = str(x)
        action = str(formStorage[x].value)

    if action=="0":
	data = {port:'0'}
    elif action=="1":
	data = {port:'1'}
    elif action=="r":
	data = {port:'r'}
    # user hit the exit button
    else:
        exitButton = "yes"

    if (exitButton == "no"):
        f = opener.open(posturl, data=urllib.urlencode(data))

print "Content-type: text/html\n\n"
print '<html>'
print '<head>'

print '<style type="text/css">'
print 'BODY{background-color:black;}.MTab{cursor:default;}.MCell{font-weight:bold;font-size:9pt;font-family:Arial,Helvetica,sans-serif;color:White;background-color:#999999;}.MCellOver{font-weight:bold;font-size:10pt;font-family:Arial,Helvetica,sans-serif;color:White;background-color:#b1a9ab;}.White{font-weight:bold;font-size:16pt;font-family:"Arial Rounded MT Bold",Arial,Helvetica,sans-serif;color:White;}.GuardWhite{font-weight:bold;font-size:24pt;font-family:"Arial Rounded MT Bold",Arial,Helvetica,sans-serif;color:White;font-style:italic;background-color:Black;}.Red{font-weight:bold;font-size:24pt;font-family:"Arial Rounded MT Bold",Arial,Helvetica,sans-serif;color:Red;}.bar{border-width:2px;border-style:solid none none none;border-color:Red;}.button{background-color:#a7a7a7;border-width:1px;border-color:#a7a7a7;color:Black;font-weight:normal;font-size:10pt;font-family:Arial,Helvetica,sans-serif;}.Text{font-family:Arial,Helvetica,sans-serif;font-size:24px;color:White;}.Device{font-family:Arial,Helvetica,sans-serif;font-size:24px;color:White;text-align:right;}.Rack{font-family:Arial,Helvetica,sans-serif;font-size:18px;color:White;text-align:center;}.ON{font-family:Arial,Helvetica,sans-serif;font-size:18px;color:Lime;}.OFF{font-family:Arial,Helvetica,sans-serif;font-size:18px;color:#ABABAD;}.RST{font-family:Arial,Helvetica,sans-serif;font-size:18px;color:#FFFF00;}.ION{font-family:Arial,Helvetica,sans-serif;font-size:18px;font-style:italic;color:Lime;}.IOFF{font-family:Arial,Helvetica,sans-serif;font-size:18px;font-style:italic;color:#ABABAD;}.IRST{font-family:Arial,Helvetica,sans-serif;font-size:18px;font-style:italic;color:#FFFF00;}.Warning{font-family:Arial,Helvetica,sans-serif;font-size:18px;color:Yellow;}.Associat{font-family:Arial,Helvetica,sans-serif;font-size:18px;color:White;}.Link{font-family:Arial,Helvetica,sans-serif;font-size:24px;color:White;}.DomTitle{font-weight:bold;font-size:14pt;font-family:Arial,Helvetica,sans-serif;color:White;}'

print '</style>'
print '</head>'
print '<body>'
print '<table width=550 border=0 cellspacing=0 cellpadding=0><tr><td>'
print '<img src=../../images/logo.gif width=256 height=46></td>'
print '<td class=White align=center>Power&nbsp;Switch<br>Master&nbsp;Twin&nbsp;8-Port</td></tr> </table>'

if (exitButton == "yes"):
    print '<h3><font color="white">Logged out</font></h3>'
    print '</body>'
    print '</html>'
    sys.exit(1)
    
print '<script>'
print '_T_="<table width=\'550\' border=\'0\' cellspacing=\'1\' cellpadding=\'0\'>";'
print '_t_="</td></tr></table>";'
print '_L_="<tr><td><hr class=\'bar\'></td></tr>";'
print '_M_=_T_+"<tr><td height=\'160\' valign=\'middle\' align=\'center\' class=\'Text\'>";'
print 'function w(s){window.document.write(s);}'
print 'function l(){w(_T_+_L_+_t_);}'
print 'function f(v,n,a,g,z){s="<form action=\'"+document.URL+"\' method=\'post\'";if(g)s+=" target=\'_top\'";s+=">";if(z)s+="<td width=\'"+z+"\'>";s+="<input type=\'submit\' value=\'"+v+"\' class=\'button\'><input type=\'hidden\' name=\'"+n+"\' value=\'"+a+"\'>";if(z)s+="</td>";s+="</form>";return(s);}'
print 'function rack(r,n,m){w(_T_+"<tr><td class=\'DomTitle\' align=\'left\'>"+r+"</td><td class=\'Device\' align=\'right\'>"+n+_t_);l();w(_T_+"<tr><td class=\'Device\' align=\'right\'>"+m+_t_);}'
print 'function exit(){l();w(_T_+"<tr align=\'right\'><td>"+f("   Exit   ","X","X",1,0)+_t_);}'
print 'function trim(str){re=/(^\s*)|(\s*$)/g;return str.replace(re,"");}'
print 'function socket(cmd,name,state,pf){if(state==1){c="ON";a=0;}else if(state==2){c="RST";a=1;}else{c="OFF";a=1;}if(pf){cl=c;}else{cl="I"+c;}w(_T_+"<tr height=40 valign=top><td width=40 class="+cl+">"+c+"</td>"+f(" Power ","P"+cmd,a,0,60)+f("Restart","P"+cmd,"r",0,60)+"<td align=right class="+cl+">&nbsp;"+name+_t_);}'
print 'function warning(pf,i){if(~pf&i){if(i==1)m="A";else m="B";w(_T_+"<tr align=\'left\' valign=\'middle\' height=\'40\'><td width=\'40\'><img src=\'../../images/warning.jpg\'></td><td class=\'Warning\'>Warning! no power on section "+m+_t_+"<br>");}}'
print 'function display(name1,state1,name2,state2,name3,state3,name4,state4,name5,state5,name6,state6,name7,state7,name8,state8,index,pf,valid,option,mail){if(option&1){if(pf&4){if(option&2){w(_T_+"<tr align=\'left\' valign=\'middle\' height=\'40\'><td width=\'40\'><img src=\'../../images/associat.jpg\'></td><td class=\'Associat\'>Twin Mode Activated"+_t_+"<br>");warning(pf,1);warning(pf,2);for(var i=0;i<4;i++){if(valid & (1<<i)){socket(index+i,arguments[2*i],arguments[1+2*i],pf&(1<<(i/4)));}}for(var i=4;i<8;i++){if((valid&(1<<i))&&!(valid&(1<<(i-4)))){socket(index+i,arguments[2*i],arguments[1+2*i],pf&(1<<(i/4)));}}}else{for(var i=0;i<8;i++){if(i==0){if(valid&0x0f){warning(pf,1);}}if(i==4){w("<br>");if(valid&0xf0){warning(pf,2);}}if(valid&(1<<i)){socket(index+i,arguments[2*i],arguments[1+2*i],pf&(1<<(i/4)));}}}}else{mail=trim(mail);if(mail==""){w(_M_+"<p>Device not found</p>"+_t_);}else{w(_M_+"<p>Device not found, send an email to:</p><p><a class=\'Link\' href=\'mailto:"+mail+"\'>"+mail+"</a></p>"+_t_);}}}else{w(_M_+"<p>Device not activated</p>"+_t_);}}'

f2 = opener.open(posturl)
for x in f2:
    if (x.find("rack") != -1):
        print x

print '</script>'
print '</body>'
print '</html>'
