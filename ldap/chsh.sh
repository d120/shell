#! /bin/bash

# functions used
array_contains () { 
    local array="$1[@]"
    local seeking=$2
    local in=1
    for element in "${!array}"; do
        if [[ $element == $seeking ]]; then
            in=0
            break
        fi
    done
    return $in
}


# read valid shells from /etc/shells
# ignore lines starting with # and empty lines
shells=()
while read -r line; do
	[[ "$line" =~ ^#.*$ ]] && continue
	[[ "$line" =~ ^[[:space:]]*$ ]] && continue
	shells+=("$line")
done < /etc/shells

# more than 1 argument? print usage!
if [ "$#" -gt 1 ]; then
	echo "Usage: $0 [/path/to/shell]"
	exit 1
fi

if [ "$#" -eq 1 ]; then
	# user supplied a shell on the commandline
	input=$1
else
	# no shell supplied, show dialog with available shells
	items=""
	for i in "${!shells[@]}"; do
		items="$items $i ${shells[$i]}"
	done

	# use tempfile for output as exit code is used to indicate whether "cancel" was pressed
	tempfile=$(mktemp)
	trap "rm $tempfile; exit" SIGHUP SIGINT SIGTERM
	dialog --menu "Please choose a shell" 0 0 4 $items 2>$tempfile

	if [ "$?" -ne "0" ]; then
		# user pressed cancel
		exit 2
	fi

	# read input from tempfile and delete it afterwards
	input=${shells[$(<$tempfile)]}
	rm -f $tempfile
fi

# check if selected shell is available and modify ldap settings. asks user for password.
if array_contains shells $input; then
	DN="uid=`whoami`,ou=People,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de"

	ldapmodify -v -P3 -H ldaps://ldap.d120.de -W -D $DN <<- EOM
		dn: $DN
		changetype: modify
		replace: loginShell
		loginShell: $input
		-
		EOM
else
	echo "Please choose a valid shell!"
fi
