# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 15:57:55 2024

@author: Usama.Saqib
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import webbrowser
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Global variable to enable or disable memory allocation parser
memory_parser_enabled = False

# Existing functions remain unchanged...

def parse_memory_allocation(file_path):
    p_space = 0
    x_space = 0
    y_space = 0

    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Combine lines that should be in one line
    combined_lines = []
    current_line = ""
    for line in lines:
        if line.strip() == "":
            continue
        if line.startswith(" ") and current_line:
            current_line += " " + line.strip()
        else:
            if current_line:
                combined_lines.append(current_line)
            current_line = line.strip()
    if current_line:
        combined_lines.append(current_line)

    for line in combined_lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        size_hex = parts[2]
        try:
            size = int(size_hex, 16)
        except ValueError:
            # print(f"Skipping invalid size value: {size_hex}")
            continue

        if 'P_iram' in line:
            p_space += size
        elif 'X_iram' in line:
            x_space += size
        elif 'Y_iram' in line:
            y_space += size

    return p_space, x_space, y_space

def convert_to_kb(bytes):
    return bytes / 1024

def count_lines_of_code(directory, result):
    file_types = {}
    file_paths = {}
    memory_allocations = []
    file_relationships = nx.DiGraph()

    for root, _, files in os.walk(directory):
        for file in files:
            file_type = file.split('.')[-1]
            file_path = os.path.join(root, file)
            if memory_parser_enabled and file_type == 'map':
                p_space, x_space, y_space = parse_memory_allocation(file_path)
                memory_allocations.append((file_path, p_space, x_space, y_space))
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        lines = f.readlines()
                except UnicodeDecodeError:
                    continue  # Skip files that can't be read

            blank_lines = sum(1 for line in lines if line.strip() == '')
            comment_lines = sum(1 for line in lines if line.strip().startswith('#') or line.strip().startswith('//'))
            code_lines = len(lines) - blank_lines - comment_lines

            if file_type not in file_types:
                file_types[file_type] = {'files': 0, 'blank': 0, 'comment': 0, 'code': 0}
                file_paths[file_type] = []

            file_types[file_type]['files'] += 1
            file_types[file_type]['blank'] += blank_lines
            file_types[file_type]['comment'] += comment_lines
            file_types[file_type]['code'] += code_lines
            file_paths[file_type].append((file_path, code_lines))

            # Add file relationships to the graph
            for line in lines:
                if 'import' in line or '#include' in line:
                    parts = line.split()
                    if len(parts) > 1:
                        imported_file = parts[1].strip('\";')
                        file_relationships.add_edge(file, imported_file)

    result['file_types'] = file_types
    result['file_paths'] = file_paths
    result['memory_allocations'] = memory_allocations
    result['file_relationships'] = file_relationships

def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        processing_label.config(text="FETCHING DATA...")
        result = {}
        thread = threading.Thread(target=count_lines_of_code, args=(directory, result))
        thread.start()
        root.after(100, check_thread, thread, result)

def check_thread(thread, result):
    if thread.is_alive():
        root.after(100, check_thread, thread, result)
    else:
        try:
            file_types = result['file_types']
            file_paths = result['file_paths']
            memory_allocations = result['memory_allocations']
            file_relationships = result['file_relationships']

            for file_type, counts in file_types.items():
                tree.insert("", "end", values=(file_type, counts['files'], counts['blank'], counts['comment'], counts['code']))

            total_files = sum(counts['files'] for counts in file_types.values())
            total_blank = sum(counts['blank'] for counts in file_types.values())
            total_comment = sum(counts['comment'] for counts in file_types.values())
            total_code = sum(counts['code'] for counts in file_types.values())

            sum_label.config(text=f"Files: {total_files}, Blank: {total_blank}, Comment: {total_comment}, Code: {total_code}")

            global all_file_paths
            all_file_paths = file_paths
            global all_memory_allocations
            all_memory_allocations = memory_allocations
            global all_file_relationships
            all_file_relationships = file_relationships
            processing_label.config(text="")

            populate_dropdown(file_types.keys())
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

def clear_counts():
    for item in tree.get_children():
        tree.delete(item)
    sum_label.config(text="Files: 0, Blank: 0, Comment: 0, Code: 0")

def show_file_paths(event):
    selected_item = tree.selection()[0]
    file_type = tree.item(selected_item, "values")[0]
    if file_type != "SUM:":
        if file_type == ".map":
            show_memory_allocations()
        else:
            file_paths = all_file_paths[file_type]
            new_window = tk.Toplevel(root)
            new_window.title(f"Files of type: {file_type}")

            frame = ttk.Frame(new_window, padding="10")
            frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            columns = ("File Path", "Line Count")
            treeview = ttk.Treeview(frame, columns=columns, show="headings")
            for col in columns:
                treeview.heading(col, text=col)
            treeview.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            for path, line_count in file_paths:
                treeview.insert("", "end", values=(path, line_count))

            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=treeview.yview)
            treeview.configure(yscroll=scrollbar.set)
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            new_window.grid_rowconfigure(0, weight=1)
            new_window.grid_columnconfigure(0, weight=1)

def show_memory_allocations():
    selected_item = tree.selection()[0]
    file_type = tree.item(selected_item, "values")[0]
    if file_type == ".map":
        file_paths = all_file_paths[file_type]
        for path, _ in file_paths:
            p_space, x_space, y_space = parse_memory_allocation(path)
            memory_window = tk.Toplevel(root)
            memory_window.title(f"Memory Allocation for {path}")

            frame = ttk.Frame(memory_window, padding="10")
            frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            columns = ("File Path", "P Space", "X Space", "Y Space", "Total")
            treeview = ttk.Treeview(frame, columns=columns, show="headings")
            for col in columns:
                treeview.heading(col, text=col)
            treeview.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            total_space = p_space + x_space + y_space
            treeview.insert("", "end", values=(path, f"{p_space} bytes ({convert_to_kb(p_space):.2f} KB)", f"{x_space} bytes ({convert_to_kb(x_space):.2f} KB)", f"{y_space} bytes ({convert_to_kb(y_space):.2f} KB)", f"{total_space} bytes ({convert_to_kb(total_space):.2f} KB)"))

            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=treeview.yview)
            treeview.configure(yscroll=scrollbar.set)
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            memory_window.grid_rowconfigure(0, weight=1)
            memory_window.grid_columnconfigure(0, weight=1)

def show_about():
    about_text = (
        "Line of Code and Connectivity (LOCC) Mapper\n\n"
        "Author: Usama Saqib\n\n"
        "GitHub: https://github.com/irtiq7\n\n"
        "Description: LOCC Mapper is a comprehensive tool designed to analyze and visualize the structure of codebases. "
        "It counts lines of code, identifies blank and comment lines, and maps file relationships.\n\n "
        "Tutorial:\n"
        "1. Click 'Browse Directory' to select the directory containing your code files.\n"
        "2. The tool will process the files and display the count of lines of code, blank lines, and comment lines for each file type.\n"
        "3. Double-click on a file type in the table to view the file paths and line counts for that type.\n"
        "4. Use the dropdown menu to filter files by type.\n"
        "5. Click 'Show File Relationships' to visualize the relationships between files based on imports/includes.\n"
        "6. Click 'Clear Counts' to reset the counts.\n"
        "7. Click 'About' to view this information."
    )
    
    about_window = tk.Toplevel(root)
    about_window.title("About LOCC")
    about_window.configure(bg="#f0f8ff")
    
    about_label = tk.Label(about_window, text=about_text, font=("Arial", 12), justify=tk.LEFT, wraplength=400, bg="#f0f8ff")
    about_label.pack(padx=10, pady=10)
    
    github_link = tk.Label(about_window, text="Webpage: https://irtiq7.github.io/", font=("Arial", 12), fg="blue", cursor="hand2", bg="#f0f8ff")
    github_link.pack(padx=10, pady=5)
    github_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://irtiq7.github.io/"))


def open_github(event):
    webbrowser.open_new("https://github.com/irtiq7")

def populate_dropdown(file_types):
    global dropdown_var
    dropdown_var = tk.StringVar()
    
    dropdown_label = ttk.Label(frame, text="Select File Type:")
    dropdown_label.grid(row=0, column=3, padx=5, pady=5, sticky=(tk.W, tk.E))
    
    dropdown_menu = ttk.Combobox(frame, textvariable=dropdown_var, values=["All"] + list(file_types))
    dropdown_menu.grid(row=0, column=4, padx=5, pady=5, sticky=(tk.W, tk.E))

    filter_button = ttk.Button(frame, text="Filter", command=filter_files)
    filter_button.grid(row=0, column=5, padx=5, pady=5, sticky=(tk.W, tk.E))

def filter_files():
    selected_file_type = dropdown_var.get()
    if not selected_file_type:
        messagebox.showwarning("No Selection", "Please select a file type.")
        return
    
    if selected_file_type == "All":
        filtered_paths = all_file_paths
    else:
        filtered_paths = {ftype: paths for ftype, paths in all_file_paths.items() if ftype == selected_file_type}
    
    for item in tree.get_children():
        tree.delete(item)
    
    total_files = sum(len(paths) for paths in filtered_paths.values())
    total_blank = sum(sum(path[1] for path in paths) for paths in filtered_paths.values())
    total_comment = sum(sum(path[1] for path in paths) for paths in filtered_paths.values())
    total_code = sum(sum(path[1] for path in paths) for paths in filtered_paths.values())

    for file_type, counts in filtered_paths.items():
        tree.insert("", "end", values=(file_type, len(counts), total_blank, total_comment, total_code))
    
    sum_label.config(text=f"Files: {total_files}, Blank: {total_blank}, Comment: {total_comment}, Code: {total_code}")

def toggle_memory_parser():
    global memory_parser_enabled
    memory_parser_enabled = not memory_parser_enabled
    status = "enabled" if memory_parser_enabled else "disabled"
    messagebox.showinfo("Memory Parser", f"Memory allocation parser is now {status}.")

def show_file_relationships():
    if not all_file_relationships:
        messagebox.showwarning("No Data", "No file relationships to display.")
        return

    relationship_window = tk.Toplevel(root)
    relationship_window.title("File Relationships")

    fig, ax = plt.subplots(figsize=(12, 12))
    pos = nx.spring_layout(all_file_relationships)
    nx.draw(all_file_relationships, pos, with_labels=True, node_size=300, node_color="skyblue", font_size=8, font_weight="bold", edge_color="grey", ax=ax)

    canvas = FigureCanvasTkAgg(fig, master=relationship_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    toolbar = NavigationToolbar2Tk(canvas, relationship_window)
    toolbar.update()
    canvas.get_tk_widget().pack()

    selected_node = None

    def on_click(event):
        nonlocal selected_node
        if selected_node is not None:
            nx.draw_networkx_nodes(all_file_relationships, pos, nodelist=[selected_node], node_color='skyblue', ax=ax)
            neighbors = list(all_file_relationships.neighbors(selected_node))
            nx.draw_networkx_nodes(all_file_relationships, pos, nodelist=neighbors, node_color='skyblue', ax=ax)
        
        node = None
        for n, (x, y) in pos.items():
            if (event.xdata - x)**2 + (event.ydata - y)**2 < 0.01:
                node = n
                break
        if node:
            selected_node = node
            neighbors = list(all_file_relationships.neighbors(node))
            nx.draw_networkx_nodes(all_file_relationships, pos, nodelist=[node], node_color='red', ax=ax)
            nx.draw_networkx_nodes(all_file_relationships, pos, nodelist=neighbors, node_color='green', ax=ax)
            canvas.draw()

    fig.canvas.mpl_connect('button_press_event', on_click)

# Set up the GUI
root = tk.Tk()
root.title("Line of Code and Connectivity Mapper")
root.configure(bg="#f0f8ff")  # Set a bright background color

# # Load and display the logo
# logo_path = "logo.png"  # Update this path to your logo file
# logo_image = tk.PhotoImage(file=logo_path)
# logo_label = tk.Label(root, image=logo_image, bg="#f0f8ff")
# logo_label.grid(row=0, column=0, columnspan=7, padx=5, pady=5, sticky=(tk.W, tk.E))


style = ttk.Style()
style.theme_use('clam')  # Use a modern theme
style.configure('Treeview', rowheight=25)  # Increase row height for better readability

ascii_logo = """
██╗      ██████╗  ██████╗ ██████╗    ███╗   ███╗ █████╗ ██████╗ ██████╗ ███████╗██████╗ 
██║     ██╔═══██╗██╔════╝██╔════╝    ████╗ ████║██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║     ██║   ██║██║     ██║         ██╔████╔██║███████║██████╔╝██████╔╝█████╗  ██████╔╝
██║     ██║   ██║██║     ██║         ██║╚██╔╝██║██╔══██║██╔═══╝ ██╔═══╝ ██╔══╝  ██╔══██╗
███████╗╚██████╔╝╚██████╗╚██████╗    ██║ ╚═╝ ██║██║  ██║██║     ██║     ███████╗██║  ██║ v.10
╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═
"""
logo_label = tk.Label(root, text=ascii_logo, font=("Courier", 10), justify=tk.LEFT)
logo_label.grid(row=0, column=0, columnspan=7, padx=5, pady=5, sticky=(tk.W, tk.E))

frame = ttk.Frame(root, padding="10", style="TFrame")
frame.grid(row=1, column=0, columnspan=8, sticky=(tk.W, tk.E, tk.N, tk.S))

browse_button = ttk.Button(frame, text="Browse Directory", command=browse_directory)
browse_button.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))

clear_button = ttk.Button(frame, text="Clear Counts", command=clear_counts)
clear_button.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

about_button = ttk.Button(frame, text="About", command=show_about)
about_button.grid(row=0, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))

dropdown_label = ttk.Label(frame, text="Select File Type:")
dropdown_label.grid(row=0, column=3, padx=5, pady=5, sticky=(tk.W, tk.E))

dropdown_var = tk.StringVar()
dropdown_menu = ttk.Combobox(frame, textvariable=dropdown_var)
dropdown_menu.grid(row=0, column=4, padx=5, pady=5, sticky=(tk.W, tk.E))

filter_button = ttk.Button(frame, text="Filter", command=filter_files)
filter_button.grid(row=0, column=5, padx=5, pady=5, sticky=(tk.W, tk.E))

if memory_parser_enabled:
    toggle_parser_button = ttk.Button(frame, text="Toggle Memory Parser", command=toggle_memory_parser)
    toggle_parser_button.grid(row=0, column=6, padx=5, pady=5, sticky=(tk.W, tk.E))

show_relationships_button = ttk.Button(frame, text="Show File Relationships", command=show_file_relationships)
show_relationships_button.grid(row=0, column=7, padx=5, pady=5, sticky=(tk.W, tk.E))

instruction_label = ttk.Label(frame, text="Double-click on a file type to view file locations")
instruction_label.grid(row=1, column=0, columnspan=8, padx=5, pady=5, sticky=(tk.W, tk.E))

processing_label = ttk.Label(frame, text="", font=("Arial", 12, "bold"))
processing_label.grid(row=2, column=0, columnspan=8, padx=5, pady=5, sticky=(tk.W, tk.E))

columns = ("File Type", "Files", "Blank", "Comment", "Code")
tree = ttk.Treeview(frame, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
tree.grid(row=3, column=0, columnspan=8, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
tree.configure(yscroll=scrollbar.set)
scrollbar.grid(row=3, column=8, sticky=(tk.N, tk.S))

sum_label = ttk.Label(frame, text="SUM: Files: 0, Blank: 0, Comment: 0, Code: 0")
sum_label.grid(row=4, column=0, columnspan=8, padx=5, pady=5, sticky=(tk.W, tk.E))

tree.bind("<Double-1>", show_file_paths)

frame.grid_rowconfigure(3, weight=1)
frame.grid_columnconfigure(0, weight=1)
frame.grid_columnconfigure(1, weight=1)
frame.grid_columnconfigure(2, weight=1)
frame.grid_columnconfigure(3, weight=1)
frame.grid_columnconfigure(4, weight=1)
frame.grid_columnconfigure(5, weight=1)
frame.grid_columnconfigure(6, weight=1)
frame.grid_columnconfigure(7, weight=1)

root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

root.mainloop()
