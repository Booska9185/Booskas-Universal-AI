from PyQt6.QtCore import Qt, QTimer
import win32gui
import os

def setup(core):
    """
    Universal Window & Audio Engine:
    1. Handles native window focus settings.
    2. Keeps game audio alive using passive frame-painting messages.
    3. Restores inline rendering strictly for user gameplay screenshots.
    """
    try:
        # --- 1. NATIVE WINDOW FOCUS SETUP ---
        core.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        core.show()

        core.input_box.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        core.chat_display.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        core.input_box.setPlaceholderText("Click here and type to talk to AI...")

        # --- 2. SIGNAL OVERRIDE (Empty-text submission fix) ---
        try:
            core.input_box.returnPressed.disconnect()
        except TypeError:
            pass

        def smart_input_submission():
            text = core.input_box.text().strip()
            if text or core.attached_screenshot_path:
                core.send_to_ai()

        core.input_box.returnPressed.connect(smart_input_submission)

        # --- 3. USER SCREENSHOT DISPLAY HOOK ---
        # This only renders gameplay captures you send to Gemini (NPC portraits stay in npc_manager)
        def render_inline_image_hook(text):
            if core.attached_screenshot_path and os.path.exists(core.attached_screenshot_path):
                web_path = core.attached_screenshot_path.replace("\\", "/")
                img_html = f"<br><br><img src='{web_path}' width='220'><br>"
                if text.strip():
                    return f"{text} {img_html}"
                else:
                    return f"[Attached Image] {img_html}"
            return text

        core.hooks_pre_send.append(render_inline_image_hook)

        # --- 4. STABILIZED AUDIO KEEP-ALIVE ---
        core.last_game_hwnd = None

        def keep_game_audio_alive():
            try:
                current_fg = win32gui.GetForegroundWindow()
                overlay_hwnd = int(core.winId())
                
                if current_fg and current_fg != overlay_hwnd:
                    core.last_game_hwnd = current_fg
                elif core.last_game_hwnd:
                    # 134 = WM_NCACTIVATE (paints frame active without moving cursor)
                    win32gui.SendMessageTimeout(core.last_game_hwnd, 134, 1, 0, 2, 10)
            except Exception:
                pass

        core.audio_timer = QTimer(core)
        core.audio_timer.timeout.connect(keep_game_audio_alive)
        core.audio_timer.start(100)

        core.chat_display.append(
            "<i style='color: #428bca;'>[System]: Focus & Audio Engine active. "
            "User screenshot presentation layer restored.</i>"
        )
    except Exception as e:
        core.chat_display.append(f"<i style='color: #ff4444;'>[System]: Error launching focus extensions: {e}</i>")