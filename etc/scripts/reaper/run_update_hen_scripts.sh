#!/bin/sh
PWD="/usr/local/hen/etc/scripts/reaper"
TEMP_OUTPUT="/tmp/update_hen_scripts_output"
TEMP_MAIL="/tmp/update_hen_scripts_mail"
UPDATE_SCRIPT="$PWD/update_hen_scripts.sh"
RECIPIENT="t.schooley@cs.ucl.ac.uk"

if [ -r $TEMP_OUTPUT ] ; then
	/bin/rm -f $TEMP_OUTPUT
fi
if [ -r $TEMP_MAIL ] ; then
	/bin/rm -f $TEMP_MAIL
fi

date=`/bin/date`
echo "" >> $TEMP_MAIL
echo "===== Update Summary =====" >> $TEMP_MAIL
echo "Date: $date" >> $TEMP_MAIL

result="failure"

$UPDATE_SCRIPT > $TEMP_OUTPUT
if [ "$?" -eq "0" ] ; then
	echo "Status: successful" >> $TEMP_MAIL
	result="success"
else
	echo "Status: failure" >> $TEMP_MAIL
fi

echo "Output: " >> $TEMP_MAIL
echo "" >> $TEMP_MAIL
/bin/cat $TEMP_OUTPUT >> $TEMP_MAIL	
/usr/bin/mail -s "[reaper] update_hen_scripts: $result" $RECIPIENT < $TEMP_MAIL	

exit 0
