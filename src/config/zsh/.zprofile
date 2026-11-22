# /etc/zprofile (path_helper) reorders PATH after .zshenv, so re-add ours here.
[[ -x /opt/homebrew/bin/brew ]] && eval "$(/opt/homebrew/bin/brew shellenv)"
export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"
