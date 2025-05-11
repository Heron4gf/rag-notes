import tkinter as tk
from tkinter import simpledialog, messagebox
from vect_db import find_docs, add_doc, delete_doc, update_doc
from document import Document
import uuid

class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RAG Notes App")
        self.root.geometry("500x600")
        self.root.configure(bg="#f9f9f6")

        # Top bar frame
        top_frame = tk.Frame(root, bg="#f9f9f6")
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Delete (trash) icon
        self.delete_icon = tk.Label(top_frame, text="🗑️", font=("Arial", 18), cursor="hand2", bg="#f9f9f6")
        self.delete_icon.pack(side=tk.LEFT, padx=(0, 10))
        self.delete_icon.bind("<Button-1>", self.delete_note)

        # Search bar
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(top_frame, textvariable=self.search_var, font=("Arial", 14), width=28, relief=tk.GROOVE, bd=2)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.search_entry.bind("<Return>", self.search_notes)

        # Add (plus) icon
        self.add_icon = tk.Label(top_frame, text="＋", font=("Arial", 22), cursor="hand2", bg="#f9f9f6")
        self.add_icon.pack(side=tk.RIGHT, padx=(10, 0))
        self.add_icon.bind("<Button-1>", self.add_note)

        # Main text area for note content
        self.text_area = tk.Text(root, font=("Arial", 14), wrap=tk.WORD, relief=tk.FLAT, bg="#fff", bd=2)
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=20, pady=(0, 20))

        # State
        self.current_doc = None
        self.notes = []

        # Initial load
        self.load_notes()

        # Save on text change (after typing stops)
        self.text_area.bind("<KeyRelease>", self.schedule_save)

        self.save_after_id = None

    def load_notes(self, query=""):
        self.notes = find_docs(query)
        if self.notes:
            self.current_doc = self.notes[0]
            self.display_note(self.current_doc)
        else:
            self.current_doc = None
            self.text_area.delete("1.0", tk.END)

    def display_note(self, doc):
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, doc.content)

    def add_note(self, event=None):
        new_id = str(uuid.uuid4())
        new_doc = Document(id=new_id, content="")
        add_doc(new_doc)
        self.current_doc = new_doc
        self.load_notes()
        self.display_note(new_doc)

    def delete_note(self, event=None):
        if not self.current_doc:
            messagebox.showinfo("No note", "No note to delete.")
            return
        if messagebox.askyesno("Delete", "Are you sure you want to delete this note?"):
            delete_doc(self.current_doc.id)
            self.load_notes()

    def search_notes(self, event=None):
        query = self.search_var.get()
        self.load_notes(query=query)

    def schedule_save(self, event=None):
        if self.save_after_id:
            self.root.after_cancel(self.save_after_id)
        self.save_after_id = self.root.after(1000, self.save_note)

    def save_note(self):
        if self.current_doc:
            new_content = self.text_area.get("1.0", tk.END).strip()
            if new_content != self.current_doc.content:
                self.current_doc.content = new_content
                update_doc(self.current_doc)

if __name__ == "__main__":
    root = tk.Tk()
    app = NotesApp(root)
    root.mainloop()
