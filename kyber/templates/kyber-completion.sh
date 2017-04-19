GREP_BIN=$(/usr/bin/which grep)
ORIGINAL_PS1=$PS1
_CURRENT_KUBE_CONTEXT_FILE=/tmp/kubectl-config-get-contexts.tmp

function __kube_check {
	kubectl > /dev/null 2>&1
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

function kubes {
	# a helper function to list kube contexts, which caches the output for 1 minute
	rm -f `find $_CURRENT_KUBE_CONTEXT_FILE -type file -mtime +0h1m 2>/dev/null`
	if [ ! -e $_CURRENT_KUBE_CONTEXT_FILE ]; then
		__list_kube_contexts > $_CURRENT_KUBE_CONTEXT_FILE
	fi
	cat $_CURRENT_KUBE_CONTEXT_FILE
}

# PS1 helpers
function __get_current_kube_context_namespace {
	kubes|$GREP_BIN '^*'|awk {'print $5'}
}

function __get_current_kube_context_cluster {
        kubes|$GREP_BIN '^*'|awk {'print $3'}
}

function __get_current_kube_context_auth {
	kubes|$GREP_BIN '^*'|awk {'print $4'}
}

function __get_current_kube_context_name {
	kubes|$GREP_BIN '^*'|awk {'print $2'}
}

function __list_kube_context_names {
	kubes|$GREP_BIN -v CURRENT|sed -e 's/^\*//'|awk {'print $1'}
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
	# XXX: REPLACE WITH `kb deploy_targets` or similar command which lists actual
	#      image tags from ECR
	if [ -d ".git" ]; then
		git log --format=oneline | awk {'print $1'} | head -10
	fi
}

function __list_kb_config_keys {
	cmdcache kb config list |cut -d= -f1
}

function __kb_status {
        CMDCACHE_MAX_AGE=30 cmdcache kb status --skip-ecr --skip-k8s
}

function __kyber_list_pods {
        project=$(__kb_status |$GREP_BIN Project:|cut -d: -f2|sed -e 's/ //')
        cmdcache kubectl get pods -l app=$project -o name|cut -d/ -f2
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

function __kyber_logs_compgen {
        local cur
        cur=${COMP_WORDS[COMP_CWORD]}
        if [[ "$cur" != "" ]]; then
                if [[ $cur == -* ]]; then
                        if [[ $cur == --s* ]]; then
                                COMPREPLY=( --skip-seconds )
                        elif [[ $cur == --k* ]]; then
                                COMPREPLY=( --keep-timestamps )
                        else
                                COMPREPLY=(--skip-seconds --keep-timestamps)
                        fi
                else
                        COMPREPLY=( $( __list_kb_pods |$GREP_BIN "^$cur" ) )
                fi
        else
                COMPREPLY=( $( __list_kb_pods ) )
        fi
}

function __kyber_config_compgen {
	local cur prev
        cur=${COMP_WORDS[COMP_CWORD]}
	prev=${COMP_WORDS[COMP_CWORD-1]}
	CMDS=$_KYBER_CONFIG_CMDS
	if [[ $prev == "config" ]]; then
		COMPREPLY=( $( echo $CMDS ) )
		if [ "$cur" != "" ]; then
			COMPREPLY=( $( echo "$CMDS"|$GREP_BIN "^$cur" ) )
		fi
	elif [[ $prev == "get" || $prev == "set" ]]; then
		COMPREPLY=( $( __list_kb_config_keys ) )
		if [ "$cur" != "" ]; then
			COMPREPLY=( $( __list_kb_config_keys|$GREP_BIN "^$cur" ) )
		fi
	fi
}

_KYBER_CMDS=$'{%- for cmd in kyber_commands %}{{cmd}}\n{% endfor %}'
_KYBER_CONFIG_CMDS=$'{%- for cmd in kyber_config_commands %}{{cmd}}\n{% endfor %}'

function __kyber_compgen {
	local cur prev
        cur=${COMP_WORDS[COMP_CWORD]}
	prev=${COMP_WORDS[COMP_CWORD-1]}
	pprev=${COMP_WORDS[COMP_CWORD-2]}
	CMDS=$_KYBER_CMDS

	if [[ $prev == "kb" ]]; then
		COMPREPLY=( $( echo $CMDS ) )
		if [[ $cur != "" ]]; then
			COMPREPLY=( $(echo "$CMDS"|$GREP_BIN "^$cur" ) )
		fi
	elif [[ $prev == "deploy" ]]; then
		__kyber_deploy_compgen
        elif [[ $prev == "logs" ]]; then
                __kyber_logs_compgen
	elif [[ $prev == "config" || $pprev == "config" ]]; then
		__kyber_config_compgen
	fi
}

complete -F _kb_completion -o default kb;

function kuse {
	__kube_guard
	unkubify
	/bin/rm -f $_CURRENT_KUBE_CONTEXT_FILE
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
	local __kube_cluster='`__get_current_kube_context_cluster`'
	local __kube_auth='`__get_current_kube_context_auth`'
	local __kube_namespace='`__get_current_kube_context_namespace`'
	local __kube_context='`__get_current_kube_context_name`'
	local __prompt="(kb: $__kube_context"
	if [ "$__kube_namespace" != "" ]; then
		__prompt="$__prompt [$__kube_namespace]"
	fi
	export PS1="$__prompt) $ORIGINAL_PS1"
}

function unkubify {
	export PS1=$ORIGINAL_PS1
}
kubify
