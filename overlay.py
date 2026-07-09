import sys
import os
import sqlite3
import time
import datetime
import shutil
import json
import importlib.util
import glob

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QBrush, QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QComboBox, QGraphicsOpacityEffect, QLabel,
    QDialog, QMessageBox
)

    def pulse_glow(self):
        """Animates the border glow effect without reloading the whole stylesheet."""
        self.glow_state = (self.glow_state + 1) % 6
        colors = ["#4a0404", "#6b0000", "#8b0000", "#b30000", "#8b0000", "#6b0000"]

        # Optimized: Just update the border color directly
        current_style = self.styleSheet()
        new_color = colors[self.glow_state]

        # Replace only the border property
        updated_style = current_style
        for c in ["#8b0000", "#6b0000", "#4a0404", "#b30000"]:
            updated_style = updated_style.replace(f"border: 2px solid {c};", f"border: 2px solid {new_color};")

        self.setStyleSheet(updated_style)

    def set_avatar_image(self, path):
        """Draws the NPC avatar."""
        target = QPixmap(128, 128)
        target.fill(Qt.GlobalColor.transparent)
        p = QPainter(target)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        clip = QPainterPath()
        clip.addEllipse(0, 0, 128, 128)
        p.setClipPath(clip)
        if path and os.path.exists(path):
            p.drawPixmap(0, 0, 128, 128, QPixmap(path))
        else:
            p.setBrush(QBrush(QColor("#4a0404")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(0, 0, 128, 128)
            p.setBrush(QBrush(QColor("#ffd700")))
            p.drawEllipse(40, 40, 48, 48)
        p.end()
        self.avatar_label.setPixmap(target)

    def update_avatar(self, name):
        """Updates the avatar based on the selected NPC."""
        if not name or name == 'General AI':
            self.set_avatar_image(None)
            self.title_label.setText("Booska's RPG Companion")
        else:
            self.title_label.setText(name)
            p_path = os.path.join("npcs", name, "portrait.png")
            self.set_avatar_image(p_path if os.path.exists(p_path) else None)

    def toggle_collapse(self):
        """Toggles the visibility of the UI."""
        self.is_collapsed = not self.is_collapsed
        widgets_to_hide = [self.chat_display]
        for i in range(self.input_layout.count()):
            widget = self.input_layout.itemAt(i).widget()
            if widget:
                widgets_to_hide.append(widget)
        for w in widgets_to_hide:
            w.setHidden(self.is_collapsed)
        self.setFixedHeight(65 if self.is_collapsed else self.normal_height)

    def cleanup_screenshots(self):
        """Deletes old screenshots on startup."""
        if os.path.exists("screenshots"):
            for f in os.listdir("screenshots"):
                try: 
                    os.remove(os.path.join("screenshots", f))
                except Exception: 
                    pass

    def load_npcs(self):
        """Loads available NPC folders."""
        cur = self.npc_selector.currentText()
        self.npc_selector.clear()
        self.npc_selector.addItem('General AI')
        if os.path.exists("npcs"):
            for f in os.listdir("npcs"):
                if os.path.isdir(os.path.join("npcs", f)):
                    self.npc_selector.addItem(f)
        idx = self.npc_selector.findText(cur)
        if idx >= 0: 
            self.npc_selector.setCurrentIndex(idx)

    def handle_main_input(self):
        """Processes chat input."""
        if self.input_box.text().strip():
            self.send_to_ai()

    def start_npc_creation(self):
        """Opens a popup for NPC creation."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New NPC")
        layout = QVBoxLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter NPC name...")
        
        backstory_input = QTextEdit()
        backstory_input.setPlaceholderText("Enter NPC backstory...")
        
        btn = QPushButton("Create NPC")
        
        def save_npc():
            name = name_input.text().strip()
            backstory = backstory_input.toPlainText().strip()
            if not name:
                return
            path = os.path.join("npcs", name)
            os.makedirs(path, exist_ok=True)
            mem = {
                "short_term": [],
                "mid_term": [],
                "long_term": f"Identity: {name}\nBackstory: {backstory}"
            }
            with open(os.path.join(path, "memory.json"), "w", encoding="utf-8") as f:
                json.dump(mem, f, indent=4)
            self.chat_display.append(f"<i style='color: #aaa;'>[System]: NPC {name} created.</i>")
            self.load_npcs()
            dialog.close()

        btn.clicked.connect(save_npc)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(name_input)
        layout.addWidget(QLabel("Backstory:"))
        layout.addWidget(backstory_input)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        dialog.exec()

    def edit_memory(self):
        """Opens a popup for memory editing."""
        npc = self.npc_selector.currentText()
        if npc == 'General AI':
            self.chat_display.append("<i style='color: #ff4444;'>[System]: General AI has no memory to edit.</i>")
            return
            
        mem_path = os.path.join("npcs", npc, "memory.json")
        if not os.path.exists(mem_path):
            self.chat_display.append("<i style='color: #ff4444;'>[System]: Error: No memory.json found.</i>")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Editing {npc} Memory")
        layout = QVBoxLayout()
        editor = QTextEdit()
        with open(mem_path, "r", encoding="utf-8") as f:
            editor.setPlainText(f.read())
            
        btn = QPushButton("Save Memory")
        
        def save_mem():
            try:
                json_data = json.loads(editor.toPlainText())
                with open(mem_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4)
                self.chat_display.append(f"<i style='color: #aaa;'>[System]: Memory saved for {npc}.</i>")
                dialog.close()
            except Exception as e:
                QMessageBox.critical(dialog, "Invalid JSON", f"Save failed: {e}")

        btn.clicked.connect(save_mem)
        layout.addWidget(editor)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        dialog.exec()

    def delete_npc(self):
        npc = self.npc_selector.currentText()
        if npc == 'General AI':
            self.chat_display.append("<i style='color: #ff4444;'>[System]: General AI cannot be deleted.</i>")
            return
        path = os.path.join("npcs", npc)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                self.chat_display.append(f"<i style='color: #aaa;'>[System]: NPC '{npc}' banished.</i>")
            except Exception as e:
                self.chat_display.append(f"<i style='color: #ff4444;'>[System]: Banishment failed: {e}</i>")
        self.load_npcs()
        self.npc_selector.setCurrentIndex(0)
        self.update_avatar('General AI')

    def load_history(self):
        self.chat_display.clear()
        for r, m in reversed(db_query("SELECT role, message FROM chat_history ORDER BY id DESC LIMIT 50", fetch=True)):
            self.chat_display.append(self.format_message(r, m))

    def clear_chat(self):
        db_query("DELETE FROM chat_history")
        self.chat_display.clear()
        self.chat_display.append("<i style='color: #aaa;'>[System]: Chrono-log purged.</i>")

    def capture_screen(self):
        # Optimized: Set opacity to 0 instead of hiding, which is much smoother
        self.setWindowOpacity(0)
        QApplication.processEvents()
        time.sleep(0.1) # Reduced delay for snappier performance
        screen = QApplication.primaryScreen()
        if screen:
            path = f"screenshots/snip_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs("screenshots", exist_ok=True)
            screen.grabWindow(0).save(path, "png")
            self.attached_screenshot_path = path
            self.chat_display.append("<i style='color: #aaa;'>[System]: Capture cached.</i>")
        self.setWindowOpacity(0.9)

    def load_modules(self):
        os.makedirs("modules", exist_ok=True)
        for file_path in glob.glob("modules/*.py"):
            module_name = os.path.basename(file_path)[:-3]
            if module_name == "__init__":
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                if hasattr(mod, 'setup'):
                    mod.setup(self)
            except Exception as e:
                self.chat_display.append(f"<i style='color: #ff4444;'>[System]: Error loading {module_name}: {e}</i>")

    def send_to_ai(self):
        text = self.input_box.text()
        # 1. Run Pre-Send Hooks
        for hook in self.hooks_pre_send:
            text = hook(text)
            
        if text is None:
            self.input_box.clear()
            return
            
        if not text and not self.attached_screenshot_path:
            return
        
        npc = self.npc_selector.currentText()
        self.chat_display.append(self.format_message("You", text))
        self.input_box.clear()
        self.input_box.setEnabled(False)
        
        db_query("INSERT INTO chat_history (role, message) VALUES (?, ?)", ("You", text if text else "[Attached Image]"))
        
        contents = []
        for r, m in reversed(db_query("SELECT role, message FROM chat_history ORDER BY id DESC LIMIT 14", fetch=True)):
            if m.strip() or self.attached_screenshot_path:
                contents.append(types.Content(role="user" if r.lower() == "you" else "model", parts=[types.Part.from_text(text=m)]))
        
        # Screenshot logic
        if self.attached_screenshot_path and os.path.exists(self.attached_screenshot_path):
            try:
                with open(self.attached_screenshot_path, "rb") as f:
                    img = f.read()
                if contents and contents[-1].role == "user":
                    contents[-1].parts.append(types.Part.from_bytes(data=img, mime_type="image/png"))
                else:
                    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=text if text else "Image attached"), types.Part.from_bytes(data=img, mime_type="image/png")]))
            except Exception:
                pass
            try:
                os.remove(self.attached_screenshot_path)
            except Exception:
                pass
            
            self.attached_screenshot_path = None
            
        sys_inst = None
        if npc != 'General AI':
            mem_path = os.path.join("npcs", npc, "memory.json")
            if os.path.exists(mem_path):
                try:
                    with open(mem_path, "r", encoding="utf-8") as f:
                        mem_data = json.load(f)
                    sys_inst = (
                        "You are an NPC in a game. Context:\n\n"
                        "LONG-TERM:\n" + mem_data.get('long_term', '') + "\n\n"
                        "MID-TERM:\n" + json.dumps(mem_data.get('mid_term', [])) + "\n\n"
                        "SHORT-TERM:\n" + json.dumps(mem_data.get('short_term', [])) + "\n"
                    )
                except Exception:
                    pass

        self.glow_timer.start(150)
        self.chat_display.append(f"<b style='color:#ffd700;'>[{npc}]:</b> ")
        self.stream_cursor = self.chat_display.textCursor()
        self.stream_cursor.movePosition(QTextCursor.MoveOperation.End)
        
        self.worker = GeminiWorker(self.client, contents, sys_inst)
        self.worker.chunk_received.connect(lambda c: (self.stream_cursor.insertText(c), self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())))
        self.worker.finished.connect(lambda t: self.handle_ai_response(t, npc, text))
        
        def handle_error(e):
            self.glow_timer.stop()
            self.update_style("#8b0000")
            self.input_box.setEnabled(True)
            self.chat_display.append(self.format_message("Error", e))
        
        self.worker.error.connect(handle_error)
        self.worker.start()
    def handle_ai_response(self, text, npc, user_text):
        self.glow_timer.stop()
        self.update_style("#8b0000")
        self.input_box.setEnabled(True)
        db_query("INSERT INTO chat_history (role, message) VALUES (?, ?)", (npc, text))
        
        if npc != 'General AI':
            mem_path = os.path.join("npcs", npc, "memory.json")
            if os.path.exists(mem_path):
                try:
                    with open(mem_path, "r", encoding="utf-8") as f:
                        mem_data = json.load(f)
                    
                    mem_data.setdefault("short_term", []).append({"You": user_text, npc: text})
                    
                    if len(mem_data["short_term"]) >= 10:
                        self.chat_display.append("<i style='color: #aaa;'>[System]: Memory threshold reached. Collapsing timeline...</i>")
                        self.memory_worker = MemorySummarizer(self.client, npc, mem_data, mem_path)
                        self.memory_worker.finished_update.connect(lambda msg: self.chat_display.append(f"<i style='color: #aaa;'>[System]: {msg}</i>"))
                        self.memory_worker.start()
                    else:
                        with open(mem_path, "w", encoding="utf-8") as f:
                            json.dump(mem_data, f, indent=4)
                except Exception as e:
                    self.chat_display.append(f"<i style='color: #ff4444;'>[System]: Memory save error: {e}</i>")

        # 2. Run Post-Receive Hooks
        for hook in self.hooks_post_receive:
            hook(npc, text)

    def format_message(self, sender, text):
        c = "#428bca" if sender == "You" else ("#ff4444" if sender == "Error" else "#ffd700")
        return f"<b style='color:{c};'>[{sender}]:</b> {text}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = GameOverlay()
    overlay.show()
    sys.exit(app.exec())