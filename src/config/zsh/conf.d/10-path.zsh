typeset -U path PATH
path=(
    "$HOME/.local/bin"
    /opt/homebrew/opt/mysql-client/bin
    /opt/homebrew/bin
    /opt/homebrew/sbin
    $path
    "$HOME/.cargo/bin"
)
export PATH
