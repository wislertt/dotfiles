# The only zsh file in ~. Everything else lives in $ZDOTDIR.
export XDG_CONFIG_HOME="$HOME/.config"
export ZDOTDIR="$XDG_CONFIG_HOME/zsh"

# Read by every zsh, including non-interactive scripts.
[ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
