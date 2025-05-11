import customtkinter as ctk
from tkinter import messagebox
from vect_db import find_docs, add_doc, delete_doc, update_doc # Ensure this is the updated vect_db
from document import Document
import uuid
import threading
import time
import pyperclip

import styles 

ctk.set_appearance_mode(styles.APPEARANCE_MODE)
ctk.set_default_color_theme(styles.DEFAULT_COLOR_THEME)

# Define a similarity threshold for suggestions (0.0 to 1.0)
# Higher means more similar. 0.35 is a starting point, adjust as needed.
SIMILARITY_THRESHOLD_SUGGESTIONS = 0.35


class NotesApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.configure(fg_color=styles.COLOR_PALETTE["app_bg"])
        self.title("RAG Notes App")
        self.geometry("700x750")

        top_frame = ctk.CTkFrame(self, **styles.TOP_FRAME_STYLE)
        top_frame.pack(side=ctk.TOP, fill=ctk.X, padx=10, pady=(10, 0))

        self.copy_icon_label = ctk.CTkLabel(top_frame, text="📋", cursor="hand2", **styles.ICON_LABEL_STYLE)
        self.copy_icon_label.pack(side=ctk.LEFT, padx=(10, 10), pady=5)
        self.copy_icon_label.bind("<Button-1>", self.copy_note_content)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(top_frame, textvariable=self.search_var, placeholder_text="Search notes...", **styles.SEARCH_ENTRY_STYLE)
        self.search_entry.pack(side=ctk.LEFT, expand=True, fill=ctk.X, padx=0, pady=5)
        self.search_entry.bind("<Return>", self.search_notes_action)
        self.search_entry.bind("<KeyRelease>", self.schedule_search_suggestions)

        self.add_icon_label = ctk.CTkLabel(top_frame, text="＋", cursor="hand2", **styles.ICON_LABEL_STYLE)
        self.add_icon_label.pack(side=ctk.RIGHT, padx=(10, 10), pady=5)
        self.add_icon_label.bind("<Button-1>", self.add_note)
        
        self.suggestions_scroll_frame = ctk.CTkScrollableFrame(self, **styles.SUGGESTIONS_SCROLL_FRAME_STYLE)
        
        self.text_area = ctk.CTkTextbox(self, **styles.TEXT_AREA_STYLE)
        self.text_area.pack(expand=True, fill=ctk.BOTH, padx=10, pady=10)

        self.current_doc = None
        self.was_just_deleted_by_emptying = False

        self.load_notes()
        self.text_area.bind("<KeyRelease>", self.schedule_save)
        self.save_after_id = None
        self.search_after_id = None
        self.bind_all("<Button-1>", self.hide_suggestions_on_click_outside, add="+")
        self.clipboard_monitoring_active = True
        self.internal_copy_active = False
        self.clipboard_thread = threading.Thread(target=self._clipboard_monitor_loop, daemon=True)
        self.clipboard_thread.start()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.clipboard_monitoring_active = False
        if self.clipboard_thread.is_alive():
            self.clipboard_thread.join(timeout=0.5) 
        self.destroy()

    def copy_note_content(self, event=None):
        if self.current_doc and self.text_area.get("1.0", ctk.END).strip():
            current_text_content = self.text_area.get("1.0", ctk.END).strip()
            try:
                self.internal_copy_active = True 
                pyperclip.copy(current_text_content)
                print("Note content copied to clipboard.")
            except pyperclip.PyperclipException as e:
                print(f"Error: Could not copy note content to clipboard: {repr(e)}")
                messagebox.showerror("Copy Error", "Could not copy to clipboard.", parent=self)
            except Exception as e:
                print(f"Error: Unexpected error during copy_note_content: {repr(e)}")
        else:
            print("No current note or note is empty, nothing to copy.")

    def _clipboard_monitor_loop(self):
        last_copied_text_processed_by_monitor = ""
        try:
            last_copied_text_processed_by_monitor = pyperclip.paste()
        except pyperclip.PyperclipException:
            pass 
        while self.clipboard_monitoring_active:
            try:
                current_clipboard_text = pyperclip.paste()
                if current_clipboard_text and current_clipboard_text != last_copied_text_processed_by_monitor:
                    if self.internal_copy_active:
                        self.internal_copy_active = False 
                        last_copied_text_processed_by_monitor = current_clipboard_text 
                        time.sleep(0.1) 
                        continue 
                    if self.clipboard_monitoring_active: 
                        doc_id = str(uuid.uuid4())
                        new_document = Document(id=doc_id, content=current_clipboard_text)
                        try:
                            add_doc(new_document)
                            print(f"Saved note from clipboard with ID: {doc_id[:8]}")
                            last_copied_text_processed_by_monitor = current_clipboard_text
                        except Exception as e:
                            error_message = repr(e) 
                            print(f"Error saving clipboard note to vector DB: {error_message}")
                elif not current_clipboard_text and last_copied_text_processed_by_monitor:
                    last_copied_text_processed_by_monitor = ""
            except pyperclip.PyperclipException:
                time.sleep(2) 
                continue
            except Exception as e:
                print(f"Error: Unexpected error in clipboard monitor: {repr(e)}")
            time.sleep(1)

    def hide_suggestions_on_click_outside(self, event):
        if event.widget != self.search_entry:
            is_in_suggestions = False
            if self.suggestions_scroll_frame.winfo_ismapped():
                try:
                    if event.widget.winfo_ismapped() and self.suggestions_scroll_frame.winfo_containing(event.x_root, event.y_root) == self.suggestions_scroll_frame:
                         is_in_suggestions = True
                except Exception:
                    pass
            if not is_in_suggestions and self.suggestions_scroll_frame.winfo_ismapped():
                 self.hide_suggestions()

    def load_notes(self, query=""):
        self.was_just_deleted_by_emptying = False
        # For general loading or non-suggestion search, threshold is not applied strictly or is 0
        found_notes = find_docs(query, k=1 if query else 20, min_similarity_threshold=0.0) 
        if found_notes:
            if self.current_doc and any(note.id == self.current_doc.id for note in found_notes):
                 self.display_note_content(self.current_doc)
            else:
                self.current_doc = found_notes[0]
                self.display_note_content(self.current_doc)
        else:
            self.display_note_content(None)

    def display_note_content(self, doc: Document):
        self.text_area.delete("1.0", ctk.END)
        if doc:
            self.text_area.insert(ctk.END, doc.content)
            self.current_doc = doc 
            self.title(f"RAG Notes App - {doc.id[:8]}")
        else:
            self.current_doc = None
            self.title("RAG Notes App")

    def add_note(self, event=None):
        new_id = str(uuid.uuid4())
        new_doc = Document(id=new_id, content="")
        add_doc(new_doc) 
        self.current_doc = new_doc
        self.display_note_content(new_doc)
        self.search_var.set("") 
        self.hide_suggestions()
        self.text_area.focus_set()
        self.was_just_deleted_by_emptying = False

    def search_notes_action(self, event=None): 
        query = self.search_var.get()
        self.hide_suggestions()
        if query:
            # For direct search action, always get the top result, no threshold.
            results = find_docs(query, k=1, min_similarity_threshold=0.0) 
            if results:
                self.current_doc = results[0]
                self.display_note_content(self.current_doc)
                self.was_just_deleted_by_emptying = False
            else:
                messagebox.showinfo("Search", "No notes found matching your query.", parent=self)
        else:
            self.load_notes()

    def schedule_save(self, event=None):
        if self.was_just_deleted_by_emptying:
            self.was_just_deleted_by_emptying = False
            return
        if event and event.keysym in ("Up", "Down", "Left", "Right", "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"):
            if not (event.keysym in ("BackSpace", "Delete")): 
                 return
        if self.save_after_id:
            self.after_cancel(self.save_after_id)
        self.save_after_id = self.after(1000, self.save_note)

    def save_note(self):
        if self.was_just_deleted_by_emptying:
            self.was_just_deleted_by_emptying = False
            return

        if self.current_doc:
            original_content_on_focus = self.current_doc.content
            new_content = self.text_area.get("1.0", ctk.END).strip()

            if not new_content and original_content_on_focus:
                doc_to_delete = self.current_doc
                self.current_doc = None 
                self.text_area.delete("1.0", ctk.END)
                delete_doc(doc_to_delete)
                print(f"Note {doc_to_delete.id[:8]} deleted due to being empty.")
                self.was_just_deleted_by_emptying = True
                self.load_notes(self.search_var.get())
            elif new_content != original_content_on_focus:
                self.current_doc.content = new_content
                update_doc(self.current_doc)
                print(f"Note {self.current_doc.id[:8]} saved.")
        
    def schedule_search_suggestions(self, event=None):
        if event and event.keysym in ("Return", "Enter", "Up", "Down"): 
            return 
        if self.search_after_id:
            self.after_cancel(self.search_after_id)
        self.search_after_id = self.after(400, self._perform_search_suggestions)

    def _clear_suggestions_widgets(self):
        for widget in self.suggestions_scroll_frame.winfo_children():
            widget.destroy()

    def _perform_search_suggestions(self):
        query = self.search_var.get().strip()
        self._clear_suggestions_widgets()

        if not query:
            self.hide_suggestions()
            return

        if not self.suggestions_scroll_frame.winfo_ismapped():
            self.suggestions_scroll_frame.pack(after=self.search_entry.master, fill=ctk.X, padx=10, pady=(2,5),ipady=0)
            self.suggestions_scroll_frame.lift()
        
        # Use the SIMILARITY_THRESHOLD_SUGGESTIONS for suggestions
        suggested_docs = find_docs(query, k=5, min_similarity_threshold=SIMILARITY_THRESHOLD_SUGGESTIONS)
        
        if suggested_docs:
            for doc in suggested_docs:
                preview = doc.content.replace('\n', ' ').strip()
                if len(preview) > 70: 
                    preview = preview[:67] + "..."
                else:
                    preview = preview[:70]
                
                suggestion_button = ctk.CTkButton(
                    self.suggestions_scroll_frame,
                    text=preview,
                    command=lambda d=doc: self.select_suggestion(d),
                    **styles.SUGGESTION_BUTTON_STYLE
                )
                suggestion_button.pack(fill=ctk.X, pady=(3,0), padx=3)
        else:
            # If find_docs returns empty (e.g., even top result was filtered, though current logic prevents this for k>=1)
            # or no docs found at all.
            self.hide_suggestions()


    def hide_suggestions(self):
        if self.suggestions_scroll_frame.winfo_ismapped():
            self.suggestions_scroll_frame.pack_forget()
        self._clear_suggestions_widgets()

    def select_suggestion(self, doc: Document):
        self.current_doc = doc
        self.display_note_content(doc)
        self.search_var.set("") 
        self.hide_suggestions()
        self.text_area.focus_set()
        self.was_just_deleted_by_emptying = False

if __name__ == "__main__":
    app = NotesApp()
    app.mainloop()