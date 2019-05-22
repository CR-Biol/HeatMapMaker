"""
Python script to make heatmaps from CSV files.
These files are reminescent to an Excel sheet of the form:

        1              2          3          4          5
A       any            label1     label2     label3     ...
B       condition1     data       data       data       ...
C       condition2     data       data       data       ...
D       condition3     data       data       data       ...
E       ...            ...        ...        ...        ...

where label and condition are explanatory strings while data represents any 
numerical data form.
Cell A1 may contain any string and is ignored by the script. 

CSVs used here are derived from an Excel sheet.
To generate a CSV file, go to "Data", "Export", "Change Type" and chose CSV.
Nothing else should be contained in the excel sheet.

Per default, the German Excel version is assumed. If another CSV type is used,
change the SEPERATOR_IN_INPUT_CSV variable accordingly.
Make sure that if you use a number notation where the decimal point is written 
as a comma to not have conflicting cell delimiters! 

Christian Rauch
05/2019.
"""

__version__ = "1.0"
__author__ = "Christian Rauch"

import sys
import os
import tkinter as tk
import tkinter.filedialog
import tkinter.font as tkFont
from tkinter import ttk

from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# sep in input csv


class CSV:
    """Object containing information stored in plain text CSV file.
    Initializes by reading the file specified with the string path_to_csv_file.
    Uses optional argument seperator to seperate cells. If no seperator is
    given, a standard character (',') is used.
    """
    def __init__(
        self, 
        path_to_csv_file, 
        seperator=",", 
        has_row_titles=True, 
        has_col_titles=True
        ):
        self._sep = seperator
        self.rows = []
        with open(path_to_csv_file) as csv_file:
            for line in csv_file:
                self.rows.append(line.strip().split(sep=self._sep))
        assert self.all_are_the_same_length(self.rows)
        self.length_of_rows = len(self.rows[0])

        self.cols = []
        for idx in range(self.length_of_rows):
            _col = [row[idx] for row in self.rows]
            self.cols.append(_col)
        assert self.all_are_the_same_length(self.cols)
        self.length_of_cols = len(self.cols[0])

        self._row_titles, self._col_titles = has_row_titles, has_col_titles


    def all_are_the_same_length(self, iterable):
        """Returns True if all items in an iterable are the same length.
        Returns False otherwise."""
        length = None
        for item in iterable:
            if length is None:
                length = len(item)
            if not len(item) == length:
                return False
        return True


    def __repr__(self):
        csv_as_str = ""
        for row in self.rows:
            csv_as_str += str(row) + "\n"
        return csv_as_str


    # def read_file(self, file):
    #     with open(file) as csv_file:
    #         for line in csv_file:
    #             self.rows.append(line.strip().split(sep=self._sep))


    def to_df(self):
        """Parses the CSV into a pandas dataframe resembling the orientation of
        the original input file.
        """
        row_titles = self.get_row_titles()
        col_titles = self.get_col_titles()
        data = self.get_data_per_row_without_titles()
        data = self.parse_data(data)
        dataframe = pd.DataFrame(data, index=row_titles, columns=col_titles)
        return dataframe


    def parse_data(self, list_of_list_with_numerical_data_as_strings):
        """Takes a nested list and parses every inner element into a float."""
        parsed_data = [[float(val.replace(",", ".")) for val in nested_list] 
                    for nested_list in list_of_list_with_numerical_data_as_strings
                    ]
        return parsed_data


    def get_row_titles(self):
        """Returns a list of list, where the inner list constitutes rows of the
        original input file.
        """
        if self._row_titles:
            if self._col_titles:
                return [row[0] for i, row in enumerate(self.rows) if i != 0]
            else:
                return [row[0] for row in self.rows]
        else:
            return None


    def get_col_titles(self):
        """Returns a list of list, where the inner list constitutes columns of 
        the original input file.
        """
        if self._col_titles:
            if self._row_titles:
                return [col[0] for i, col in enumerate(self.cols) if i != 0]
            else:
                return [col[0] for col in self.cols if col]
        else:
            return None


    def get_data_per_row_without_titles(self):
        """Returns a list of list where the inner list represents rows of the 
        original input file. 
        Row and column headings are stripped from the returned nested list.
        """
        relevant_rows = []
        if self._row_titles and self._col_titles:
            for i, row in enumerate(self.rows):
                if i == 0:
                    continue
                relevant_rows.append(row[1:])
        elif self._col_titles:
            for i, row in enumerate(self.rows):
                if i == 0:
                    continue
                relevant_rows.append(row)
        elif self._row_titles:
            for row in self.rows:
                relevant_rows.append(row[1:])
        else:
            relevant_rows = self.rows
        return relevant_rows


    def get_data_per_col_without_titles(self):
        """Returns a list of list where the inner list represents columns of the 
        original input file. 
        Row and column headings are stripped from the returned nested list.
        """
        relevant_cols = []
        if self._row_titles and self._col_titles:
            for i, col in enumerate(self.cols):
                if i == 0:
                    continue
                relevant_cols.append(col[1:])
        elif self._row_titles:
            for i, col in enumerate(self.cols):
                if i == 0:
                    continue
                relevant_cols.append(col)
        elif self._col_titles:
            for col in self.cols:
                relevant_cols.append(col[1:])
        else:
            relevant_cols = self.cols
        return relevant_cols
    

def make_heatmap(
    dataframe,
    filename,
    colormap,
    show_values_in_cells,
    cells_should_be_squared,
    lower_boundary,
    upper_boundary,
    dpi=300,
    title=None,
    center=None,
    cbar_label="log2 (fold change)"
    ):
    """Main function to plot heatmaps.

    Required arguments:
    dataframe                 pandas DataFrame, contains data to be plotted
    filename                  string, file name handle used to save the plot
    colormap                  string, specifies pyplot colormap used in heatmap
    show_values_in_cells      boolean, if True plots raw data values in cells
    cells_should_be_squared   boolean, if True coerces cells in square shape
    lower_boundary            numerical, lowest value for color computation
    upper_boundary            numerical, highest value for color computation

    Optional arguments:
    dpi                       numerical, DPI for the saved heatmap
    title                     string, specifies plot title if given
    center                    numerical, center color calculation. If omitted,
                                takes numerical mean of lower_boundary and 
                                upper_boundary
    cbar_label                string, specifies label for the colorbar
    """
    if center is None:
        center = (lower_boundary + upper_boundary) / 2

    plt.rcParams["font.weight"] = "bold"
    sns.set(font_scale=0.75)
    fig, ax = plt.subplots()
    sns.heatmap(
        dataframe,
        ax = ax,
        cmap = colormap,
        vmin = lower_boundary, 
        center = center, 
        vmax = upper_boundary, 
        annot = show_values_in_cells, 
        fmt = ".1f", # Prevents e+ notation for shown values.
        linecolor = "white",
        linewidth = 3, # Size of cell margins. Set 0 to remove margins.
        cbar_kws = {"label": f"\n{cbar_label}"} 
        ) 

    ax.set_xticklabels(ax.get_xticklabels(), rotation = 45) 
    ax.xaxis.tick_top() 
    if cells_should_be_squared:
        ax.set_aspect("equal") 

    if title is not None:
        plt.title(title, fontweight = "bold", fontsize = 18)

    plt.tight_layout() 
    plt.savefig(filename, dpi = dpi)
    plt.close(title)
    return True


class EntryWithPlaceholder(tk.Entry):
    """Class written by Stackoverflow user Nae.
    https://stackoverflow.com/questions/27820178/how-to-add-placeholder-to-an-entry-in-tkinter
    """
    def __init__(
        self, 
        master=None, 
        placeholder="default", 
        textvariable=None, 
        color='grey'
        ):
        super().__init__(master, textvariable=textvariable)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()


class MainWindow(tk.Frame):
    """Helper Class for building the GUI. 
    Contains methods for easier access of utilities for registering and placing
    widgets in the main app.
    """
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.exit_button = tk.Button(self, text="Exit", command=self.quit)


    def register_exit_button(self):
        """This method is to be used for placing the exit_button using a
        geometry manager of choice."""
        return self.exit_button


    def quit(self):
        """Ends application. Used by self.exit_button."""
        sys.exit()


    def spacer(self):
        """Generate an empty label for spacing."""
        return tk.Label(self, text="")


    def label(self, text):
        """Return a label from a string or tkinter StringVar."""
        if isinstance(text, str):
            return tk.Label(self, text=text)
        elif isinstance(text, tk.StringVar):
            return tk.Label(self, textvariable=text)
        else:
            raise ValueError("text must be string or tk.StringVar type.")


    def button(self, text, function):
        """Returns a tkinter Button with an attached text and function."""
        return tk.Button(self, text=text, command=function)


    def entry(self, string_var):
        """Returns a tkinter Entry with an attached tkinter StringVar."""
        return tk.Entry(self, textvariable=string_var)


    def radiobuttons(
        self, 
        text_for_on, 
        text_for_off, 
        var,
        on_val=True, 
        off_val=False
        ):
        """Returns two tkinter Radiobuttons (on and off) with given text as 
        label and tkinter variable.
        """         
        on = tk.Radiobutton(self, text=text_for_on, variable=var, value=on_val)
        off = tk.Radiobutton(self, text=text_for_off, variable=var, value=off_val)
        return on, off


class DrawGui:
    def __init__(self, parent):
        parent.title(f"HeatMapMaker {__version__}")
        self.heatmap_title = tk.StringVar()
        self.min_value = tk.IntVar()
        self.max_value = tk.IntVar()
        self.dpi = tk.IntVar()
        self.notification_csv = tk.StringVar()
        self.notification_heatmap = tk.StringVar()
        self.legal_colors = {
            "Blue and Red (strong)": "seismic",
            "Blue and Red (light)": "bwr",
            "Blue with high values in green": "ocean_r",
            "White to Blue": "Blues",
            "Black and White": "binary",
            "Color Blind Mode": "PuOr"
            }
        self.ckey = tk.StringVar()
        self.show_annotation_in_cells = tk.BooleanVar()
        self.show_cells_as_squares = tk.BooleanVar()
        self.seperator_in_input_csv = tk.StringVar()

        self.set_base_style()
        self.set_variables_to_default()
        self.register_widgets(parent)
        self.make_menu_bar(parent)

        
    def set_base_style(self):
        self.font_size = "10"
        self.font_family = "Nirmala UI"
        self.BTN_WIDTH = 15

        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(
            size = self.font_size,
            family = self.font_family
            )


    def set_variables_to_default(self):
        """Sets all Gui variables to a default state."""
        self.min_value.set(-4)
        self.max_value.set(+4)
        self.dpi.set(600)
        self.notification_csv.set(
            "No data CSV defined yet. Click 'Read CSV' to proceed."
            )
        self.dataframe = None
        self.ckey.set("Blue and Red (strong)")
        self.show_annotation_in_cells.set(True)
        self.show_cells_as_squares.set(True)
        self.seperator_in_input_csv.set(";")


    def register_widgets(self, parent):
        """Registers all widgets needed for the Gui to function.
        Makes use of the MainWindow helper class.
        """
        top = MainWindow(parent)
        top.grid()

        self.welcome_label = top.label(
            "Welcome to the heat map maker.\nPlease chose configuration "
            "as appropriate, the click 'Save Heatmap' \nto generate "
            "and save a heat map plot"
            )
            
        self.make_big(self.welcome_label)
        self.welcome_label.grid(
            row = 0, 
            columnspan = 2,
            padx = 10,
            pady = (20, 10)
            )

        top.spacer().grid()

        self.choose_cmap_label =  top.label("Chose a color map: ")
        self.choose_cmap_label.grid(row = 2, column = 0, sticky = tk.E)

        self.color_option_menu = tk.OptionMenu(
            top, 
            self.ckey, 
            *self.legal_colors.keys()
            )
        self.color_option_menu.configure(width = "30")
        self.color_option_menu.grid(row = 2, column = 1, sticky = tk.W)

        self.show_annotation_in_cells_on, self.show_annotation_in_cells_off = top.radiobuttons(
            "Show values in cells", 
            "Show only colors", 
            self.show_annotation_in_cells
            )
        self.show_annotation_in_cells_on.grid(row=3, column=0, sticky=tk.W, padx = 10)
        self.show_annotation_in_cells_off.grid(row=3, column=1, sticky=tk.W)
        self.square_on, self.square_off = top.radiobuttons(
            "Coerce cells into squares", 
            "Cells as rectangles", 
            self.show_cells_as_squares
            )
        self.square_on.grid(row=4, column=0, sticky=tk.W, padx = 10)
        self.square_off.grid(row=4, column=1, sticky=tk.W)

        top.spacer().grid()

        self.title_label = top.label("(Optional) Enter the title for your heat map: ")
        self.title_label.grid(row=6, column=0, stick=tk.E)
        self.title_entry = EntryWithPlaceholder(
            top, 
            placeholder = "Heatmap Title",
            textvariable = self.heatmap_title
            )
        self.title_entry.configure(width = "40", justify = "center")
        self.title_entry.grid(
            row=6, 
            column=1, 
            padx=5,
            pady=5, 
            ipady=3,
            stick=tk.W
            ) 
        
        self.seperator_label = top.label("Seperator used in CSV file: ")
        self.seperator_label.grid(row=7, column=0, sticky=tk.E)
        self.seperator_entry = top.entry(self.seperator_in_input_csv)
        self.seperator_entry.configure(width = "40", justify = "center")
        self.seperator_entry.grid(
            row=7, 
            column=1, 
            padx=5,
            pady=5, 
            ipady=3,
            stick=tk.W
            ) 
        
        top.spacer().grid()

        self.csv_read_label = top.label(self.notification_csv)
        self.make_big(self.csv_read_label)
        self.csv_read_label.grid(columnspan=3, padx=5, pady=5)
        self.heatmap_status_label = top.label(self.notification_heatmap)
        self.make_big(self.heatmap_status_label)
        self.heatmap_status_label.grid(columnspan=3, padx=5, pady=5)

        top.spacer().grid()

        sub = MainWindow(top)
        sub.grid(columnspan=2)

        self.read_button = tk.Button(
            sub, 
            text = "Read CSV", 
            command = self.define_dataframe
            )
        self.heatmap_button = tk.Button(
            sub, 
            text = "Save Heatmap", 
            command = self.call_make_heatmap
            )
        self.cancel_button = sub.register_exit_button()

        self.configure_btn(self.read_button)
        self.configure_btn(self.heatmap_button)
        self.configure_btn(self.cancel_button)

        self.read_button.grid(row=0, column=0, padx=10, pady=15)
        self.heatmap_button.grid(row=0, column=1, padx=10, pady=15)
        self.cancel_button.grid(row=0, column=3, padx=10, pady=15)

        self.copyright = top.label(f"Written by Christian Rauch, version {__version__}")
        self.make_small(self.copyright)
        self.copyright.grid(pady = (0, 10))


    def configure_btn(self, btn_widget):
        btn_widget.configure(
            width=self.BTN_WIDTH, 
            font=(self.font_family, self.font_size, "bold"),
            cursor="hand2",
            background="#bbb",
            activebackground="#4c4c4c" 
        )


    def make_small(self, widget):
        widget.configure(
            font = (
                self.font_family, 
                str(int( int(self.font_size) * 0.75 ))
                )
        )


    def make_big(self, widget):
        widget.configure(
            font = (
                self.font_family, 
                str(int (int(self.font_size) * 1.25 )), 
                "bold"
                )
        )


    def define_dataframe(self):
        """Opens input CSV file and parses it into a pandas DataFrame."""
        csv_file =  tk.filedialog.askopenfilename(
            initialdir = os.getcwd(),
            title = "Select CSV file",
            filetypes = (("CSV files", "*.csv"), ("all files", "*.*"))
            )
        csv = CSV(csv_file, seperator=self.seperator_in_input_csv.get())
        self.dataframe = csv.to_df()
        self.notification_csv.set(f"Current active data CSV: {os.path.basename(csv_file)}")
        self.notification_heatmap.set("")


    def call_make_heatmap(self):
        """Calls the make_heatmap function. 
        Wrapper function to attach the call to a tkinter Button.
        """
        if self.dataframe is None:
            self.notification_heatmap.set(
                "Could not make heatmap." 
                + " Check if a CSV file has been read!"
                )
            return

        save_to = tk.filedialog.asksaveasfilename(
            defaultextension = ".png",
            filetypes = [('PNG files', '.png'), ('all files', '.*')]
            )
        has_made_heatmap = make_heatmap(
            dataframe = self.dataframe,
            title = self.heatmap_title.get(), 
            colormap = self.legal_colors[self.ckey.get()],
            filename = save_to,
            show_values_in_cells = self.show_annotation_in_cells.get(),
            cells_should_be_squared = self.show_cells_as_squares.get(),
            lower_boundary = self.min_value.get(),
            upper_boundary = self.max_value.get(),
            dpi = self.dpi.get()
            )

        if has_made_heatmap:
            self.notification_heatmap.set(f"Created heatmap2 '{self.heatmap_title.get()}'")
        else:
            self.notification_heatmap.set(
                "Could not make heatmap." 
                + " Check if a CSV file has been read!"
                )


    def help(self, parent, about):
        """Opens a help window about a topic."""
        def close():
            window.destroy()
        msg = ""
        path_to_files = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 
            "help"
            )
        with open(os.path.join(path_to_files, about)) as file:
            for line in file:
                msg += line
        window = tk.Toplevel(parent)
        help_text = tk.Label(window, text=msg, justify=tk.LEFT).pack(padx=5, pady=5)
        ok_button = tk.Button(window, text="OK", command=close).pack(pady=5)
        return


    def setting(self, var, label_text):
        """Function to be called to change the variables from the Settings menu."""
        def ok():
            new_val = int(wrapper_var.get())
            var.set(new_val)
            new.destroy()

        new = tk.Toplevel(root)
        wrapper_var = tk.StringVar()
        wrapper_var.set(str(var.get()))
        tk.Label(new, text="Set new value for {}:".format(label_text)).pack(padx=5)
        tk.Entry(new, textvariable=wrapper_var).pack(padx=5, pady=10)
        tk.Button(new, text="OK", command=ok).pack(pady=5)
        return


    def make_menu_bar(self, parent):
        """Creates dropdown menubar for the Gui."""        
        menubar = tk.Menu(parent)

        settingsmenu = tk.Menu(menubar, tearoff=0)
        settingsmenu.add_command(
            label = "Set Maximum Value for Color Scale",
            command = lambda: self.setting(
                self.max_value, 
                "maximal value on color scale"
                )
            )
        settingsmenu.add_command(
            label = "Set Minimum Value for Color Scale",
            command = lambda: self.setting(
                self.min_value, 
                "minmal value on color scale"
                )
            )
        settingsmenu.add_separator()
        settingsmenu.add_command(
            label = "Set DPI for Heat Map PNG file",
            command = lambda: self.setting(
                self.dpi, 
                "DPI count"
                )
            )
        menubar.add_cascade(
            label = "Settings", 
            menu = settingsmenu
            )
            
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(
            label = "About", 
            command = lambda: self.help(parent, "about.txt")
            )
        helpmenu.add_command(
            label = "Required Data Format", 
            command = lambda: self.help(parent, "format.txt")
            )
        helpmenu.add_separator()
        helpmenu.add_command(
            label = "Exit", 
            command = sys.exit
            )
        menubar.add_cascade(
            label = "Help", 
            menu = helpmenu
            )
        parent.config(menu = menubar)


if __name__ == "__main__":
    root = tk.Tk() 
    DrawGui(root)
    root.mainloop()
