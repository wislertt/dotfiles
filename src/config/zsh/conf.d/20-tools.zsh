##### Global: same in every shell #####

# starship: prompt
eval "$(starship init zsh)"

# gcloud: add the SDK to PATH and enable tab completion
if [ -f /opt/homebrew/share/google-cloud-sdk/path.zsh.inc ]; then
    . /opt/homebrew/share/google-cloud-sdk/path.zsh.inc
    . /opt/homebrew/share/google-cloud-sdk/completion.zsh.inc
fi

# kiro: shell integration, only inside Kiro's terminal
[[ "$TERM_PROGRAM" == "kiro" ]] && . "$(kiro --locate-shell-integration-path zsh)"

# zsh completion: load ~/.zfunc completions and use a selectable menu
fpath+=~/.zfunc
autoload -Uz compinit
compinit
zstyle ':completion:*' menu select

# launchctl: GUI apps inherit this PATH; built from a clean login shell, not this one, so an inherited entry cannot cycle back.
[[ $OSTYPE == darwin* ]] && (( $+commands[launchctl] )) && {
    () {
        local -aU dirs=(${^${(s.:.)"$(env -i HOME=$HOME USER=$USER LOGNAME=$LOGNAME SHELL=/bin/zsh PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/zsh -lc 'print -r -- $PATH')"}}(N-/))
        (( $#dirs )) && launchctl setenv PATH "${(j.:.)dirs}"
    } &>/dev/null &!
}

# mise: activate managed tool versions
eval "$(mise activate zsh)"

# git-credential-manager: no default store on Linux (macOS uses the Keychain)
[[ $OSTYPE == linux* ]] && export GCM_CREDENTIAL_STORE=secretservice

# gh: expose the GitHub CLI login as GITHUB_TOKEN
export GITHUB_TOKEN="$(gh auth token 2>/dev/null)"

# gpg: warn before the commit signing key expires, since git then refuses to commit; Update renews it
() {
    local key expires days
    key=$(git config --get user.signingkey 2>/dev/null) || return 0
    expires=$(gpg --list-keys --with-colons "$key" 2>/dev/null | awk -F: '$1 == "pub" { print $7; exit }')
    [[ -n $expires ]] || return 0
    zmodload -F zsh/datetime p:EPOCHSECONDS
    days=$(( (expires - EPOCHSECONDS) / 86400 ))
    if (( expires <= EPOCHSECONDS )); then
        print -u2 "GPG signing key expired; commits fail until you run: bake update"
    elif (( days < 7 )); then
        print -u2 "GPG signing key expires in $days days; run: bake update"
    fi
}

##### Per-project: depends on the directory the shell starts in #####

# python: activate the project venv
[ -f .venv/bin/activate ] && source .venv/bin/activate

# rust: run freshly built binaries by name
[ -d target/debug ] && export PATH="./target/debug:$PATH"
[ -d target/release ] && export PATH="./target/release:$PATH"
