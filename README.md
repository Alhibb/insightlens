markdown
# InsightLens ✨

**InsightLens: Interact with your documents using AI. A CLI agent for a post-UI world.**

InsightLens allows you to load documents (PDFs, DOCX, TXT) and then "chat" with them. You can ask questions, get summaries, and explore content through a command-line interface, leveraging the power of Google's Gemini models. It's designed to explore how we might interact with information when traditional UIs become obsolete, focusing on intent interpretation and dynamic, generative experiences.

## Core Features

*   **Document Loading:** Ingest text from PDF, DOCX, and TXT files.
    *   Interactive mode to select files from an `insightlens_inbox/` directory or current path.
*   **Conversational Q&A:** Ask natural language questions about your loaded documents.
    *   Target all loaded documents in a collection.
    *   Target a specific document using `--document <filename>`.
    *   `focus` on a specific document for subsequent questions.
*   **Hierarchical Summarization:** Generate comprehensive summaries of entire documents.
    *   Output summaries to the console, PDF, or DOCX files.
*   **Persistent Memory:**
    *   Document data (embeddings) is stored persistently using ChromaDB.
    *   User configurations and short-term conversation history are saved across sessions.
*   **Question Suggestions:** Get AI-powered suggestions for insightful questions to ask about your documents.
*   **Configurable:** Adjust chunking parameters, retrieval settings, and default collections.
*   **Rich CLI Experience:** Enhanced command-line interface using the `rich` library for better readability and user experience.
*   **Post-UI Focus:** All interactions are command-line driven, avoiding traditional graphical UI elements.

## Setup

1.  **Clone the Repository (or create the file structure):**
    Ensure you have all the project files in a directory named `insightlens`.

2.  **Create a Virtual Environment (Recommended):**
    bash
    cd insightlens
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    

3.  **Install Dependencies:**
    bash
    pip install -r requirements.txt
    

4.  **Set up Gemini API Key:**
    *   Create a file named `.env` in the `insightlens` project root directory.
    *   Add your Google Generative AI API key to it:
        env
        GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
        
    *   You can obtain an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

5.  **Create Inbox Directory (Optional but Recommended for Interactive Load):**
    InsightLens will automatically create an `insightlens_inbox` directory within the project folder. You can place documents here for easy selection when using the interactive `load` command.

## Usage

All commands are run from within the `insightlens` directory in your terminal (with the virtual environment activated).

**General Help:**
bash
python main.py --help


**First Run (Onboarding):**
bash
python main.py

This will display a welcome message and quick start guide.

### Core Commands:

*   **Load a Document:**
    *   Specify a path:
        bash
        python main.py load path/to/your/document.pdf
        
    *   Interactive mode (scans `./insightlens_inbox/` and current directory):
        bash
        python main.py load
        
        Then select the document number from the list.

*   **Ask a Question:**
    *   About the current default collection/focused document:
        bash
        python main.py ask "What is the main argument of the author?"
        
    *   About a specific document:
        bash
        python main.py ask --document "sample_paper.pdf" "What methodology was used?"
        
    *   With a specific persona:
        bash
        python main.py ask --persona "a beginner" "Explain the conclusion simply."
        

*   **Summarize a Document:**
    bash
    python main.py summarize-doc path/to/your/document.pdf
    
    *   Output as PDF:
        bash
        python main.py summarize-doc path/to/document.pdf --output-format pdf
        
    *   Output as DOCX:
        bash
        python main.py summarize-doc path/to/document.pdf --output-format docx
        
    *   Limit chunks processed for summary (for long documents or quick tests):
        bash
        python main.py summarize-doc path/to/document.pdf --max-chunks 10
        

### Utility Commands:

*   **List Loaded Documents:**
    bash
    python main.py list-docs
    python main.py list-docs --collection-name "my_other_collection"
    

*   **Focus on a Specific Document:**
    (Subsequent `ask` commands without `--document` will target this document)
    bash
    python main.py focus "document_filename.pdf"
    
    *   Clear focus:
        bash
        python main.py focus --clear
        

*   **Suggest Questions:**
    *   For a specific document:
        bash
        python main.py suggest-questions --filepath path/to/document.pdf
        
    *   For the current collection/focused document:
        bash
        python main.py suggest-questions --num 5
        

*   **Clear Short-Term Conversation Memory:**
    (Clears the last question and answer used for follow-up context)
    bash
    python main.py clear-memory
    

### Configuration:

*   **View or Update Configuration:**
    bash
    python main.py configure
    python main.py configure --top-k 5 --chunk-size 1500
    python main.py configure --current-collection "project_alpha_docs"
    
    (Configuration is saved in `config.json`)

*   **Reset a Collection:** (Deletes all indexed data for that collection!)
    bash
    python main.py reset-collection your_collection_name
    
    (You will be prompted for confirmation.)

## File Structure


insightlens/
├── .env                    # For API Key (user-created)
├── .gitignore
├── requirements.txt
├── main.py                 # CLI interface and orchestration
├── document_loader.py      # Functions to load and parse documents
├── text_chunker.py         # Logic for splitting text into chunks
├── embedding_generator.py  # Generates embeddings using Gemini
├── vector_store_manager.py # Manages interaction with ChromaDB
├── rag_core.py             # Core RAG logic, prompting, and Gemini calls
├── utils.py                # Utility functions
├── config.json             # Stores persistent app configuration (auto-generated)
├── chroma_db_data/         # Stores ChromaDB persistent data (auto-generated)
└── insightlens_inbox/      # Default directory for interactive document loading (auto-generated)


## Future Ideas (Post-UI Exploration)

*   **Audio Interaction:** Integrate Speech-to-Text and Text-to-Speech for voice commands and spoken responses.
*   **Proactive Agent:** Have InsightLens proactively suggest insights or related documents based on usage patterns or newly loaded content.
*   **Dynamic Visual Elements (Non-UI):** If a display is available, generate simple, abstract visualizations related to the content being discussed (e.g., concept maps, timelines) rather than traditional charts.
*   **Watched Folder Agent:** A background process that automatically ingests new documents added to a specific folder.

## Contributing

This project is currently designed as a conceptual exploration. Contributions focusing on enhancing the non-traditional UI aspects and core AI agent capabilities are welcome.

## License

This project is open-source (e.g., MIT License - specify if you have one).

