# RAG Notes

A solution to organize notes using Vector Databases offline.

You'll get downloaded from huggingface the `BGEM3FlagModel`, but you may choose between the ones supported by `FlagEmbedding` to embed the files into the database

## Project Structure

The RAG Notes App is organized into the following directory structure:

```
RAG Notes
├── .git
├── .gitignore
├── LICENSE
├── __pycache__
├── app.py
├── document.py
├── embedding.py
├── requirements.txt
├── styles.py
└── vect_db.py
```

### Important Files

- **app.py**: The main application file that initializes the GUI and manages user interaction.
- **document.py**: Contains the `Document` class for note representation and methods for file handling.
- **embedding.py**: Handles the embedding of text using the `BGEM3FlagModel` for document similarity.
- **vect_db.py**: Manages the vector database for storing, retrieving, and manipulating documents.
- **styles.py**: Defines visual styles and configurations for the application components.
- **requirements.txt**: Lists Python package dependencies required to run the application.

## Installation

To install the required dependencies, create a virtual environment and run:

```bash
pip install -r requirements.txt
```

## Usage

To run the application, execute:

```bash
python app.py
```

## Features

- **Note Management**: Create, delete, and update notes.
- **Search Functionality**: Search for notes with auto-suggestions based on user input.
- **Clipboard Monitoring**: Automatically detect and save text copied to the clipboard as new notes.
- **Local Document Embedding**: Utilize the `BGEM3FlagModel` for semantic similarity between notes.
- **Easy to implement a LLM**: the `vect_db.py` allows CRUD operations quickly and stable

## Classes and Functions

### Document Class

```python
class Document:
    def __init__(self, id: str, content: str):
        self.id = id
        self.content = content

    def to_file(self, file_path: str):
        ...
```

- **Attributes**:
  - `id`: Unique identifier for the document.
  - `content`: Text content of the document.

- **Methods**:
  - `to_file(file_path)`: Saves the document content to a specified file.

### Functions in vect_db.py

- **add_doc(doc: Document) -> None**: Adds a document to the vector database and updates the embeddings.
- **delete_doc(doc_to_delete: Document) -> None**: Deletes a specific document from the database.
- **update_doc(doc: Document) -> None**: Updates an existing document in the database.
- **find_docs(query: str, k: int, min_similarity_threshold: float) -> List[Document]**: Retrieves documents matching a query based on semantic similarity.

### GUI Components

#### Main Application Class: NotesApp

```python
class NotesApp(ctk.CTk):
    ...
```
- **Initialization**: Configures the main window, initializes GUI elements, and starts clipboard monitoring.

- **Methods**:
  - `copy_note_content()`: Copies the current note content to the clipboard.
  - `load_notes(query="")`: Loads notes based on a search query.
  - `add_note(event=None)`: Handles note creation events.
  - `search_notes_action(event=None)`: Executes search operations and displays the results.

### Styles Configuration

The `styles.py` file manages the theme and user interface styling, including color palettes, fonts, and widget styles. Key styles include:

- **COLOR_PALETTE**: A dictionary that defines colors used throughout the application.
- **APPEARANCE_MODE & DEFAULT_COLOR_THEME**: Define the initial appearance settings.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- **CustomTkinter**: A modern Tkinter wrapper used for better UI flexibility.
- **BGEM3FlagModel**: Used for obtaining document embeddings.
