# image_viewer.py

import tkinter as tk
from PIL import Image, ImageTk, ImageDraw

def show_images(matched_files):
    if not matched_files:
        print("⚠️ 没有可显示的图像。")
        return

    root = tk.Tk()
    root.title("匹配的穴位图")

    # Maximize the window
    root.state('zoomed')  # For Windows
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Layout: horizontal scrollable canvas
    outer_frame = tk.Frame(root)
    outer_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer_frame, borderwidth=0, background="#f0f0f0")
    scrollbar = tk.Scrollbar(outer_frame, orient="horizontal", command=canvas.xview)
    scroll_frame = tk.Frame(canvas, background="#f0f0f0")

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(xscrollcommand=scrollbar.set)

    canvas.pack(side="top", fill="both", expand=True)
    scrollbar.pack(side="bottom", fill="x")

    canvas.pack_propagate(False)

    image_refs = []

    num_images = len(matched_files)
    if num_images == 0:
        print("⚠️ 无图可显示")
        return

    image_width = int(screen_width / num_images)
    image_height = int(screen_height * 0.8)  # Keep some margin for title

    for symptom, path, original_x, original_y in matched_files:
        frame = tk.Frame(scroll_frame, padx=10, pady=10, background="#f0f0f0")
        frame.pack(side="left", fill="y")

        label = tk.Label(frame, text=f"症状：{symptom}", font=("Arial", 14), background="#f0f0f0")
        label.pack()

        img = Image.open(path).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Draw red dot BEFORE resizing
        dot_radius = 6
        draw.ellipse(
            [original_x - dot_radius, original_y - dot_radius,
             original_x + dot_radius, original_y + dot_radius],
            fill="red"
        )

        # Scale image to fit into image_width
        aspect_ratio = img.width / img.height
        target_width = image_width
        target_height = int(image_width / aspect_ratio)

        # If image is too tall, shrink based on height instead
        if target_height > image_height:
            target_height = image_height
            target_width = int(image_height * aspect_ratio)

        resized = img.resize((target_width, target_height))
        tk_img = ImageTk.PhotoImage(resized)

        img_label = tk.Label(frame, image=tk_img, background="#f0f0f0")
        img_label.pack()
        image_refs.append(tk_img)

    # Bring to front
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)

    root.mainloop()
