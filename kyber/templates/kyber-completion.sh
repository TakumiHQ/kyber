GREP_BIN=$(/usr/bin/which grep)
ORIGINAL_PS1=$PS1

function __kube_check {
	kubectl 2>&1>/dev/null
	return $?
}

function __kube_guard {
	__kube_check
	if [ "$?" != "0" ]; then
		exit 1;
	fi
}

function __list_kube_contexts {
	kubectl config get-contexts
}
alias kubes=__list_kube_contexts

function __list_kube_context_names {
	__list_kube_contexts|$GREP_BIN -v CURRENT|sed -e 's/^\*//'|awk {'print $1'}
}

function __kube_context_compgen {
	local cur
	cur=${COMP_WORDS[COMP_CWORD]}
	if [ "$cur" != "" ]; then
		COMPREPLY=( $( __list_kube_context_names|$GREP_BIN "^$cur" ) )
	else
		COMPREPLY=( $( __list_kube_context_names ) )
	fi
}

function __list_kb_deploy_targets {
	if [ -d ".git" ]; then
		git log --format=oneline | awk {'print $1'} | head -10
	fi
}


function __kyber_deploy_compgen {
	local cur
        cur=${COMP_WORDS[COMP_CWORD]}
	if [ "$cur" != "" ]; then
		COMPREPLY=( $( __list_kb_deploy_targets|$GREP_BIN "^$cur" ) )
	else
		COMPREPLY=( $( __list_kb_deploy_targets ) )
	fi
}

_KYBER_CMDS=$'{%- for cmd in kyber_commands %}{{cmd}}\n{% endfor %}'

function __kyber_compgen {
	local cur prev
        cur=${COMP_WORDS[COMP_CWORD]}
	prev=${COMP_WORDS[COMP_CWORD-1]}
	CMDS=$_KYBER_CMDS

	if [[ $prev == "kb" ]]; then
		COMPREPLY=( $( echo $CMDS ) )
		if [[ $cur != "" ]]; then
			COMPREPLY=( $(echo "$CMDS"|$GREP_BIN "^$cur" ) )
		fi
	elif [[ $prev == "deploy" ]]; then
		__kyber_deploy_compgen
	fi
}

complete -F _kb_completion -o default kb;

function kuse {
	__kube_guard
	kubectl config use-context $1
	kubify
}
complete -o nospace -F __kube_context_compgen kuse
complete -o nosort -F __kyber_compgen kb

function kubify {
	__kube_check
	if [ "$?" != "0" ]; then
		echo "can't access kubectl, is your PATH ok?"
	fi
	local __kube_cluster="`__list_kube_contexts |$GREP_BIN '^*'|awk {'print $3'}`"
	local __kube_auth="`__list_kube_contexts |$GREP_BIN '^*'|awk {'print $4'}`"
	local __kube_namespace="`__list_kube_contexts |$GREP_BIN '^*'|awk {'print $5'}`"
	local __kube_context='`kubectl config current-context`'
	local __prompt="(kb: $__kube_context"
	if [ "$__kube_namespace" != "" ]; then
		__prompt="$__prompt [$__kube_namespace]"
	fi
	export PS1="$__prompt) $ORIGINAL_PS1"
}
kubify
