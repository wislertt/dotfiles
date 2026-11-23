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

# launchctl: GUI apps launched from Spotlight or the Dock inherit this PATH.
command -v launchctl >/dev/null && launchctl setenv PATH "$PATH" 2>/dev/null

# mise: activate managed tool versions
eval "$(mise activate zsh)"

# git-credential-manager: no default store on Linux (macOS uses the Keychain)
[[ $OSTYPE == linux* ]] && export GCM_CREDENTIAL_STORE=secretservice

# gh: expose the GitHub CLI login as GITHUB_TOKEN
export GITHUB_TOKEN="$(gh auth token 2>/dev/null)"

##### Per-project: depends on the directory the shell starts in #####

# python: activate the project venv
[ -f .venv/bin/activate ] && source .venv/bin/activate

# rust: run freshly built binaries by name
[ -d target/debug ] && export PATH="./target/debug:$PATH"
[ -d target/release ] && export PATH="./target/release:$PATH"
