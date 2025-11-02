import keyboard
import pyperclip
import time
import tkinter as tk
from google import genai
from google.genai import types 
import os
import threading
import configparser 

# --- CONFIGURATION FILE SETUP ---
CONFIG_FILE = 'config.ini'

# --- CONSTANTS for Aesthetics ---
BG_COLOR = "#F5F9FD" 
FG_COLOR = "#000000"  
BUTTON_BG = "#E8ECF0" 
CLOSE_BUTTON_HOVER_BG = "#D3D7DB"
BORDER_COLOR = "#C0C0C0" 

# --- Global Initialization ---
client = None
ROOT = None
GEMINI_API_KEY = None
# Default window size
DEFAULT_WIN_W = 400
DEFAULT_WIN_H = 300 
current_win_w = DEFAULT_WIN_W
current_win_h = DEFAULT_WIN_H


# --- 1. GUI HELPER FUNCTIONS (MOVED TO TOP) ---

resize_data = {'x': 0, 'y': 0, 'w': 0, 'h': 0}

def create_close_button(parent_window, window_destroy_func):
    """Creates a custom 'X' button in the top right corner."""
    
    close_btn = tk.Label(parent_window, text="  ✕  ", bg=BG_COLOR, fg=FG_COLOR, 
                         font=("Arial", 9, "bold"), cursor="hand2")
    
    close_btn.pack(pady=0, padx=0, side=tk.RIGHT)
    close_btn.bind("<Button-1>", lambda e: window_destroy_func())
    
    def on_enter(e):
        close_btn.config(bg=CLOSE_BUTTON_HOVER_BG)
    
    def on_leave(e):
        close_btn.config(bg=BG_COLOR)
        
    close_btn.bind("<Enter>", on_enter)
    close_btn.bind("<Leave>", on_leave)
    return close_btn

def setup_draggable(window, drag_widget):
    """Makes a window draggable using a specific widget."""
    def start_move(event):
        window.x = event.x
        window.y = event.y
    def stop_move(event):
        window.x = None
        window.y = None
    def do_move(event):
        if window.x is not None and window.y is not None:
            deltax = event.x - window.x
            deltay = event.y - window.y
            x = window.winfo_x() + deltax
            y = window.winfo_y() + deltay
            window.geometry(f"+{x}+{y}")
    drag_widget.bind("<ButtonPress-1>", start_move)
    drag_widget.bind("<ButtonRelease-1>", stop_move)
    drag_widget.bind("<B1-Motion>", do_move)

def setup_resizable(window, resize_widget, min_w=200, min_h=150):
    """Makes the window resizable using a specific widget."""
    
    def start_resize(event):
        resize_data['x'] = event.x
        resize_data['y'] = event.y
        resize_data['w'] = window.winfo_width()
        resize_data['h'] = window.winfo_height()

    def do_resize(event):
        deltax = event.x - resize_data['x']
        deltay = event.y - resize_data['y']
        
        new_w = max(min_w, resize_data['w'] + deltax)
        new_h = max(min_h, resize_data['h'] + deltay)
        
        window.geometry(f"{new_w}x{new_h}")

    resize_widget.bind("<ButtonPress-1>", start_resize)
    resize_widget.bind("<B1-Motion>", do_resize)

def create_copy_button(parent_frame, text_widget):
    """Creates a 'Copy' button that copies the content of the text widget."""
    
    def copy_text():
        text_widget.config(state=tk.NORMAL)
        content = text_widget.get("1.0", tk.END).strip()
        pyperclip.copy(content)
        text_widget.config(state=tk.DISABLED)
        print("Answer copied to clipboard.")

    copy_btn = tk.Button(parent_frame, text="Copy", command=copy_text, 
                         bg=BUTTON_BG, fg=FG_COLOR, relief=tk.FLAT, 
                         font=("Arial", 9))
    copy_btn.pack(side=tk.RIGHT, padx=5)
    return copy_btn


# --- 2. CONFIGURATION MANAGEMENT ---

def load_config():
    """Loads API key and window size from config.ini."""
    global current_win_w, current_win_h
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    
    key = None
    if 'AI_CONFIG' in config and 'api_key' in config['AI_CONFIG']:
        key = config['AI_CONFIG']['api_key']

    if 'WINDOW_CONFIG' in config:
        try:
            current_win_w = int(config['WINDOW_CONFIG'].get('width', DEFAULT_WIN_W))
            current_win_h = int(config['WINDOW_CONFIG'].get('height', DEFAULT_WIN_H))
        except ValueError:
            pass # Use defaults if values are invalid
            
    return key

def save_config(key, width=None, height=None):
    """Saves API key and window size to config.ini."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE) # Read existing config if present

    if 'AI_CONFIG' not in config:
        config['AI_CONFIG'] = {}
    if key is not None:
        config['AI_CONFIG']['api_key'] = key
        
    if 'WINDOW_CONFIG' not in config:
        config['WINDOW_CONFIG'] = {}
        
    if width is not None:
        config['WINDOW_CONFIG']['width'] = str(width)
    if height is not None:
        config['WINDOW_CONFIG']['height'] = str(height)
    
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


# --- 3. API INITIALIZATION (Adapted for new config functions) ---

def initialize_gemini_client(key):
    global client
    try:
        if key:
            client = genai.Client(api_key=key)
            print("Gemini Client Initialized successfully.")
            return True
        return False
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        client = None
        return False

def show_api_input_window():
    # ... (Implementation is the same as previous version, calling save_config)
    global GEMINI_API_KEY, client

    input_root = tk.Tk()
    input_root.title("API Key Required")
    input_root.geometry("450x180")
    input_root.attributes('-topmost', True) 
    
    screen_width = input_root.winfo_screenwidth()
    screen_height = input_root.winfo_screenheight()
    x = (screen_width / 2) - (450 / 2)
    y = (screen_height / 2) - (180 / 2)
    input_root.geometry(f'+{int(x)}+{int(y)}')
    
    tk.Label(input_root, text="Please enter your Gemini API Key:", font=("Arial", 10)).pack(pady=10)
    
    api_entry = tk.Entry(input_root, width=50, font=("Arial", 10))
    api_entry.pack(padx=20, pady=5)
    
    status_label = tk.Label(input_root, text="", fg="red")
    status_label.pack()

    def submit_key():
        key = api_entry.get().strip()
        if initialize_gemini_client(key):
            save_config(key=key) # Save key
            GEMINI_API_KEY = key
            input_root.destroy()
        else:
            status_label.config(text="Invalid or failed to connect. Try again.")

    submit_button = tk.Button(input_root, text="Submit and Start", command=submit_key)
    submit_button.pack(pady=10)

    input_root.mainloop()


def check_and_set_api():
    global GEMINI_API_KEY
    
    # Load key and window config
    key = load_config()
    
    if key and initialize_gemini_client(key):
        GEMINI_API_KEY = key
        return True

    show_api_input_window()
    return client is not None


# --- 4. AI Core (Unchanged) ---
def get_ai_response(user_text):
    if not client:
        return "ERROR: Gemini AI service not available."
    
    system_instruction = ("You are a quick, concise, and helpful context-aware assistant. ... [CRITICAL: DO NOT use Markdown, LaTeX, or any mathematical formatting.]")
    try:
        print(f"Fetching response for: {user_text[:40]}...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[user_text],
            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2)
        )
        return response.text.strip()
    except Exception as e:
        return f"An error occurred during AI generation: {e}"


# --- 5. GUI WINDOWS (Updated to handle saved size) ---

def save_current_window_size(window):
    """Saves the current dimensions of the window."""
    global current_win_w, current_win_h
    # Get geometry string (e.g., '400x300+100+100')
    geometry = window.geometry()
    width_height = geometry.split('+')[0]
    w, h = map(int, width_height.split('x'))
    
    current_win_w = w
    current_win_h = h
    save_config(key=GEMINI_API_KEY, width=w, height=h)


def show_popup_window(answer_text):
    """Creates and displays the AI answer window (Uses saved size)."""
    global current_win_w, current_win_h

    if ROOT is None: return
        
    popup = tk.Toplevel(ROOT)
    popup.title("AI Quick Answer")
    
    popup.overrideredirect(True) 
    popup.attributes('-topmost', True) 
    popup.configure(bg=BG_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
    
    # Set window size from persistent configuration
    popup.geometry(f"{current_win_w}x{current_win_h}")
    
    # ... (Rest of UI setup)
    main_frame = tk.Frame(popup, bg=BG_COLOR)
    main_frame.pack(fill=tk.BOTH, expand=True)

    title_frame = tk.Frame(main_frame, bg=BG_COLOR, height=25)
    title_frame.pack(fill=tk.X)
    
    # Bind save size function to window close event
    def close_and_save():
        save_current_window_size(popup)
        popup.destroy()

    create_close_button(title_frame, close_and_save) # Use the new close function
    setup_draggable(popup, title_frame) 
    
    text_widget = tk.Text(main_frame, wrap=tk.WORD, font=("Arial", 11), 
                          bg=BG_COLOR, fg=FG_COLOR, bd=0, 
                          padx=10, pady=5)

    create_copy_button(title_frame, text_widget)
    
    model_label = tk.Label(title_frame, text="Windows Quick Look", bg=BG_COLOR, fg="#555555", font=("Arial", 8))
    model_label.pack(side=tk.LEFT, padx=5)

    text_widget.insert(tk.END, answer_text)
    text_widget.config(state=tk.DISABLED)
    text_widget.pack(expand=True, fill=tk.BOTH, padx=(0, 10))

    # Resizing Handle
    resize_handle = tk.Label(main_frame, text="", bg=BG_COLOR, cursor="sizing")
    resize_handle.place(relx=1.0, rely=1.0, anchor='se', width=10, height=10)
    setup_resizable(popup, resize_handle) 

    # Positioning (Bottom Right - initial position)
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    x = screen_width - current_win_w - 50 
    y = screen_height - current_win_h - 50 
    popup.geometry(f'+{x}+{y}')
    
    popup.bind('<Escape>', lambda e: close_and_save()) # Bind ESC to save and close
    popup.focus_force()

# --- 6. Manual Input Window (Unchanged functionality) ---
def show_manual_input_window():
    # ... (Implementation same as previous version)
    if ROOT is None: return

    manual_popup = tk.Toplevel(ROOT)
    # ... (rest of the manual popup setup)
    
    WINDOW_WIDTH = 350
    WINDOW_HEIGHT = 220
    manual_popup.overrideredirect(True) 
    manual_popup.attributes('-topmost', True)
    manual_popup.configure(bg=BG_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
    manual_popup.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

    # Custom Title Bar Setup (for dragging)
    title_frame = tk.Frame(manual_popup, bg=BG_COLOR, height=25)
    title_frame.pack(fill=tk.X)
    create_close_button(title_frame, manual_popup.destroy)
    setup_draggable(manual_popup, title_frame) 
    
    title_label = tk.Label(title_frame, text="Manual Query", bg=BG_COLOR, fg=FG_COLOR, font=("Arial", 10, "bold"))
    title_label.pack(side=tk.LEFT, padx=5)

    input_text = tk.Text(manual_popup, wrap=tk.WORD, font=("Arial", 11),
                         bg="#F0F0F0", fg=FG_COLOR, bd=1, relief=tk.FLAT, padx=5, pady=5)
    input_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

    def submit_query():
        query = input_text.get("1.0", tk.END).strip()
        manual_popup.destroy() 
        if query:
            t = threading.Thread(target=run_ai_and_show_gui, args=(query,))
            t.daemon = True
            t.start()

    submit_button = tk.Button(manual_popup, text="Ask AI", command=submit_query, 
                              bg=BUTTON_BG, fg=FG_COLOR, font=("Arial", 10, "bold"))
    submit_button.pack(pady=(0, 10))

    manual_popup.bind('<Return>', lambda e: submit_query())
    manual_popup.bind('<Escape>', lambda e: manual_popup.destroy())
    
    screen_width = manual_popup.winfo_screenwidth()
    screen_height = manual_popup.winfo_screenheight()
    x = (screen_width / 2) - (WINDOW_WIDTH / 2)
    y = (screen_height / 2) - (WINDOW_HEIGHT / 2)
    manual_popup.geometry(f'+{int(x)}+{int(y)}')
    manual_popup.focus_force()


# --- 7. Listener/HotKey Logic (Unchanged) ---
def get_highlighted_text():
    time.sleep(0.01)
    text = pyperclip.paste()
    return text.strip()

def run_ai_and_show_gui(prompt_text):
    if not prompt_text:
        ai_answer = "Error: Query was empty. Please highlight text or enter a query."
    else:
        ai_answer = get_ai_response(prompt_text)
    
    if ROOT:
        ROOT.after(0, lambda: show_popup_window(ai_answer))

def process_f9_highlighted():
    prompt_text = get_highlighted_text()
    print("F9 triggered. Checking clipboard...")
    
    t = threading.Thread(target=run_ai_and_show_gui, args=(prompt_text,))
    t.daemon = True 
    t.start()

def process_f8_manual():
    print("F8 triggered. Opening manual input window.")
    if ROOT:
        ROOT.after(0, show_manual_input_window)


# --- 8. Running the Application ---
def start_listener():
    keyboard.add_hotkey('f9', process_f9_highlighted)
    keyboard.add_hotkey('f8', process_f8_manual)
    keyboard.wait()

if __name__ == "__main__":
    
    # 1. Check/Setup API Key
    if not check_and_set_api():
        exit()

    # 2. Initialize Main Tkinter Root (Must happen AFTER API Check)
    try:
        ROOT = tk.Tk()
        ROOT.withdraw()
    except Exception as e:
        print(f"Main Tkinter root initialization failed: {e}")
        exit()

    print(f"--- AI Quick Look App Started ---")
    
    # 3. Start the keyboard listener
    listener_thread = threading.Thread(target=start_listener)
    listener_thread.daemon = True
    listener_thread.start()
    
    print("Press Ctrl+C in this console to stop the service.")
    
    # 4. Run the main Tkinter loop
    if ROOT:
        ROOT.mainloop()

