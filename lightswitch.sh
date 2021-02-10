#!/bin/bash

# simple function from my .bashrc
# controls screen gamma to effectively tweak brightness and contrast

# written for my specific device. you may need to change:
#     - the actual --brightness values. these happen to work well for my awful teenage dell
#     - the --output device or devices. simply running "xrandr" in your terminal should list your options
# written for bash, will test in some other shells eventually and try to make it universal

lightswitch ()
{
        CONTRAST=`stdbuf -o0 xrandr --verbose | awk '/Brightness/ { print $2; exit }'`
        if [ $(echo "$CONTRAST > 0.85"|bc -l) -eq 1 ]; then
                xrandr --output "LVDS-1" --brightness "0.75"
        else
                xrandr --output "LVDS-1" --brightness "0.95"
        fi
}
