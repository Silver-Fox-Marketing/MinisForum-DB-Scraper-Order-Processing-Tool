import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import subprocess

# --- File paths ---
config_file = 'input_data/config.csv'
main_script = 'main.py'

# --- Load config data ---
try:
    config_df = pd.read_csv(config_file)
    config_df = config_df.sort_values(by='site_name')
except FileNotFoundError:
    print("CSV file not found.")
    exit()

# --- Tkinter setup ---
root = tk.Tk()
root.title("Vehicle Scraper v18")
root.geometry("650x650")  # Increase window size

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill='both', expand=True)

# --- Checkbox variables ---
checkbox_vars = {}
font_style = ("Arial", 12)

# Split entries into two columns
half = (len(config_df) + 1) // 2
left_frame = ttk.Frame(main_frame)
right_frame = ttk.Frame(main_frame)
left_frame.grid(row=0, column=0, sticky='n')
right_frame.grid(row=0, column=1, sticky='n', padx=20)

for i, (_, row) in enumerate(config_df.iterrows()):
    var = tk.BooleanVar(value=(row['to_scrap'].strip().lower() == 'yes'))
    cb = ttk.Checkbutton(
        left_frame if i < half else right_frame,
        text=row['site_name'],
        variable=var
    )
    cb.configure(style='Custom.TCheckbutton')
    cb.pack(anchor='w', pady=2)
    checkbox_vars[row['site_name']] = var

# --- Style configuration ---
style = ttk.Style()
style.configure('TButton', font=font_style)
style.configure('Custom.TCheckbutton', font=font_style)
style.configure('TLabel', font=font_style)

# --- Save function ---
def save_changes():
    for site, var in checkbox_vars.items():
        config_df.loc[config_df['site_name'] == site, 'to_scrap'] = 'yes' if var.get() else 'no'
    config_df.to_csv(config_file, index=False)
    messagebox.showinfo("Success", "Changes saved.")
    try:
        subprocess.run(['python', main_script], check=True)
        messagebox.showinfo("Success", "main.py ran successfully.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"main.py failed:\n{e}")

# --- Save button (inside main_frame) ---
tt_btn = ttk.Button(main_frame, text="Save Changes", command=save_changes)
tt_btn.grid(row=1, column=0, columnspan=2, pady=20)


# --- Start app ---
root.mainloop()
