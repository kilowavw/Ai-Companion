import keyboard
import pyperclip
import time
import tkinter as tk
from google import genai
from google.genai import types 
import os
import threading

# run ini di cmd: pip install google-genai pyperclip keyboard
# --- Configuration: HARDCODED API KEY ---
GEMINI_API_KEY = "" # <--isi pake gemini key sendiri ambil dari https://aistudio.google.com/api-keys

# Initialize client globally
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("Gemini Client Initialized successfully.")
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        client = None

# --- Global Tkinter Root ---
try:
    ROOT = tk.Tk()
    ROOT.withdraw()
except Exception as e:
    ROOT = None

# --- CONSTANTS for Aesthetics ---
# New background color (light blue/gray)
BG_COLOR = "#F5F9FD" 
FG_COLOR = "#000000"  
BUTTON_BG = "#E8ECF0" # Light gray for button background
CLOSE_BUTTON_HOVER_BG = "#D3D7DB" # Slightly darker for hover
BORDER_COLOR = "#C0C0C0" # Border color for the custom window

# --- Resizing Globals ---
# To store the initial position of the mouse during resizing
resize_data = {'x': 0, 'y': 0, 'w': 0, 'h': 0}


# --- 1. AI Core (with Plain Text Instruction) ---
def get_ai_response(user_text):
    if not client:
        return "ERROR: Gemini AI service not available. Please check your API key."

    system_instruction = (
        "You are a quick, concise, and helpful context-aware assistant. "
        "The user has highlighted a text snippet or a question. "
        "Provide a brief, direct, and well-structured answer (max 3-4 sentences). "
        "CRITICAL: DO NOT use Markdown, LaTeX, or any mathematical formatting. "
        "Use plain, easily readable text for all symbols (e.g., use 'x^2' instead of '$x^2$' or 'x**2')."
    )
    
    try:
        print(f"Fetching response for: {user_text[:40]}...")
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[user_text],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"An error occurred during AI generation: {e}"


# --- 2. GUI Helper Functions ---

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
    """Makes a window draggable using a specific widget (e.g., title bar)."""
    
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
    """Makes the window resizable using a specific widget (e.g., resize handle)."""
    
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


# --- 3. AI Answer Window (Resizable) ---

def show_popup_window(answer_text):
    
    if ROOT is None:
        return
        
    popup = tk.Toplevel(ROOT)
    popup.title("AI Quick Answer")
    
    # Custom Border and Styling
    popup.overrideredirect(True) 
    popup.attributes('-topmost', True) 
    popup.configure(bg=BG_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
    
    # Frame for content and drag handle
    main_frame = tk.Frame(popup, bg=BG_COLOR)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Custom Title Bar
    title_frame = tk.Frame(main_frame, bg=BG_COLOR, height=25)
    title_frame.pack(fill=tk.X)
    
    create_close_button(title_frame, popup.destroy)
    setup_draggable(popup, title_frame) # Make draggable by title bar
    
    model_label = tk.Label(title_frame, text="Windows 11", bg=BG_COLOR, fg="#555555", font=("Arial", 8))
    model_label.pack(side=tk.LEFT, padx=5)

    # Content Widget
    text_widget = tk.Text(main_frame, wrap=tk.WORD, font=("Arial", 11), 
                          bg=BG_COLOR, fg=FG_COLOR, bd=0, 
                          padx=10, pady=5)
    
    lines = answer_text.count('\n') + 1
    height = min(max(lines * 20 + 70, 150), 450)
    width = 400
    popup.geometry(f"{width}x{height}")
    
    text_widget.insert(tk.END, answer_text)
    text_widget.config(state=tk.DISABLED)
    text_widget.pack(expand=True, fill=tk.BOTH, padx=(0, 10)) # Right padding for handle area

    # Resizing Handle (Small triangle in the corner)
    resize_handle = tk.Label(main_frame, text="", bg=BG_COLOR, cursor="sizing")
    resize_handle.place(relx=1.0, rely=1.0, anchor='se', width=10, height=10)
    setup_resizable(popup, resize_handle) # Make resizable by handle

    # Positioning (Bottom Right)
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    x = screen_width - width - 50 
    y = screen_height - height - 50 
    popup.geometry(f'+{x}+{y}')
    
    popup.bind('<Escape>', lambda e: popup.destroy())
    popup.focus_force()


# --- 4. Manual Input Window (Smaller Size + Custom Border) ---

def show_manual_input_window():
    if ROOT is None:
        return

    manual_popup = tk.Toplevel(ROOT)
    manual_popup.title("Manual AI Query (F8)")
    
    WINDOW_WIDTH = 350
    WINDOW_HEIGHT = 220
    
    # Custom Border and Styling
    manual_popup.overrideredirect(True) 
    manual_popup.attributes('-topmost', True)
    manual_popup.configure(bg=BG_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
    manual_popup.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

    # Custom Title Bar
    title_frame = tk.Frame(manual_popup, bg=BG_COLOR, height=25)
    title_frame.pack(fill=tk.X)
    
    create_close_button(title_frame, manual_popup.destroy)
    setup_draggable(manual_popup, title_frame) # Make draggable
    
    title_label = tk.Label(title_frame, text="Manual Query", bg=BG_COLOR, fg=FG_COLOR, font=("Arial", 10, "bold"))
    title_label.pack(side=tk.LEFT, padx=5)

    # Input Text Area
    input_text = tk.Text(manual_popup, wrap=tk.WORD, font=("Arial", 11),
                         bg="#F0F0F0", fg=FG_COLOR, bd=1, relief=tk.FLAT, padx=5, pady=5)
    input_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

    # Submit Button Action
    def submit_query():
        query = input_text.get("1.0", tk.END).strip()
        manual_popup.destroy() 
        if query:
            t = threading.Thread(target=run_ai_and_show_gui, args=(query,))
            t.daemon = True
            t.start()

    # Submit Button
    submit_button = tk.Button(manual_popup, text="Ask AI", command=submit_query, 
                              bg=BUTTON_BG, fg=FG_COLOR, font=("Arial", 10, "bold"))
    submit_button.pack(pady=(0, 10))

    manual_popup.bind('<Return>', lambda e: submit_query())
    manual_popup.bind('<Escape>', lambda e: manual_popup.destroy())
    
    # Positioning (Center of screen)
    screen_width = manual_popup.winfo_screenwidth()
    screen_height = manual_popup.winfo_screenheight()
    x = (screen_width / 2) - (WINDOW_WIDTH / 2)
    y = (screen_height / 2) - (WINDOW_HEIGHT / 2)
    manual_popup.geometry(f'+{int(x)}+{int(y)}')
    
    manual_popup.focus_force()


# --- 5. Listener/HotKey Logic (Unchanged) ---

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


# --- 6. Running the Application ---
def start_listener():
    keyboard.add_hotkey('f9', process_f9_highlighted)
    keyboard.add_hotkey('f8', process_f8_manual)
    keyboard.wait()

if __name__ == "__main__":
    
    print(f"--- AI Quick Look App Started ---")
    print(f"F9: Get answer from highlighted (requires Ctrl+C first).")
    print(f"F8: Open manual input window.")
    
    listener_thread = threading.Thread(target=start_listener)
    listener_thread.daemon = True
    listener_thread.start()
    
    print("Press Ctrl+C in this console to stop the service.")
    
    if ROOT:
        ROOT.mainloop()

#baca dulu tutorial di atas