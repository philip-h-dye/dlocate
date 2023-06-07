#------------------------------------------------------------------------------

function logit () {
    name="$1" ; shift
    dest=log/${name}/
    txt=${dest}/output.txt
    raw=${dest}/raw-output.dat
    mkdir -p ${dest} || exit -1
    ( "$@" 2>&1 ) | tee ${raw}
    status=$?
    raw-to-text < ${raw} > ${txt}
}

#------------------------------------------------------------------------------

function last_logit () {
    ( more log/"$1"/utmost.dat ; exit 1 )
}

function last_logts () {
    ( more log/"$1"/utmost.dat ; exit 1 )
}

#------------------------------------------------------------------------------

# alias inst='( clear && logts -b log/install invoke install && echo "install path = $( which-module ${module} )" )'

# alias inst='( clear && invoke install && echo "install path = $( which-module ${module} )" )'
function do_install_logit() {
    clear && \
	( logit log/install/overwrited invoke install || show_log ) && \
	echo "install path = $(which-module ${module})"
}

function do_install_logts() {
    clear && \
	( logts -b log/install invoke install || show_log ) && \
	echo "install path = $(which-module ${module})"
}

#------------------------------------------------------------------------------

module=$( echo $PWD | sed -e 's/^.*\///' )

alias c='( clear && logit log/clean/latest.txt invoke clean && clean "$@" )'

if [ -x ~/.local/bin/logts ] ; then
    alias b='( clear && logts -b log/build invoke build || last_log build )'
    alias t='( clear && logts -b log/test invoke test   || last_log test )'
    alias inst=do_install_logts
else
    
    alias b='( clear && logit build invoke build	|| last_log )'
    alias t='( clear && logit test  invoke test )'    
    alias inst=do_install_logit
fi

alias re='( c && b && t )'

alias pyhere=' PYTHONPATH=".:${PYTHONPATH}" python'

# function pyhere() { } -- perhaps to allow alternate commands, not necessary yet.

alias xt=' PYTHONPATH=".:${PYTHONPATH}" logts -b log/test pytest '

#
#

module=$( echo $PWD | sed -e 's/^.*\///' )

alias c='( clear && invoke clean )'

alias b='( clear && invoke build )'

alias t='( clear && ( invoke test 2>&1 ) | tee raw ; raw-to-text < raw > err )'

alias inst='( clear && invoke install && echo "install path = $( which-module ${module} )" )'

alias re='( c && b && t )'

#

if [ -e .custom ] ; then
  . .custom
fi

#
