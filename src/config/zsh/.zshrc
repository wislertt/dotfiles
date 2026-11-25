# Loader: public, private and group modules all link into conf.d/.
for _f in "$ZDOTDIR"/conf.d/*.zsh(N); do
    source "$_f"
done
unset _f

if [ -f "$HOME/.zshrc.local" ]; then
    source "$HOME/.zshrc.local"
fi
