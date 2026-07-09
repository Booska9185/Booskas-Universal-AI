*   Input: Original code (Python script with `sqlite3`, `PyQt6`, `concurrent.interpreters`).
    *   Task: Apply a "Suggested Edit" to the original code.
    *   Constraint: Output *only* the full file. No explanations. Preserve existing comments. Preserve unchanged code.
    *   Target Change: `patched_db_query` function within `setup`.
        *   SELECT logic: Better handling of `ORDER BY` and `LIMIT`.
        *   INSERT logic: Adding `VALUES (?, ` and prepending `core.current_world_id` to `params`.
    *   Wait, looking at the original code provided in the prompt:
        *   It has a syntax error in the original code snippet: `query = query[:idx] + f" {where_clause} " + query[idx:` (missing closing bracket and quote).
        *   It has a duplicated `load_world` function at the end.
        *   It has a syntax error: `active_interp = core.world_interpreters[world_id` (missing closing bracket).
    *   The "Suggested Edit" provides a cleaned-up version of the entire file.

    *   The suggested edit isn't just a snippet; it's a full version of the file.
    *   I need to ensure the output matches the provided suggested edit's logic while keeping the structure of the original if requested, but since the suggested edit provides the full corrected file, I will use that as the base, ensuring it resolves the bugs in the original (like the broken strings and duplicate functions).

    *   `patched_db_query` is updated.
    *   `load_world` is defined once.
    *   Syntax errors (missing brackets/quotes) are fixed.
    *   `InterpreterPoolExecutor` and `concurrent.interpreters` are kept.

    *   Only code.
    *   No summary.
    *   Full file.```python
import sqlite3
import os
import sys
from PyQt6.QtWidgets import QComboBox
# Python 3.14 specific imports for isolated memory execution
import concurrent.interpreters
from concurrent.futures import InterpreterPoolExecutor

def setup(core):
    """
    World IDs Module (Python 3.14 Edition):
    Injects a world selector, isolates database queries, and
    guarantees zero memory bleed by running each world's AI 
    background threads in isolated Python subinterpreters.
    """
    # 1. Initialize Active World State
    core.current_world_id = "Save_Slot_1"
    db_name = "universal_ai_rpg.db" 
    
    # 2. Update Database Structure Safely
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("ALTER TABLE chat_history ADD COLUMN world_id TEXT DEFAULT 'Save_Slot_1'")
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        pass 
    
    # 3. Inject "Load Game" UI Dropdown
    core.world_selector = QComboBox()
    core.world_selector.addItems(["Save_Slot_1", "Save_Slot_2", "Save_Slot_3")
    
    if core.centralWidget() and core.centralWidget().layout():
        core.centralWidget().layout().insertWidget(0, core.world_selector)
        
    # 4. Monkey Patch `db_query` to isolate memory
    core_module = sys.modules[core.__module__
    original_db_query = core_module.db_query
    
    def patched_db_query(query, params=(), fetch=False):
        """Intercepts queries to dynamically append the active world_id"""
        query_upper = query.upper()

        # Handle SELECT queries - Insert WHERE before ORDER BY or LIMIT
        if "FROM CHAT_HISTORY" in query_upper and "SELECT" in query_upper:
            where_clause = f"WHERE world_id = '{core.current_world_id}'"
            if "WHERE" in query_upper:
                query = query.replace("WHERE", f"{where_clause} AND ")
            else:
                order_idx = query_upper.find("ORDER BY")
                limit_idx = query_upper.find("LIMIT")
                idx = -1
                if order_idx != -1 and limit_idx != -1:
                    idx = min(order_idx, limit_idx)
                elif order_idx != -1:
                    idx = order_idx
                elif limit_idx != -1:
                    idx = limit_idx

                if idx != -1:
                    query = query[:idx] + f" {where_clause} " + query[idx:
                else:
                    query += f" {where_clause}"

        # Handle INSERT queries - Add placeholder for world_id
        elif "INSERT INTO CHAT_HISTORY" in query_upper and "WORLD_ID" not in query_upper:
            query = query.replace("(role, message", "(world_id, role, message")
            query = query.replace("VALUES (", "VALUES (?, ")
            params = (core.current_world_id,) + tuple(params)

        return original_db_query(query, params, fetch)
        
    core_module.db_query = patched_db_query
    
    # 5. Python 3.14 Subinterpreter Context Switching
    core.world_interpreters = {}
    core.world_executor = InterpreterPoolExecutor(max_workers=3) 

    def load_world(world_id):
        core.current_world_id = world_id
        
        # Isolate physical file directories for NPC pixel art
        npc_dir = f"npc_data_{world_id}"
        os.makedirs(npc_dir, exist_ok=True)
        core.npc_directory_path = npc_dir 
        
        # Spin up a completely isolated Python 3.14 environment for this world
        if world_id not in core.world_interpreters:
            interp = concurrent.interpreters.create()
            core.world_interpreters[world_id = interp
            
        # Bind the world configuration into the subinterpreter's __main__ globals
        active_interp = core.world_interpreters[world_id]
        active_interp.prepare_main(world_id=world_id, npc_dir=npc_dir)

        print(f"Loaded: {world_id}. NPC data locked to {npc_dir}. AI isolated in Subinterpreter {active_interp.id}.")

    # Connect UI dropdown to load logic
    core.world_selector.currentTextChanged.connect(load_world)
    load_world(core.current_world_id)
