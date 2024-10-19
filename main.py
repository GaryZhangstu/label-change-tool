import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class AnnotationApp:
    def show_status_message(self, message):
        self.status_label.config(text=message)
        self.root.after(3000, lambda: self.status_label.config(text=""))
    def __init__(self, root):
        self.root = root
        self.root.title("Annotation Modification App")
        self.root.bind("<Left>", lambda event: self.previous_image())
        self.root.bind("<Right>", lambda event: self.next_image())

        self.json_data = None
        self.images_folder = None
        self.current_image_index = 0
        self.annotations = []

        # UI Elements
        self.upload_button = tk.Button(root, text="Upload JSON File", command=self.upload_json)
        self.upload_button.grid(row=0, column=0, padx=10, pady=5, sticky='w')

        self.open_folder_button = tk.Button(root, text="Open Images Folder", command=self.open_images_folder)
        self.open_folder_button.grid(row=1, column=0, padx=10, pady=5, sticky='w')

        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.grid(row=0, column=1, rowspan=6, padx=10, pady=5)
        self.canvas_width = 1200
        self.canvas_height = 800
        self.canvas = tk.Canvas(self.canvas_frame, bg='white', width=self.canvas_width, height=self.canvas_height, scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.class_name_var = tk.StringVar()
        self.class_name_options = ["acne", "scar", "freckle", "mole"]
        self.class_name_menu = tk.OptionMenu(root, self.class_name_var, *self.class_name_options, command=self.update_class_name)
        self.class_name_menu.grid(row=2, column=0, padx=10, pady=5, sticky='w')

        

        self.previous_image_button = tk.Button(root, text="Previous Image", command=self.previous_image)
        self.previous_image_button.grid(row=4, column=0, padx=10, pady=5, sticky='w')

        self.next_image_button = tk.Button(root, text="Next Image", command=self.next_image)
        self.next_image_button.grid(row=5, column=0, padx=10, pady=5, sticky='w')

        self.status_label = tk.Label(root, text="", fg="green")
        self.status_label.grid(row=6, column=1, padx=10, pady=5, sticky='se')

    def save_json(self):
        if self.json_data:
            with open(self.json_file_path, 'w') as f:
                json.dump(self.json_data, f, indent=4)

    def upload_json(self):
        json_file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if json_file_path:
            with open(json_file_path, 'r') as f:
                self.json_data = json.load(f)
            self.json_file_path = json_file_path
            messagebox.showinfo("Info", "JSON File Loaded Successfully")
            self.load_image()

    def open_images_folder(self):
        self.images_folder = filedialog.askdirectory()
        if self.images_folder:
            messagebox.showinfo("Info", "Images Folder Loaded Successfully")

    def load_image(self):
        self.zoom_scale = 1.0
        if not self.json_data or not self.images_folder:
            messagebox.showwarning("Warning", "Please load JSON file and images folder first.")
            return

        images = self.json_data.get("images", [])
        if self.current_image_index >= len(images):
            messagebox.showinfo("Info", "No more images to display.")
            return

        image_info = images[self.current_image_index]
        image_path = os.path.join(self.images_folder, image_info["file_name"])

        if os.path.exists(image_path):
            image = Image.open(image_path)
            image.thumbnail((800, 600), Image.LANCZOS)
            
            self.photo = ImageTk.PhotoImage(image)
            self.canvas.config(scrollregion=(0, 0, image.width, image.height))
            if hasattr(self, 'image_on_canvas'):
                self.canvas.delete(self.image_on_canvas)
                if hasattr(self, 'image_on_canvas'):
                    self.canvas.delete(self.image_on_canvas)
                self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.load_annotations(image_info["id"], image.width / image_info["width"], image.height / image_info["height"])
            self.canvas.bind("<Button-1>", self.on_annotation_click)
            self.canvas.bind("<MouseWheel>", self.zoom_image)
            self.canvas.tag_raise("annotation")
            self.canvas.bind("<Button-1>", self.on_annotation_click)
        else:
            messagebox.showwarning("Warning", f"Image {image_info['file_name']} not found in folder.")

    def load_annotations(self, image_id, scale_x, scale_y):
        self.annotation_ids = []
        self.canvas.delete("annotation")
        self.annotations = [ann for ann in self.json_data.get("annotations", []) if ann["image_id"] == image_id]
        
        for ann in self.annotations:
            x, y = ann["coordinates"]
            x *= scale_x
            y *= scale_y
            radius = ann["radius"]
            radius *= (scale_x + scale_y) / 2
            annotation_id = self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline="red", width=2, tags=("annotation", f"annotation_{ann['id']}"))
            self.annotation_ids.append((annotation_id, ann))

    def update_class_name(self, _=None):
        if not hasattr(self, 'selected_annotation'):
            messagebox.showwarning("Warning", "Please select an annotation first.")
            return
        new_class_name = self.class_name_var.get()
        if not new_class_name:
            messagebox.showwarning("Warning", "Please enter a class name.")
            return

        self.selected_annotation["class_name"] = new_class_name
        self.save_json()
        self.show_status_message("Class name updated successfully.")

        

    def on_annotation_click(self, event):
        # Reset all annotations to red before handling the click
        for annotation_id, _ in self.annotation_ids:
            self.canvas.itemconfig(annotation_id, outline="red", width=2)
        clicked_x, clicked_y = event.x, event.y
        for annotation_id, ann in self.annotation_ids:
            coords = self.canvas.coords(annotation_id)
            x1, y1, x2, y2 = coords
            if x1 <= clicked_x <= x2 and y1 <= clicked_y <= y2:
                self.selected_annotation = ann
                self.class_name_var.set(ann["class_name"])
                # Change the selected annotation to green
                self.canvas.itemconfig(annotation_id, outline="green", width=2)
                return

    def zoom_image(self, event):
        scale_factor = 1.1 if event.delta > 0 else 0.9
        self.zoom_scale = max(0.1, min(5.0, self.zoom_scale * scale_factor))

        # Redraw the image with updated scale
        images = self.json_data.get("images", [])
        if self.current_image_index < len(images):
            image_info = images[self.current_image_index]
            image_path = os.path.join(self.images_folder, image_info["file_name"])
            if os.path.exists(image_path):
                image = Image.open(image_path)
                new_size = (int(image.width * self.zoom_scale), int(image.height * self.zoom_scale))
                image = image.resize(new_size, Image.LANCZOS)
                self.photo = ImageTk.PhotoImage(image)
                self.canvas.config(scrollregion=(0, 0, new_size[0], new_size[1]))
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
                self.load_annotations(image_info["id"], new_size[0] / image_info["width"], new_size[1] / image_info["height"])
                self.canvas.tag_raise("annotation")

    def previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_image()

    def next_image(self):
        self.current_image_index += 1
        self.load_image()


if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationApp(root)
    root.mainloop()
