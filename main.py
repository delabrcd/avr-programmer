import tkinter
import customtkinter
import subprocess
import serial.tools.list_ports
import logging
import threading

from time import sleep
from os import name as OSNAME

from typing import Union, Tuple, Optional, Callable
from pathlib import Path
from PIL import Image

from tooltip import CreateToolTip

APPLICATION_NAME = "AVR Programmer"
AUTHOR = "Caleb DeLaBruere"

DEFAULT_PADDING = 5

SUPPORTED_DEVICES = {'atmega32u4': ('avr109', '115200')}

CWD = Path().resolve()


class ProgressDialog(customtkinter.CTkToplevel):
    def update_text_task(self, process: subprocess.Popen):
        while True:
            if not self.programmer_run:
                process.kill()
            out = process.stderr.readline()
            if out == b'' and process.poll() is not None:
                break
            logging.info(str(out))
            self.text.insert(customtkinter.END, out)
            self.text.see(customtkinter.END)
        try:
            self.wm_title(APPLICATION_NAME + ': Programming Finished')
        except:
            pass

    def cancel_programming(self):
        self.programmer_run = False

    def __init__(self, parent: any, *args, fg_color: Optional[Union[str, Tuple[str, str]]] = None, **kwargs):
        super().__init__(parent, *args, fg_color=fg_color, **kwargs)
        self.programmer_run = True
        self.var = customtkinter.StringVar()
        self.wm_title(APPLICATION_NAME + ': Programming in Progress...')

        self.text = customtkinter.CTkTextbox(self)
        x, y, cx, cy = parent.bbox("insert")
        x += parent.winfo_rootx() + 25
        y += parent.winfo_rooty() + 20
        self.wm_geometry("600x400+%d+%d" % (x, y))
        self.cancel_button = customtkinter.CTkButton(
            self, text="Cancel", command=self.cancel_programming)

        self.text.pack(side=customtkinter.TOP,
                       fill=customtkinter.BOTH, expand=True)
        self.cancel_button.pack(side=customtkinter.BOTTOM,
                                padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

    def show(self, process: subprocess.Popen):
        logging.info("the commandline is {}".format(process.args))
        self.grab_set()
        t = threading.Thread(target=self.update_text_task,
                             args=[process], daemon=True)
        t.start()
        self.wait_window()
        if process.poll() is None:
            logging.info(
                "Window Closed before programming was finished, terminating")
            process.kill()
        return


class FileSelection(customtkinter.CTkFrame):
    def choose_file(self):
        name = Path(customtkinter.filedialog.askopenfilename(
            filetypes=[("Hex Files", "*.hex")]))
        if not name.is_file():
            return

        self.selection.set(name)
        if self.command is not None:
            self.command(name)

    def __init__(self, master: any, label: str = "Default:", selection: customtkinter.Variable = None, command: Union[Callable[[str], None], None] = None, width: int = 200, height: int = 200, corner_radius: Optional[Union[int, str]] = None, border_width: Optional[Union[int, str]] = None, bg_color: Union[str, Tuple[str, str]] = "transparent", fg_color: Optional[Union[str, Tuple[str, str]]] = None, border_color: Optional[Union[str, Tuple[str, str]]] = None, background_corner_colors: Union[Tuple[Union[str, Tuple[str, str]]], None] = None, overwrite_preferred_drawing_method: Union[str, None] = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color,
                         border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)
        self.command = command
        self.selection = selection
        customtkinter.CTkLabel(
            self, text=label, justify=customtkinter.LEFT).grid(row=0, column=0,
                                                               padx=DEFAULT_PADDING, pady=DEFAULT_PADDING, sticky=customtkinter.W)
        self.file_select_entry = customtkinter.CTkEntry(
            self, textvariable=selection)
        self.file_select_entry.grid(row=1, column=0,
                                    sticky='ew', padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        edit_image = customtkinter.CTkImage(
            dark_image=Image.open(Path(str(CWD) + "/edit_icon_dark.png")), light_image=Image.open(Path(str(CWD) + "/edit_icon_dark.png")))
        file_select_button = customtkinter.CTkButton(
            self, image=edit_image, text=None, command=self.choose_file)
        file_select_button.grid(
            row=1, column=1, sticky='ew', padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)
        self.file_select_entry.configure(state=customtkinter.DISABLED)
        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=1)


class LabeledDropDown(customtkinter.CTkFrame):
    def __init__(self, master: any, text: str = "None", variable: customtkinter.Variable = None, values: list = None, command: Union[Callable[[str], None], None] = None, width: int = 200, height: int = 200, corner_radius: Optional[Union[int, str]] = None, border_width: Optional[Union[int, str]] = None, bg_color: Union[str, Tuple[str, str]] = "transparent", fg_color: Optional[Union[str, Tuple[str, str]]] = None, border_color: Optional[Union[str, Tuple[str, str]]] = None, background_corner_colors: Union[Tuple[Union[str, Tuple[str, str]]], None] = None, overwrite_preferred_drawing_method: Union[str, None] = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color,
                         border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)
        self.label = customtkinter.CTkLabel(
            self, text=text, anchor=customtkinter.W, justify=customtkinter.LEFT)
        self.label.grid(row=0, column=0, sticky=customtkinter.W,
                        padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        self.dropdown = customtkinter.CTkOptionMenu(
            self, variable=variable, command=command, values=values)
        self.dropdown.grid(row=1, column=0, sticky=customtkinter.E +
                           customtkinter.W, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)
        self.grid_columnconfigure(0, weight=1)


class MainFrame(customtkinter.CTkFrame):
    # daemon thread, won't keep application running on exit
    def port_watcher(self):
        while True:
            newports = [
                port.device for port in serial.tools.list_ports.comports()]
            self.portmutex.acquire()
            if self.ports != newports:
                logging.info("serial devices changed")
                new_device = list(set(newports) - set(self.ports))
                self.ports = newports
                self.portmutex.release()
                if len(new_device) == 1:
                    logging.info("New Device: " + new_device[0])
                    if self.auto_flash.get():
                        self.selected_serial_device.set(
                            new_device[0])
                        if self.eval_flash():
                            self.flash_device()

                if self.selected_serial_device.get() not in self.ports:
                    self.selected_serial_device.set("None")
                    self.eval_flash()

                self.serial_device_dropdown.dropdown.configure(
                    values=self.ports)
            else:
                self.portmutex.release()
            sleep(1)

    def eval_flash(self, current_value=None):
        self.portmutex.acquire()
        for item in self.check_list:
            if item[0].get() == item[1]:
                self.flash_button.configure(state=customtkinter.DISABLED)
                self.portmutex.release()
                return False
        self.portmutex.release()
        self.flash_button.configure(state=customtkinter.NORMAL)
        return True

    def flash_device(self):
        self.portmutex.acquire()
        command_name = []
        if OSNAME == 'nt':
            command_name = [str(Path(str(CWD) + '/avrdude/avrdude')),
                            '-C' + str(Path(str(CWD) + '/avrdude/avrdude.conf'))]
        elif OSNAME == 'posix':
            command_name = ['avrdude']
        else:
            logging.error(
                "Unrecognized System Platform. Supported platforms: linux, windows")
            return

        cmd_args = ['-p' + self.device_type.get(), '-c' + SUPPORTED_DEVICES[self.device_type.get()][0],
                    '-P' + self.selected_serial_device.get(), '-b' + SUPPORTED_DEVICES[self.device_type.get()][1], '-D', '-Uflash:w:' + self.selected_file.get()+':a']

        cmd = command_name + cmd_args
        logging.info(str(cmd))

        ProgressDialog(self).show(subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE))
        self.portmutex.release()

    def __init__(self, master: any, width: int = 200, height: int = 200, corner_radius: Optional[Union[int, str]] = None, border_width: Optional[Union[int, str]] = None, bg_color: Union[str, Tuple[str, str]] = "transparent", fg_color: Optional[Union[str, Tuple[str, str]]] = None, border_color: Optional[Union[str, Tuple[str, str]]] = None, background_corner_colors: Union[Tuple[Union[str, Tuple[str, str]]], None] = None, overwrite_preferred_drawing_method: Union[str, None] = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color,
                         border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)
        self.ports = [
            port.device for port in serial.tools.list_ports.comports()]
        self.portmutex = threading.Lock()
        self.portmutex.acquire()
        self.check_list = []

        self.device_type = tkinter.StringVar()
        self.device_type.set("None")
        self.check_list.append((self.device_type, "None"))
        device_dropdown = LabeledDropDown(
            self, text="Type:", variable=self.device_type, command=self.eval_flash, values=[key for key, value in SUPPORTED_DEVICES.items()])
        device_dropdown.pack(side="top", fill=customtkinter.X,
                             padx=DEFAULT_PADDING, pady=DEFAULT_PADDING, expand=True)

        self.selected_serial_device = tkinter.StringVar()
        self.selected_serial_device.set("None")
        self.check_list.append((self.selected_serial_device, "None"))
        self.serial_device_dropdown = LabeledDropDown(
            self, text="Port:", variable=self.selected_serial_device, command=self.eval_flash, values=self.ports)
        self.serial_device_dropdown.pack(side="top", fill=customtkinter.X,
                                         padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)
        self.port_watcher_thread = threading.Thread(
            target=self.port_watcher, daemon=True)
        self.port_watcher_thread.start()

        self.selected_file = customtkinter.StringVar()
        self.selected_file.set("None")
        self.check_list.append((self.selected_file, "None"))
        file_select_frame = FileSelection(
            self, selection=self.selected_file, label="File:", command=self.eval_flash)
        file_select_frame.pack(side="top", fill=customtkinter.X,
                               padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        self.flash_button = customtkinter.CTkButton(
            self, text="Flash Device!", command=self.flash_device)
        self.flash_button.pack(side="bottom", fill=customtkinter.X,
                               padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)
        self.flash_button.configure(state='disabled')

        self.auto_flash = customtkinter.BooleanVar()
        self.auto_flash_switch = customtkinter.CTkSwitch(
            self, text="Auto Flash", variable=self.auto_flash)
        self.auto_flash_switch.pack(side="bottom", fill=customtkinter.X,
                                    padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)
        CreateToolTip(
            self.auto_flash_switch, 'Enable "Auto Flash" mode, which will attempt to use your currently selected settings to flash any new serial device that is hotplugged. This is useful for flashing Leonardo\'s with the LUFA bootloader.')
        self.portmutex.release()


class MainWindow(customtkinter.CTk):
    def __init__(self, fg_color: Optional[Union[str, Tuple[str, str]]] = None, **kwargs):
        super().__init__(fg_color, **kwargs)
        customtkinter.set_appearance_mode("dark")
        self.wm_title(APPLICATION_NAME)
        # self.geometry('400x600')
        main_frame = MainFrame(self)
        main_frame.pack(fill=customtkinter.BOTH, expand=True)


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")
    logging.info("Starting " + APPLICATION_NAME)
    logging.info("Platform: " + OSNAME)
    if OSNAME == 'nt':
        pass
    elif OSNAME == 'posix':
        pass
    else:
        logging.error(
            "Unrecognized System Platform. Supported platforms: linux, windows")
        exit(1)
    root = MainWindow()
    root.mainloop()
