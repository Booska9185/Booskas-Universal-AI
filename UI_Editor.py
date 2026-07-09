from PyQt6.QtWidgets import QPushButton, QInputDialog, QSizeGrip, QMainWindow

def setup(core):
    """
    Hooks into the main GameOverlay (core) to enable window resizing
    and provides a theme editor that dynamically updates UI styles.
    """

    # ==========================================
    # 1. WINDOW RESIZING LOGIC
    # ==========================================
    
    # QSizeGrip is a built-in PyQt widget that allows users to resize 
    # a frameless window by dragging the corner handle.
    resize_grip = QSizeGrip(core)
    
    # Style the grip to be visible as a semi-transparent yellow square.
    resize_grip.setStyleSheet(
        "width: 15px; "
        "height: 15px; "
        "background-color: rgba(255, 215, 0, 0.3); "
        "border-radius: 7px;"
    )
    
    # Add the grip to the bottom input layout so it appears in the corner.
    core.input_layout.addWidget(resize_grip)

    # We patch the resizeEvent to remember the custom window height.
    # Without this, the UI would reset to the default 480px height 
    # whenever you collapsed and expanded it.
    def hooked_resize_event(event):
        if not core.is_collapsed:
            core.normal_height = event.size().height()
        
        # Call the original QMainWindow resize event to ensure standard behavior is kept.
        QMainWindow.resizeEvent(core, event)
        
    # Apply the patch to the core overlay instance.
    core.resizeEvent = hooked_resize_event

    # ==========================================
    # 2. THEME OVERHAUL LOGIC
    # ==========================================
    
    # Create the palette button that launches the theme editor.
    theme_btn = QPushButton('🎨')
    core.custom_theme_color = None

    # We replace the core's update_style method so we can control all CSS 
    # from this module. This ensures the AI's internal glow animation 
    # does not override your custom colors.
    def hooked_update_style(color):
        # Determine the color to use (custom saved color or the passed-in system default).
        active_color = core.custom_theme_color if core.custom_theme_color else color
        
        # Define the stylesheet override.
        # We target the main window, buttons, inputs, and text areas.
        core.setStyleSheet(f'''
            QMainWindow {{ 
                background-color: #1a0505; 
                border: 2px solid {active_color}; 
                border-radius: 8px; 
            }}
            QPushButton {{ 
                color: #ffffff; 
                background-color: #1a0505; 
                border: 2px solid {active_color}; 
                border-radius: 5px; 
                font-weight: bold; 
                padding: 4px; 
            }}
            QPushButton:hover {{ 
                background-color: {active_color}; 
                color: #000000; 
            }}
            QLineEdit, QComboBox {{ 
                color: white; 
                background-color: #1a0505; 
                border: 1px solid {active_color}; 
                padding: 5px; 
            }}
            QTextEdit {{ 
                background-color: #0a0202; 
                color: #ffffff; 
                border: 1px solid {active_color}; 
                font-family: "Segoe UI", sans-serif; 
                font-size: 13px; 
            }}
            QScrollBar:vertical {{ 
                border: 1px solid {active_color}; 
                background: #1a0505; 
                width: 10px; 
            }}
            QScrollBar::handle:vertical {{ 
                background: {active_color}; 
                min-height: 20px; 
                border-radius: 4px; 
            }}
            QScrollBar::handle:vertical:hover {{ 
                background: #ffffff; 
            }}
        ''')
        
        # Ensure the title bar border remains consistent with your theme.
        core.title_bar.setStyleSheet(
            f"background-color: #1a0505; "
            f"border-radius: 4px; "
            f"border: 1px solid {active_color};"
        )

    # Monkey-patch the core function with our custom implementation.
    core.update_style = hooked_update_style

    # Function to trigger the dialog and update the UI when color is changed.
    def change_theme():
        new_color, ok = QInputDialog.getText(
            core, 
            "UI Theme Editor", 
            "Enter a color (e.g., #00ff00, blue, purple):"
        )
        
        # Check if the user confirmed the input.
        if ok:
            # Ensure the string is not empty before updating.
            if new_color.strip():
                core.custom_theme_color = new_color.strip()
                core.update_style(core.custom_theme_color)
                
                # Notify the user in the chat log.
                core.chat_display.append(
                    f"<i style='color: {core.custom_theme_color};'>"
                    f"[System]: UI theme updated to {core.custom_theme_color}.</i>"
                )
                
    # Connect the button click to the theme change dialog.
    theme_btn.clicked.connect(change_theme)
    
    # Inject the palette button into the main UI input row.
    # Inserting at index 4 places it near the other utility buttons.
    core.input_layout.insertWidget(4, theme_btn)