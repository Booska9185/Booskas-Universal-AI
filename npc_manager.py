import os
import json
import requests
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QTextEdit, QPushButton, QLabel, QMessageBox

def setup(core):
    """
    NPC Manager Module:
    1. Handles all NPC profile creation, memory updates, and directory layouts.
    2. Controls Pollinations.ai image synthesis using clean retro 16-bit pixel art modifiers.
    3. Injects an on-the-fly portrait regeneration tool right into the core UI layout.
    """

    # Hard-locked 16-bit pixel art tags to enforce a classic retro RPG aesthetic
    STYLE_MODIFIERS = (
        "16-bit retro pixel art portrait, classic SNES RPG character asset, "
        "detailed pixelated sprite style, clean pixel grids, limited vibrant color palette, "
        "crisp non-blurry pixel edges, 90s video game profile picture, pixel art illustration"
    )

    def generate_image(prompt, save_path):
        """Calls Pollinations.ai to build and overwrite an avatar file."""
        try:
            safe_prompt = requests.utils.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=512&height=512&seed=42"
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            print(f"Image generation failed: {e}")
            return False

    def new_start_npc_creation():
        dialog = QDialog(core)
        dialog.setWindowTitle("Create New NPC")
        layout = QVBoxLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter NPC name...")
        
        backstory_input = QTextEdit()
        backstory_input.setPlaceholderText("Enter NPC backstory...")
        
        btn = QPushButton("Create NPC & Generate 16-Bit Portrait")
        
        def save_npc():
            name = name_input.text().strip()
            backstory = backstory_input.toPlainText().strip()
            if not name:
                QMessageBox.warning(dialog, "Error", "Name required.")
                return
            
            path = os.path.join("npcs", name)
            os.makedirs(path, exist_ok=True)
            
            core.chat_display.append(f"<i style='color: #aaa;'>[System]: Synthesizing 16-bit pixel portrait for {name}...</i>")
            portrait_path = os.path.join(path, "portrait.png")
            prompt = f"Portrait of {name}, {backstory}, {STYLE_MODIFIERS}"
            
            success = generate_image(prompt, portrait_path)
            if not success:
                core.chat_display.append("<i style='color: #ff4444;'>[System]: Photo rendering dropped. Using fallback default.</i>")
            
            # Save structural long_term memory profile
            mem = {"short_term": [], "mid_term": [], "long_term": f"Identity: {name}\nBackstory: {backstory}"}
            with open(os.path.join(path, "memory.json"), "w", encoding="utf-8") as f:
                json.dump(mem, f, indent=4)
                
            core.chat_display.append(f"<i style='color: #aaa;'>[System]: NPC {name} created successfully.</i>")
            core.load_npcs()
            core.update_avatar(name)
            dialog.close()

        btn.clicked.connect(save_npc)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(name_input)
        layout.addWidget(QLabel("Backstory:"))
        layout.addWidget(backstory_input)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        dialog.exec()

    def new_edit_memory():
        npc = core.npc_selector.currentText()
        if npc == 'General AI':
            core.chat_display.append("<i style='color: #ff4444;'>[System]: General AI does not contain editable profile matrices.</i>")
            return
        mem_path = os.path.join("npcs", npc, "memory.json")
        if not os.path.exists(mem_path):
            core.chat_display.append("<i style='color: #ff4444;'>[System]: Error: Profile memory configuration missing.</i>")
            return
            
        dialog = QDialog(core)
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
                core.chat_display.append(f"<i style='color: #aaa;'>[System]: Memory logs updated for {npc}.</i>")
                dialog.close()
            except Exception as e:
                QMessageBox.critical(dialog, "Invalid JSON", f"Save aborted: {e}")

        btn.clicked.connect(save_mem)
        layout.addWidget(editor)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        dialog.exec()

    def regenerate_portrait():
        """Brings up an on-the-fly prompt tweaker to refresh the selected NPC's appearance."""
        npc = core.npc_selector.currentText()
        if npc == 'General AI':
            core.chat_display.append("<i style='color: #ff4444;'>[System]: General AI does not maintain a profile avatar.</i>")
            return
        
        mem_path = os.path.join("npcs", npc, "memory.json")
        if not os.path.exists(mem_path):
            core.chat_display.append(f"<i style='color: #ff4444;'>[System]: Error: Profile background data missing for {npc}.</i>")
            return

        # Read the file and strip administrative structural strings ("Identity:", "Backstory:")
        try:
            with open(mem_path, "r", encoding="utf-8") as f:
                mem_data = json.load(f)
            raw_context = mem_data.get("long_term", "")
            cleaned_context = raw_context.replace(f"Identity: {npc}", "").replace("Backstory:", "").strip()
        except Exception:
            cleaned_context = ""

        dialog = QDialog(core)
        dialog.setWindowTitle(f"Regenerate Portrait: {npc}")
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Tweak Character Features / Add Descriptive Elements:"))
        prompt_input = QTextEdit()
        prompt_input.setPlainText(f"Portrait of {npc}, {cleaned_context}, {STYLE_MODIFIERS}")
        layout.addWidget(prompt_input)
        
        btn = QPushButton("Generate & Replace with 16-Bit Portrait")
        
        def process_generation():
            final_prompt = prompt_input.toPlainText().strip()
            if not final_prompt:
                return
            
            portrait_path = os.path.join("npcs", npc, "portrait.png")
            core.chat_display.append(f"<i style='color: #aaa;'>[System]: Morphing 16-bit avatar structure for {npc}...</i>")
            dialog.close()
            
            success = generate_image(final_prompt, portrait_path)
            if success:
                core.chat_display.append(f"<i style='color: #aaa;'>[System]: Portrait updated for {npc}!</i>")
                core.update_avatar(npc)
            else:
                core.chat_display.append("<i style='color: #ff4444;'>[System]: Avatar transformation failed.</i>")

        btn.clicked.connect(process_generation)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        dialog.exec()

    try:
        # Safely unhook standard PyQt layout click signals to avoid console warnings
        try:
            core.npc_btn.clicked.disconnect()
        except TypeError:
            pass
            
        try:
            core.edit_btn.clicked.disconnect()
        except TypeError:
            pass

        core.npc_btn.clicked.connect(new_start_npc_creation)
        core.edit_btn.clicked.connect(new_edit_memory)
        
        # Inject the portrait modification trigger button directly into the lower control rack
        regen_btn = QPushButton('🔄')
        regen_btn.setToolTip("Regenerate Selected NPC Portrait")
        regen_btn.clicked.connect(regenerate_portrait)
        core.input_layout.insertWidget(6, regen_btn)
        
        core.chat_display.append("<i style='color: #428bca;'>[System]: NPC Manager: Pipelines isolated. 16-bit pixel engine synchronized.</i>")
    except Exception as e:
        core.chat_display.append(f"<i style='color: #ff4444;'>[System]: Error mounting layout bridges: {e}</i>")