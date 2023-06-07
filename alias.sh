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
