# AVR-programmer
A python wrapper & UI built around avrdude. To facilitate programming for [openrb](https://github.com/delabrcd/openrb-instruments)
If you want the most straightforward experience, go ahead and download the prebuilt executable for [avr-programmer](https://github.com/delabrcd/avr-programmer/releases).  This is a quick UI I built in python to directly facilitate flashing for this project, for windows it bundles its own copy of avrdude to handle the flashing, but it is cross platform with the caveat that you need to have avrdude installed and in your path for it to work.  

Steps: 
1. Download the latest release of [avr-programmer](https://github.com/delabrcd/avr-programmer/releases)
2. Download the latest release of [openrb](https://github.com/delabrcd/openrb-instruments/releases)
3. Leave your arduino unplugged
4. Run `avr-programmer.exe`
5. Select "Type" -> atmega32u4 (this is currently the *only* type)
6. Leave "Port" empty (this will auto-detect when you plug your arduino in)
7. Select the firmware file you downloaded earlier
8. Enable "Auto Flash". Here's an example for final settings: 

    ![alt text](https://github.com/delabrcd/rockband-drums-usb/blob/master/docs/avr-programmer-general-settings.png?raw=true)

9.  Plug your Arduino in and wait ~10s. The Leonardo may require you to press the reset button before it flashes, if nothing happens within 10s of plugging in, try pressing the physical reset button on the arduino. A successful flash will look something like this: 
    
    ![alt text](https://github.com/delabrcd/rockband-drums-usb/blob/master/docs/avr-programmer-successful-flash.png?raw=true)

10. Close avr-programmer and unplug your arduino, you're ready to go! Any firmware updates in the future will be done with this method
