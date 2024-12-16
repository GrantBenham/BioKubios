import os
import sys
import csv
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog, colorchooser
import traceback
from dateutil import tz
import bioread

# ---------------------------------------
# Helper Function to center windows
# ---------------------------------------
def center_window(window, width, height):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x_position = (screen_width - width) // 2
    y_position = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x_position}+{y_position}")

# ---------------------------------------
# Function 1: Read and display Biopac timings (from readacq.py)
# ---------------------------------------
def run_readacq():
    import datetime  # Ensure datetime is imported

    def select_files():
        filetypes = [("ACQ files", "*.acq")]
        file_paths = filedialog.askopenfilenames(title="Select .acq files", filetypes=filetypes)
        if file_paths:
            return file_paths
        else:
            messagebox.showerror("No Selection", "No files were selected.")
            return None

    def format_datetime(dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "Unknown"

    def adjust_datetime(dt, utc_offset=0):
        if dt:
            # Apply the UTC offset and round to the nearest second
            adjusted_time = dt + datetime.timedelta(hours=utc_offset)
            return adjusted_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return "Unknown"

    def view_markers(acq_file_paths, utc_offset):
        root = tk.Toplevel()
        root.title(f"Markers in Selected Files")
        center_window(root, 1200, 900)
        root.lift()
        root.focus_force()

        progress_frame = tk.Frame(root)
        progress_frame.pack(pady=20)
        progress_label = tk.Label(progress_frame, text="Please wait, data is being processed...")
        progress_label.pack()

        root.update()

        tree = ttk.Treeview(root, columns=('File', 'Label', 'Original UTC Time', 'UTC Adjusted Time', 'Relative Time to Segment 1'), show='headings')
        tree.heading('File', text='File')
        tree.heading('Label', text='Marker Label')
        tree.heading('Original UTC Time', text='Original UTC Time')
        tree.heading('UTC Adjusted Time', text='UTC Adjusted Time')
        tree.heading('Relative Time to Segment 1', text='Relative Time to Segment 1 (s)')

        tree.column('File', width=200)
        tree.column('Label', width=300)
        tree.column('Original UTC Time', width=200)
        tree.column('UTC Adjusted Time', width=200)
        tree.column('Relative Time to Segment 1', width=200)

        for acq_file_path in acq_file_paths:
            filename = os.path.basename(acq_file_path)
            try:
                acq_data = bioread.read_file(acq_file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Error reading {acq_file_path}: {e}")
                continue

            markers = []
            reference_time = None
            if acq_data.event_markers:
                events = acq_data.event_markers

                # Find the 'Segment 1' marker as the reference point
                for event in events:
                    if event.channel is None:
                        full_label = event.text.strip()
                        date_created_utc = event.date_created_utc
                        if "Segment 1" in full_label and reference_time is None:
                            reference_time = date_created_utc

                if reference_time is None:
                    messagebox.showerror("Error", f"No 'Segment 1' marker found in the file {filename}.")
                    continue

                for event in acq_data.event_markers:
                    if event.channel is None:
                        full_label = event.text.strip()
                        date_created_utc = event.date_created_utc

                        if date_created_utc is None:
                            continue  # Skip if no date is available

                        original_time = format_datetime(date_created_utc)
                        adjusted_time = adjust_datetime(date_created_utc, utc_offset)

                        relative_time = (date_created_utc - reference_time).total_seconds()
                        hours, remainder = divmod(relative_time, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        relative_time_formatted = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

                        tree.insert('', tk.END, values=(filename, full_label, original_time, adjusted_time, relative_time_formatted))

                tree.insert('', tk.END, values=("", "", "", "", ""))

        progress_frame.pack_forget()
        tree.pack(fill=tk.BOTH, expand=True)
        close_button = tk.Button(root, text="Close", command=root.destroy)
        close_button.pack(pady=10)
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        # No need for root.mainloop()

    def main():
        offset_root = tk.Toplevel()
        offset_root.title("Select UTC Offset")
        center_window(offset_root, 300, 300)
        offset_root.lift()
        offset_root.attributes("-topmost", True)

        utc_offset_var = tk.IntVar()
        utc_offset_var.set(-5)  # Default to -5

        label = tk.Label(offset_root, text="Select UTC Offset:")
        label.pack(pady=10)

        utc_offset_combobox = ttk.Combobox(offset_root, textvariable=utc_offset_var, state="readonly")
        utc_offset_combobox['values'] = list(range(-12, 15))  # UTC offsets from -12 to +14
        utc_offset_combobox.pack(pady=5)
        utc_offset_combobox.set(-5)  # Set default to -5

        def proceed():
            utc_offset = int(utc_offset_var.get())
            offset_root.destroy()
            acq_files = select_files()
            if acq_files:
                view_markers(acq_files, utc_offset)
            else:
                messagebox.showerror("No Selection", "No files were selected.")

        proceed_button = tk.Button(offset_root, text="Proceed", command=proceed)
        proceed_button.pack(pady=10)
        # No need for offset_root.mainloop()

    main()

# ---------------------------------------
# Function 2: Extract Biopac timings and save to CSV (integrated from extractbio3.py)
# ---------------------------------------

def run_extractbio3():
    def select_files():
        filetypes = [("ACQ files", "*.acq")]
        files = filedialog.askopenfilenames(title="Select .acq files", filetypes=filetypes)
        if files:
            return list(files)
        else:
            messagebox.showerror("No Selection", "No files were selected.")
            return None

    def format_time(seconds):
        seconds = int(round(seconds))
        hours, remainder = divmod(abs(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        return time_str

    def process_acq_file(acq_file_path):
        try:
            acq_data = bioread.read_file(acq_file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading {acq_file_path}: {e}")
            return None

        filename = os.path.basename(acq_file_path)
        marker_times = []
        problematic_markers = []
        recording_start_utc = None

        if acq_data.event_markers:
            events = acq_data.event_markers
            for event in events:
                if event.channel is None:  # Only process markers in channel 'None'
                    full_label = event.text.strip()
                    if full_label.startswith('Segment 1'):
                        recording_start_utc = event.date_created_utc
                        recording_date_str = recording_start_utc.strftime("%Y-%m-%d %H:%M")
                        continue

            if recording_start_utc is None:
                return None

            for event in events:
                if event.channel is None:  # Ensure we are only looking at 'None' channel events
                    full_label = event.text.strip()
                    if full_label.startswith('Segment'):
                        continue

                    if event.date_created_utc is None:
                        continue

                    marker_time_utc = event.date_created_utc
                    time_difference = (marker_time_utc - recording_start_utc).total_seconds()

                    if time_difference < 0:
                        problematic_markers.append({
                            'Filename': filename,
                            'Label': full_label,
                            'Marker Time': marker_time_utc,
                            'Recording Start Time': recording_start_utc,
                            'Time Difference': time_difference
                        })
                        continue

                    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                    label = full_label
                    for day in days_of_week:
                        if day in full_label:
                            label = full_label.split(day)[0].strip()
                            break

                    time_str = format_time(time_difference)
                    marker_times.append((label, time_str))

        else:
            recording_date_str = "Unknown"

        data = {
            'Filename': filename,
            'Recording Date': recording_date_str,
            'Marker Times': marker_times,
            'Notes': '',
            'Problematic Markers': problematic_markers
        }

        return data

    def resolve_duplicates(all_data):
        duplicates = []
        for data in all_data:
            # Count occurrences of each label
            label_counts = {}
            for label, _ in data['Marker Times']:
                label_counts[label] = label_counts.get(label, 0) + 1

            # Identify labels with duplicates
            duplicate_labels = [label for label, count in label_counts.items() if count > 1]
            if duplicate_labels:
                duplicates.append({
                    'Filename': data['Filename'],
                    'Duplicates': {
                        label: [time for lbl, time in data['Marker Times'] if lbl == label]
                        for label in duplicate_labels
                    }
                })

        if not duplicates:
            return all_data

        # Create GUI to resolve duplicates
        def on_submit():
            try:
                for entry in entries:
                    filename, label, var = entry
                    selection = var.get()
                    if selection == '':
                        messagebox.showerror("Selection Required", "Please select a time for each duplicate marker.")
                        return
                # Update all_data with selected times
                for entry in entries:
                    filename, label, var = entry
                    selected_time = var.get()
                    # Update data in all_data
                    for data in all_data:
                        if data['Filename'] == filename:
                            # Remove all times for this label
                            data['Marker Times'] = [mt for mt in data['Marker Times'] if mt[0] != label]
                            # Add selected time
                            data['Marker Times'].append((label, selected_time))
                root.destroy()
            except Exception as e:
                print("Error in on_submit:", e)
                traceback.print_exc()
                root.destroy()

        root = tk.Toplevel()
        root.title("Resolve Duplicate Markers")
        tk.Label(root, text="Please select the correct timing for each duplicate marker per participant.").grid(row=0, column=0, columnspan=2)

        entries = []
        row_idx = 1
        for dup in duplicates:
            filename = dup['Filename']
            tk.Label(root, text=f"File: {filename}").grid(row=row_idx, column=0, sticky='w')
            row_idx += 1
            for label, times in dup['Duplicates'].items():
                tk.Label(root, text=f"Marker: {label}").grid(row=row_idx, column=0, sticky='w')
                var = tk.StringVar(root)
                var.set(times[0])  # Default selection
                option_menu = tk.OptionMenu(root, var, *times)
                option_menu.grid(row=row_idx, column=1)
                entries.append((filename, label, var))
                row_idx += 1
        submit_btn = tk.Button(root, text="Submit", command=on_submit)
        submit_btn.grid(row=row_idx, column=0, columnspan=2)

        # Wait for the window to be closed before proceeding
        root.wait_window()

        print("Duplicate resolution completed.")
        return all_data

    # Process files
    files = select_files()
    if files is None:
        return

    all_data = []
    for acq_file in files:
        data = process_acq_file(acq_file)
        if data:
            all_data.append(data)

    # Resolve duplicate markers
    all_data = resolve_duplicates(all_data)

    # Save the extracted data to a CSV file
    output_file = 'output.csv'
    with open(output_file, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Marker Labels'] + [data['Filename'] for data in all_data])
        csv_writer.writerow(['Recording Date'] + [data.get('Recording Date', '') for data in all_data])

        # Collect all marker labels in their original order
        all_marker_labels = []
        for data in all_data:
            for label, _ in data['Marker Times']:
                if label not in all_marker_labels:
                    all_marker_labels.append(label)

        # Write the marker times to the CSV in the order they appear
        for label in all_marker_labels:
            row = [label]
            for data in all_data:
                times = [time_str for lbl, time_str in data['Marker Times'] if lbl == label]
                row.append(times[0] if times else '')
            csv_writer.writerow(row)

    messagebox.showinfo("Success", f"Extracted data saved to {output_file}")



# ---------------------------------------
# Function 3: Convert to Kubios format (integrated from ktime.py)
# ---------------------------------------
def run_ktime():
    def select_output_csv():
        file_path = filedialog.askopenfilename(title="Select output.csv file", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            messagebox.showerror("No Selection", "No file was selected.")
            return None
        return file_path

    def get_section_info(marker_labels):
        section_info = {}

        root = tk.Toplevel()
        root.title("Section Settings")
        # Adjust window size to fit 6 sections across
        window_width = 1320  # Adjusted width to fit 6 sections comfortably
        window_height = 600
        center_window(root, window_width, window_height)
        root.lift()
        root.attributes("-topmost", True)

        canvas = tk.Canvas(root)
        scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        colors_list = ['#000075', '#42d4f4', '#3cb44b', '#f032e6', '#e6194B', '#f58231', '#ffe119', '#800000']

        max_columns = 6
        num_sections = len(marker_labels)

        # Dictionaries to hold variables for each section
        duration_vars = {}
        buffer_vars = {}
        color_vars = {}
        selected_color_labels = {}

        color_buttons = {}

        for idx, label in enumerate(marker_labels):
            row = (idx // max_columns) * 10  # Adjust row spacing
            col = idx % max_columns

            # Section Frame to contain all widgets for a section
            section_frame = tk.Frame(scrollable_frame, padx=10, pady=10, bd=1, relief="solid")
            section_frame.grid(row=row, column=col, padx=10, pady=10)

            # Section Label
            tk.Label(section_frame, text=label, font=("Arial", 12, "bold")).pack(pady=5)

            # Duration Entry
            tk.Label(section_frame, text="Duration (min):").pack()
            duration_var = tk.StringVar()
            duration_entry = tk.Entry(section_frame, textvariable=duration_var, width=10)
            duration_entry.pack()
            duration_vars[label] = duration_var

            # Timing Buffer Combobox
            tk.Label(section_frame, text="Timing Buffer (min):").pack(pady=5)
            buffer_var = tk.IntVar(value=0)
            buffer_combobox = ttk.Combobox(section_frame, textvariable=buffer_var, state="readonly", width=8)
            buffer_combobox['values'] = list(range(0, 6))  # 0 to 5
            buffer_combobox.current(0)  # Default to 0
            buffer_combobox.pack()
            buffer_vars[label] = buffer_var

            # Color Selection
            tk.Label(section_frame, text="Color:").pack(pady=5)
            color_var = tk.StringVar()
            color_vars[label] = color_var

            color_frame = tk.Frame(section_frame)
            color_frame.pack()

            color_buttons[label] = []
            # Selected color label
            selected_color_label = tk.Label(section_frame, text="Selected Color: None", bg="white", width=15)
            selected_color_label.pack(pady=5)
            selected_color_labels[label] = selected_color_label

            def make_color_button(color_hex, label=label):
                btn = tk.Button(color_frame, bg=color_hex, width=2, height=1, bd=1, relief="raised")
                def select_color(b=btn, c_hex=color_hex, lbl=label):
                    # Deselect previous
                    for btn in color_buttons[lbl]:
                        btn.configure(relief="raised", bd=1)
                    # Select current
                    color_vars[lbl].set(c_hex)
                    b.configure(relief="solid", bd=2)
                    # Update selected color label
                    selected_color_labels[lbl].configure(text=f"{c_hex}", bg=c_hex)
                btn.configure(command=select_color)
                return btn

            # Create color buttons in 4x2 grid
            for i, color_hex in enumerate(colors_list):
                btn = make_color_button(color_hex, label=label)
                row_idx = i // 4
                col_idx = i % 4
                btn.grid(row=row_idx, column=col_idx, padx=2, pady=2)
                color_buttons[label].append(btn)

        # Submit Button
        def on_submit():
            for label in marker_labels:
                try:
                    duration = float(duration_vars[label].get())
                    if duration <= 0:
                        messagebox.showerror("Invalid Input", f"Duration for '{label}' must be greater than 0.")
                        return
                except ValueError:
                    messagebox.showerror("Invalid Input", f"Please enter a valid duration for '{label}'.")
                    return

                timing_buffer = buffer_vars[label].get()
                color_hex = color_vars[label].get()
                if not color_hex:
                    messagebox.showerror("No Selection", f"Please select a color for '{label}'.")
                    return

                # Convert hex color to RGB tuple
                color_rgb = tuple(int(color_hex.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))

                section_info[label] = {'duration': duration, 'buffer': timing_buffer, 'color': color_rgb}

            root.destroy()

        submit_button = tk.Button(root, text="Submit", command=on_submit)
        submit_button.pack(side="bottom", pady=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        root.wait_window()

        return section_info

    def generate_kubios_csv(output_csv_path, section_info):
        # Read the output.csv file
        with open(output_csv_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            data = list(reader)

        # Extract filenames and markers
        header = data[0]
        filenames = header[1:]
        marker_labels = []
        for row in data[2:]:
            if row[0] != 'Notes':
                marker_labels.append(row[0])
            else:
                break  # Stop if 'Notes' row is reached

        # Build a dictionary of times per file
        file_times = {}
        for idx, filename in enumerate(filenames):
            times = {}
            for row in data[2:]:
                if row[0] == 'Notes':
                    break
                label = row[0]
                time_str = row[idx + 1]  # Offset by 1 because first column is labels
                if time_str:
                    times[label] = time_str
            file_times[filename] = times

        def parse_time_str(time_str):
            parts = time_str.strip().split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
            elif len(parts) == 2:
                hours = 0
                minutes, seconds = map(int, parts)
            elif len(parts) == 1:
                hours = 0
                minutes = 0
                seconds = int(parts[0])
            else:
                raise ValueError(f"Invalid time format: {time_str}")
            return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

        def format_timedelta(tdelta):
            total_seconds = int(tdelta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}:{seconds:02}"

        # Generate Kubios_Samples.csv
        output_file = 'Kubios_Samples.csv'
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(['Kubios_Samples.csv'])
            writer.writerow(['File is used for the automatic sample generation. Kubios_Samples.csv file must be saved in the same folder as measurement file.'])
            writer.writerow([])
            writer.writerow(['Column 1: File name e.g: polar_rr_data.hrm'])
            writer.writerow(['Column 2: 0 = Sample time is given in absolute time; 1 = Sample time is given relative to beginning of the measurement'])
            writer.writerow(['Column 3: Sample Label for first sample (e.g. "Sample 1") and optionally followed by an RGB color code for the sample (e.g. "Sample 1 #255 0 0")'])
            writer.writerow(['Column 4: Start time of the sample in seconds (e.g. "600"); in hh:mm:ss format (e.g. "00:10:00"); or "START" to indicate that sample starts from the beginning of the measurement'])
            writer.writerow(['Column 5: End time of the sample in seconds (e.g. "600"); in hh:mm:ss format (e.g. "00:10:00"); or "END" to indicate that the sample ends at the end of the measurement'])
            writer.writerow(['Column 6-xx: Repeat columns 3-5 for Samples 2...N'])
            writer.writerow([])

            # Write the column headers in original order
            header_row = ['FILENAME', '0']
            for label in marker_labels:
                header_row.extend([label, 'START', 'END'])
            writer.writerow(header_row)

            for filename in filenames:
                row = [filename, '0']
                times = file_times[filename]
                for label in marker_labels:
                    start_time_str = times.get(label, '')
                    if not start_time_str:
                        row.extend(['', '', ''])
                        continue

                    duration = section_info[label]['duration']
                    timing_buffer = section_info[label]['buffer']
                    rgb = section_info[label]['color']
                    color_str = f"{label} # {rgb[0]} {rgb[1]} {rgb[2]}"

                    start_time_delta = parse_time_str(start_time_str)
                    # Add Timing Buffer
                    start_time_delta += datetime.timedelta(minutes=timing_buffer)

                    end_time_delta = start_time_delta + datetime.timedelta(minutes=duration)
                    start_time_formatted = format_timedelta(start_time_delta)
                    end_time_formatted = format_timedelta(end_time_delta)
                    row.extend([color_str, start_time_formatted, end_time_formatted])
                writer.writerow(row)

        messagebox.showinfo("Success", f"Kubios data saved to {output_file}")

    output_csv_path = select_output_csv()
    if output_csv_path is None:
        return

    with open(output_csv_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)

    marker_labels = [row[0] for row in data[2:] if row[0] != 'Notes']
    section_info = get_section_info(marker_labels)
    if section_info is None:
        return

    generate_kubios_csv(output_csv_path, section_info)





# ---------------------------------------
# Main GUI Interface
# ---------------------------------------
def main_gui():
    root = tk.Tk()
    root.title("Biopac Processing Interface")
    center_window(root, 600, 400)

    label = tk.Label(root, text="Biopac Processing Interface", font=("Arial", 18))
    label.grid(row=0, column=0, columnspan=3, pady=10)

    # Read Button: Dark Red Background, Bold White Text
    read_button = tk.Button(root, text="Read", width=15, height=5, bg='dark red', fg='white', font=("Arial", 12, "bold"), command=run_readacq)
    read_button.grid(row=1, column=0, padx=20, pady=20)

    # Extract Button: Dark Green Background, Bold White Text
    extract_button = tk.Button(root, text="Extract", width=15, height=5, bg='dark green', fg='white', font=("Arial", 12, "bold"), command=run_extractbio3)
    extract_button.grid(row=1, column=1, padx=20, pady=20)

    # Kubios Button: Dark Blue Background, Bold White Text
    kubios_button = tk.Button(root, text="Kubios", width=15, height=5, bg='dark blue', fg='white', font=("Arial", 12, "bold"), command=run_ktime)
    kubios_button.grid(row=1, column=2, padx=20, pady=20)

    # Exit Button: Centered below the others
    exit_button = tk.Button(root, text="Exit", width=10, command=root.destroy)
    exit_button.place(relx=0.5, rely=1.0, anchor=tk.S, y=-20)

    root.mainloop()

if __name__ == "__main__":
    main_gui()
