import numpy as np
import shutil
import tifffile as tif
from PIL import Image, ImageTk
import tkinter as tk
import tkinter.ttk as ttk
import skimage.io
import pandas as pd
import pandastable as pt
import tkinter.filedialog
from tkinter.scrolledtext import ScrolledText
import os
import re

############ CONFIG ############
window_name = "ImgMax"
icon_path = "icon.ico"
bg_color ='#282729'
input_color = "#414042"
font_color = "white"

# Regex example which is used as default
test_regex = r"^(?P<Well>[A-Z] - [0-9]{2})\(fld (?P<Field>[0-9]{1,3}) wv (?P<Wavelength>[0-9]{1,4}) - (?P<Channel>.*) z (?P<Z>[0-9]{1,3})\).tif"

def get_meta_table(path, regex):
    groups = re.findall(r'\<.*?\>', regex)
    for chr in ["<", ">"]:
       groups = [i.replace(chr, "") for i in groups]
    
    image_list = os.listdir(path)  
    df = pd.DataFrame([], columns=groups)

    for image in image_list:
        df.loc[image]=re.search(regex, image).groups()
    return(df)

def write_console(output):
    # Dynamically switch between normal/disabled to prevent user input
    console.configure(state ='normal')                 
    console.insert(tk.INSERT, f"{output} \n")
    console.update()
    console.see(tk.END)
    console.configure(state ='disabled') 

def create_max_projections(uid_metadata, channel_ID, img_dir):

    if os.path.exists("temp/"):
        shutil.rmtree("temp/")

    unique_stacks = uid_metadata["UID"].unique()

    for stack in unique_stacks:
        output_path = f'{img_dir}/../max_projection'
       
        stack_images = uid_metadata[uid_metadata["UID"]==stack]
        unique_channels = uid_metadata[channel_ID].unique()

        for channel in unique_channels:
            output_file_name = f"{output_path}/{stack}_{channel}.tif"
            
            if os.path.exists(output_file_name)==False:
                files = stack_images[stack_images[channel_ID]==channel].index
                paths=[]

                for file in files:
                    img_path = os.path.join(os.path.abspath(img_dir), file)
                    paths.append(img_path)
            
                if os.path.exists("temp/")==False:
                    os.makedirs("temp/")

                stack_output_file = f"temp/{stack}_{channel}.tif"
                with tif.TiffWriter(stack_output_file) as tif_stack:
                    for i in paths:              
                        tif_stack.write(tif.imread(i), photometric='minisblack', contiguous=True)
                
                max_stack = skimage.io.imread(stack_output_file)
                max_proj = np.max(max_stack, axis=0)
    
                if not os.path.exists(output_path):
                    os.makedirs(output_path)
                
                Image.fromarray(max_proj).save(f'{output_path}/{stack}_{channel}.tif')
                write_console(f"{output_file_name} Created")
                shutil.rmtree("temp/")
            
            else:
                write_console(f"{output_file_name} Already Exists")
                continue

class chooseImages():
    def __init__(self):
        window = tk.Tk()
        window.title(window_name)
        window.configure(background=bg_color)
        window.geometry('575x250')
        window.iconbitmap(icon_path)
        window.resizable(False, False)

        # Insert Logo
        logo_img = ImageTk.PhotoImage(Image.open("assets/logo.png"))
        panel = tk.Label(window, image = logo_img, bg='#282729')
        panel.grid(row=1,column=1)

        # Initilise path box for image directory 
        path_box = tk.Entry(window,font=40, width=37, bg=bg_color, fg=font_color)
        path_box.grid(row=1,column=2)
        img_listbox = tk.Listbox(window, height = 10, width = 63, fg=font_color,
                  activestyle = 'dotbox', font = "Helvetica", bg="#414042")
        img_listbox.grid(row=2,column=1, columnspan = 4)

        # Initilise "Browse" Button and Command
        def browsefunc():
            directory = tk.filedialog.askdirectory()
            path_box.delete(0, 'end')
            path_box.insert(tk.END, directory)
            global path
            path = path_box.get()
            img_list = os.listdir(path)
            img_listbox.delete(0, 'end')
            img_listbox.insert("end", *img_list)

        browse_img = ImageTk.PhotoImage(Image.open("assets/browse.png"))
        browse_but = tk.Button(window, command=browsefunc, image=browse_img, highlightthickness=0, bd=0, bg=bg_color)
        browse_but.grid(row=1,column=3)
        
        # Initilise "Submit" Button and Command
        def submitfunc():     
            window.destroy()
            createSets(path)

        submit_img = ImageTk.PhotoImage(Image.open("assets/submit.png"))
        submit_but = tk.Button(window,command=submitfunc, image=submit_img, highlightthickness=0, bd=0, bg=bg_color)
        submit_but.grid(row=1,column=4)
        window.mainloop()

class createSets():
    def __init__(self, path):
        window = tk.Tk()
        window.title(window_name)
        window.geometry('1200x800')
        window.configure(bg=bg_color)
        window.iconbitmap(icon_path)
        
        # Insert Logo
        logo_img = ImageTk.PhotoImage(Image.open("assets/logo.png"))
        panel = tk.Label(window, image = logo_img, bg='#282729')
        panel.grid(row=1,column=1)

        # Initilise the frame and extraction table
        table_frame = tk.Frame(window, width=10)
        df = pd.DataFrame([])
        table_frame.grid(row=2,column=1, columnspan=3, rowspan=4)
        table = pt.Table(table_frame, dataframe=df, showtoolbar=False, showstatusbar=True, width=600, height=300)
        table.show()
        
        # Initilise the regular expression frame and input
        regex_entry = tk.Entry(window, width = 70, bg=input_color, fg=font_color)
        regex_entry.grid(row=1,column=2)
        regex_entry.insert('end', test_regex)
          
        # Initilise the 'Check' Button and command
        def checkfunc():     
            try:
                regex = regex_entry.get()
                global metadata
                metadata = get_meta_table(path, regex)
                table.model.df = metadata.reset_index()
                table.redraw()
                group_select.delete(0, 'end')
                group_select.insert("end", *list(metadata.columns))
                channel_select['values'] = list(metadata.columns)

            except: 
                write_console("Regular Expression Error")

        check_img = ImageTk.PhotoImage(Image.open("assets/check.png"))
        check_but = tk.Button(window,command=checkfunc, image=check_img, highlightthickness=0, bd=0, bg=bg_color)
        check_but.grid(row=1,column=3)
        
        # Initilise the Channel Selector
        variable = tk.StringVar(window)
        variable.set("Channel")
        tk.Label(window, text = "Channel Identifier:", bg=bg_color, fg=font_color).grid(row=1,column=4)

        n = tk.StringVar() 
        channel_select = ttk.Combobox(window, textvariable=n)
        channel_select.grid(row=2,column=4)

        choices = []
        tk.Label(window, text = "Group By: \n Usually Well and Field/Position", bg=bg_color, fg=font_color).grid(row=3,column=4)
        
        group_select = tk.Listbox(window, listvariable=choices, height=7, selectmode='multiple' )
        group_select.grid(row=4,column=4, rowspan=1, columnspan=2,sticky="N")

        # Initilise the 'RUN' Button and command
        def runfunc():
            write_console(f"Starting Max Projection Run....\n")
            channel_ID = channel_select.get()
            group_by = []     
            for i in group_select.curselection():
                group_by.append(group_select.get(i))          
            uid_metadata = metadata
            # Sweet lambda function: dynamically concatenates a variable number of rows
            uid_metadata["UID"] = uid_metadata[group_by].apply(lambda row: '_'.join(row), axis=1)
            create_max_projections(uid_metadata, channel_ID, path)
            
        run_but = tk.Button(window, text="RUN",font=40,command=runfunc)
        run_but.grid(row=5,column=4)

        # Initilise the console box
        tk.Label(window, text = "OUTPUT:", bg=bg_color, fg=font_color).grid(row=6,column=1)

        global console
        console = ScrolledText(window, width=100, height=15)
        console.grid(row=7,column=1, columnspan=4)
        console.configure(state ='disabled') 
        
        window.mainloop()

chooseImages()