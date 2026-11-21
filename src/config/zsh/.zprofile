# /etc/zprofile (path_helper) reorders PATH after .zshenv, so re-add ours here.
eval "$(/opt/homebrew/bin/brew shellenv)"
export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"
