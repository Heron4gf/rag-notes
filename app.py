import tkinter as tk
from tkinter import simpledialog, messagebox, font as tkFont
from vect_db import find_docs, add_doc, delete_doc, update_doc
from document import Document
import uuid
import threading
import time
import pyperclip

class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RAG Notes App")
        self.root.geometry("600x700")
        
        self.colors = {
            "bg": "#f0f0f0",
            "top_bar_bg": "#e0e0e0",
            "search_bg": "#ffffff",
            "text_bg": "#ffffff",
            "button_bg": "#d0d0d0",
            "text_fg": "#333333",
            "accent": "#007aff"
        }
        self.root.configure(bg=self.colors["bg"])

        self.default_font = tkFont.Font(family="Arial", size=12)
        self.entry_font = tkFont.Font(family="Arial", size=14)
        self.text_font = tkFont.Font(family="Arial", size=14)
        self.icon_font = tkFont.Font(family="Arial", size=20)

        top_frame = tk.Frame(root, bg=self.colors["top_bar_bg"], padx=10, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self.delete_icon = tk.Label(top_frame, text="🗑️", font=self.icon_font, cursor="hand2", bg=self.colors["top_bar_bg"], fg=self.colors["text_fg"])
        self.delete_icon.pack(side=tk.LEFT, padx=(0, 10))
        self.delete_icon.bind("<Button-1>", self.delete_note)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(top_frame, textvariable=self.search_var, font=self.entry_font, width=30, relief=tk.GROOVE, bd=1, bg=self.colors["search_bg"], fg=self.colors["text_fg"])
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=4)
        self.search_entry.bind("<Return>", self.search_notes_action)
        self.search_entry.bind("<KeyRelease>", self.schedule_search_suggestions)

        self.add_icon = tk.Label(top_frame, text="＋", font=self.icon_font, cursor="hand2", bg=self.colors["top_bar_bg"], fg=self.colors["text_fg"])
        self.add_icon.pack(side=tk.RIGHT, padx=(10, 0))
        self.add_icon.bind("<Button-1>", self.add_note)
        
        self.suggestions_frame = tk.Frame(root, bg=self.colors["bg"])
        
        self.suggestions_listbox = tk.Listbox(self.suggestions_frame, font=self.default_font, bg=self.colors["text_bg"], fg=self.colors["text_fg"], relief=tk.FLAT, highlightthickness=1, highlightbackground=self.colors["accent"])
        self.suggestions_listbox.pack(fill=tk.X, expand=True)
        self.suggestions_listbox.bind("<<ListboxSelect>>", self.on_suggestion_select)

        self.text_area = tk.Text(root, font=self.text_font, wrap=tk.WORD, relief=tk.FLAT, bg=self.colors["text_bg"], fg=self.colors["text_fg"], bd=0, padx=10, pady=10, highlightthickness=1, highlightbackground=self.colors["accent"])
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

        self.current_doc = None
        self.notes_cache = {} 
        
        self.load_notes()

        self.text_area.bind("<KeyRelease>", self.schedule_save)
        self.save_after_id = None
        self.search_after_id = None
        
        self.root.bind_all("<Button-1>", self.hide_suggestions_on_click_outside, add="+")

        self.clipboard_monitoring_active = True
        self.clipboard_thread = threading.Thread(target=self._clipboard_monitor_loop, daemon=True)
        self.clipboard_thread.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.clipboard_monitoring_active = False
        if self.clipboard_thread.is_alive():
            self.clipboard_thread.join(timeout=0.5) 
        self.root.destroy()

    def _clipboard_monitor_loop(self):
        last_copied_text = ""
        try:
            last_copied_text = pyperclip.paste()
        except pyperclip.PyperclipException:
            print("Clipboard access failed on start. Ensure xclip/xsel is installed on Linux.")
            pass 

        while self.clipboard_monitoring_active:
            try:
                current_clipboard_text = pyperclip.paste()
                if current_clipboard_text and current_clipboard_text != last_copied_text:
                    if self.clipboard_monitoring_active: # Re-check before adding
                        doc_id = str(uuid.uuid4())
                        new_document = Document(id=doc_id, content=current_clipboard_text)
                        try:
                            add_doc(new_document)
                            print(f"Note from clipboard saved with ID: {doc_id}")
                            last_copied_text = current_clipboard_text
                        except Exception as e:
                            print(f"Error saving clipboard note to vector DB: {e}")
            except pyperclip.PyperclipException:
                time.sleep(2) 
                continue
            except Exception as e:
                print(f"Unexpected error in clipboard monitor: {e}")
            time.sleep(1)

    def hide_suggestions_on_click_outside(self, event):
        if event.widget != self.search_entry and event.widget != self.suggestions_listbox:
            if self.suggestions_frame.winfo_ismapped():
                self.suggestions_frame.pack_forget()

    def load_notes(self, query=""):
        found_notes = find_docs(query, k=1 if query else 20) 
        if found_notes:
            if self.current_doc and any(note.id == self.current_doc.id for note in found_notes):
                pass
            else:
                self.current_doc = found_notes[0]
            self.display_note_content(self.current_doc)
        else:
            if not query: 
                self.current_doc = None
                self.text_area.delete("1.0", tk.END)

    def display_note_content(self, doc: Document):
        if doc:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, doc.content)
            self.current_doc = doc 
            self.root.title(f"RAG Notes App - {doc.id[:8]}")
        else:
            self.text_area.delete("1.0", tk.END)
            self.root.title("RAG Notes App")

    def add_note(self, event=None):
        new_id = str(uuid.uuid4())
        new_doc = Document(id=new_id, content="")
        add_doc(new_doc) 
        self.current_doc = new_doc
        self.display_note_content(new_doc)
        self.search_var.set("") 
        self.hide_suggestions()

    def delete_note(self, event=None):
        if not self.current_doc:
            messagebox.showinfo("No note", "No note selected to delete.", parent=self.root)
            return
        if messagebox.askyesno("Delete", f"Are you sure you want to delete this note (ID: {self.current_doc.id[:8]})?", parent=self.root):
            delete_doc(self.current_doc) 
            self.current_doc = None
            self.text_area.delete("1.0", tk.END)
            self.load_notes() 
            self.hide_suggestions()

    def search_notes_action(self, event=None): 
        query = self.search_var.get()
        self.hide_suggestions()
        if query:
            results = find_docs(query, k=1)
            if results:
                self.current_doc = results[0]
                self.display_note_content(self.current_doc)
            else:
                messagebox.showinfo("Search", "No notes found matching your query.", parent=self.root)
        else:
            self.load_notes()

    def schedule_save(self, event=None):
        if event and event.keysym in ("Up", "Down", "Left", "Right", "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R", "BackSpace", "Delete"):
             if event.keysym in ("BackSpace", "Delete") and not self.text_area.get("1.0", tk.END).strip(): # Allow save if all text deleted
                pass
             elif event.keysym in ("BackSpace", "Delete"): # if deleting, proceed to save
                pass
             else: # movement keys, ignore
                return

        if self.save_after_id:
            self.root.after_cancel(self.save_after_id)
        self.save_after_id = self.root.after(1000, self.save_note)

    def save_note(self):
        if self.current_doc:
            new_content = self.text_area.get("1.0", tk.END).strip()
            if new_content != self.current_doc.content:
                self.current_doc.content = new_content
                update_doc(self.current_doc)

    def schedule_search_suggestions(self, event=None):
        if event and event.keysym in ("Return", "Enter"): 
            return 
        if self.search_after_id:
            self.root.after_cancel(self.search_after_id)
        self.search_after_id = self.root.after(400, self._perform_search_suggestions)

    def _perform_search_suggestions(self):
        query = self.search_var.get().strip()
        if not query:
            self.hide_suggestions()
            return

        if not self.suggestions_frame.winfo_ismapped():
            self.suggestions_frame.pack(after=self.search_entry.master, fill=tk.X, padx=20, pady=(0,5))
            self.suggestions_frame.lift()

        self.suggestions_listbox.delete(0, tk.END)
        self.notes_cache.clear()
        
        suggested_docs = find_docs(query, k=5)
        if suggested_docs:
            for doc in suggested_docs:
                preview = doc.content.replace('\n', ' ').strip()
                if len(preview) > 40:
                    preview = preview[:37] + "..."
                else:
                    preview = preview[:40]
                self.suggestions_listbox.insert(tk.END, f"{preview} (ID: {doc.id[:8]})")
                self.notes_cache[self.suggestions_listbox.size() -1] = doc
        else:
            self.hide_suggestions()

    def hide_suggestions(self):
        if self.suggestions_frame.winfo_ismapped():
            self.suggestions_frame.pack_forget()
        self.suggestions_listbox.delete(0, tk.END)

    def on_suggestion_select(self, event=None):
        widget = event.widget
        selection = widget.curselection()
        if selection:
            index = selection[0]
            if index in self.notes_cache:
                selected_doc = self.notes_cache[index]
                self.current_doc = selected_doc
                self.display_note_content(selected_doc)
                self.search_var.set("") 
                self.hide_suggestions()
                self.text_area.focus_set() 

if __name__ == "__main__":
    root = tk.Tk()
    app = NotesApp(root)
    root.mainloop()