typeset -U path PATH
[[ $OSTYPE == darwin* ]] && brew_path=(/opt/homebrew/bin /opt/homebrew/sbin)
path=(
    "$HOME/.local/bin"
    $brew_path
    $path
    "$HOME/.cargo/bin"
)
unset brew_path
export PATH
