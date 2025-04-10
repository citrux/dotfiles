#!/bin/sh


function set_theme() {
  case $1 in
    "dark")
      gsettings set org.gnome.desktop.interface color-scheme prefer-dark
      gsettings set org.gnome.desktop.interface gtk-theme adw-gtk3-dark
      kitty +kitten themes --reload-in=all Catppuccin-Macchiato
      sed -i 's/\(theme = "\)\w\+\("\)/\1catppuccin_macchiato\2/' $XDG_CONFIG_HOME/helix/config.toml && pkill -USR1 helix 
      ;;
    "light")
      gsettings set org.gnome.desktop.interface color-scheme default
      gsettings set org.gnome.desktop.interface gtk-theme adw-gtk3
      kitty +kitten themes --reload-in=all Catppuccin-Latte
      sed -i 's/\(theme = "\)\w\+\("\)/\1catppuccin_latte\2/' $XDG_CONFIG_HOME/helix/config.toml && pkill -USR1 helix 
      ;;
    *)
      echo "Unknown theme"
      exit 1
      ;;
  esac
}


if [ -z $1 ]; then
  while true; do
    currenttime=$(date +%H:%M)
    theme="dark"
    if [[ $currenttime > "04:00" ]] && [[ $currenttime < "18:00" ]]; then
      theme="light"
    fi
    currenttheme=""
    if [[ -f "$XDG_RUNTIME_DIR/theme" ]]; then
      currenttheme=$(<"$XDG_RUNTIME_DIR/theme")
    fi
    if [[ $currenttheme != $theme ]]; then
      set_theme $theme
      echo $theme > $XDG_RUNTIME_DIR/theme
    fi
    sleep 60
  done
else
  set_theme $1
  exit 0
fi

