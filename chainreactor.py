import sys, os, subprocess, platform, re, getpass
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components

# --- 1. BOOTSTRAP ---
def launch():
    if not os.environ.get("STREAMLIT_RUNNING"):
        os.environ["STREAMLIT_RUNNING"] = "true"
        try:
            from streamlit.web import cli as stcli
            sys.argv = ["streamlit", "run", __file__, "--server.headless", "false"]
            sys.exit(stcli.main())
        except Exception:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])

if __name__ == "__main__":
    launch()

# --- 2. ROBUST PARSER ---
def execute_smart_cmd(cmd, working_dir):
    match = re.search(r"\[(.*?)\]", cmd)
    if match:
        base_cmd = cmd[:match.start()].strip()
        raw_items = re.findall(r'(?:"[^"]*"|[^\s,]+)', match.group(1))
        items = [i.strip('"').strip("'") for i in raw_items if i.strip()]
        suffix = cmd[match.end():].strip()
        final_out, success = "", True
        for item in items:
            safe_item = f'"{item}"' if " " in item else item
            full_cmd = f"{base_cmd} {safe_item} {suffix}".strip()
            res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, cwd=working_dir)
            final_out += f"-> {safe_item}:\n{res.stdout if res.returncode==0 else res.stderr}\n"
            if res.returncode != 0: success = False
        return final_out, success
    else:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=working_dir)
        return (res.stdout if res.returncode==0 else res.stderr), (res.returncode == 0)

# --- 3. UI STYLING ---
st.set_page_config(page_title="Chain Reactor", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000; color: #0f0; }
    .stTextInput input { background-color: #0a0a0a; color: #0f0; border: 1px solid #333; font-family: monospace; }
    textarea { background-color: #050505 !important; color: #0f0 !important; font-family: 'Courier New', monospace !important; border: 1px solid #222 !important; font-size: 13px !important; }
    .order-tag { color: #000; background-color: #0f0; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.75rem; }
    .stylish-banner { font-family: 'Courier New', monospace; color: #0f0; font-size: 0.55rem; line-height: 1.1; margin-bottom: 20px; white-space: pre; }
    .cmd-header { color: #00FF41; font-family: monospace; font-size: 0.85rem; background-color: #111; padding: 5px 10px; border-radius: 4px 4px 0 0; border: 1px solid #333; margin-top: 15px; }
    .feature-box { border: 1px solid #222; padding: 15px; background-color: #050505; border-radius: 5px; margin-bottom: 15px; }
    .feature-title { color: #0f0; font-weight: bold; font-size: 1.1rem; margin-bottom: 10px; border-bottom: 1px solid #333; }
    code { color: #fff; background: #1a1a1a; padding: 2px 4px; border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. WORKSPACE LOGIC ---
if 'steps' not in st.session_state: st.session_state.steps = ["ls", "pwd"]
if 'selected_order' not in st.session_state: st.session_state.selected_order = []
if 'outputs' not in st.session_state: st.session_state.outputs = {}
if 'print_trigger' not in st.session_state: st.session_state.print_trigger = False

BANNER_TEXT = r'''
 ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗    ██████╗ ███████╗ █████╗  ██████╗████████╗ ██████╗ ██████╗ 
██╔════╝██║  ██║██╔══██╗██║████╗  ██║    ██╔══██╗██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
██║     ███████║███████║██║██╔██╗ ██║    ██████╔╝█████╗  ███████║██║        ██║   ██║   ██║██████╔╝
██║     ██╔══██║██╔══██║██║██║╚██╗██║    ██╔══██╗██╔══╝  ██╔══██║██║        ██║   ██║   ██║██╔══██╗
╚██████╗██║  ██║██║  ██║██║██║ ╚████║    ██║  ██║███████╗██║  ██║╚██████╗   ██║   ╚██████╔╝██║  ██║
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
'''
st.markdown(f"<div class='stylish-banner'>{BANNER_TEXT}</div>", unsafe_allow_html=True)

# Print Component
if st.session_state.print_trigger:
    report_html = f"<div style='font-family: monospace; background: #000; color: #0f0; padding: 20px;'><pre>{BANNER_TEXT}</pre><h2>CHAIN REACTOR REPORT</h2><hr/>"
    for key, data in st.session_state.outputs.items():
        label = "Single Step" if key.startswith("s_") else f"Chain Step {key.split('_')[1]}"
        report_html += f"<div style='border:1px solid #333; margin: 10px 0; padding: 10px;'><b>[{label}] {data['status']}</b><br/><code>$ {data.get('cmd', 'Unknown')}</code><br/><pre>{data['out']}</pre></div>"
    report_html += "</div><script>window.print();</script>"
    components.html(report_html, height=0, width=0)
    st.session_state.print_trigger = False

tab_work, tab_help = st.tabs(["🚀 WORKSPACE", "📖 HELP"])

with tab_work:
    # Workspace logic...
    for i in range(len(st.session_state.steps)):
        cols = st.columns([0.1, 0.7, 0.1, 0.1])
        is_sel = cols[0].checkbox("", key=f"sel_{i}", value=(i in st.session_state.selected_order))
        if is_sel:
            if i not in st.session_state.selected_order: st.session_state.selected_order.append(i)
            cols[0].markdown(f"<span class='order-tag'>o{st.session_state.selected_order.index(i)+1}</span>", unsafe_allow_html=True)
        elif i in st.session_state.selected_order: st.session_state.selected_order.remove(i)
        st.session_state.steps[i] = cols[1].text_input(f"S{i}", value=st.session_state.steps[i], key=f"in_{i}", label_visibility="collapsed")
        if cols[2].button("▶", key=f"run_s_{i}"):
            out, success = execute_smart_cmd(st.session_state.steps[i], os.getcwd())
            st.session_state.outputs[f"s_{i}"] = {"out": out, "status": "✅" if success else "❌", "cmd": st.session_state.steps[i]}
        if cols[3].button("❌", key=f"d_{i}"):
            st.session_state.steps.pop(i); st.rerun()
        if f"s_{i}" in st.session_state.outputs:
            d = st.session_state.outputs[f"s_{i}"]
            st.markdown(f"<div class='cmd-header'>$ {st.session_state.steps[i]} {d['status']}</div>", unsafe_allow_html=True)
            st.text_area("Result", value=d['out'], height=120, key=f"ar_s_{i}")

    st.divider()
    c1, c2, c3, c4 = st.columns([0.2, 0.2, 0.2, 0.4])
    if c1.button("＋ ADD STEP"): st.session_state.steps.append(""); st.rerun()
    if c2.button("🗑️ RESET"): st.session_state.steps=[""]; st.session_state.selected_order=[]; st.session_state.outputs={}; st.rerun()
    if c3.button("🧹 CLEAR LOGS"): st.session_state.outputs={}; st.rerun()
    if c4.button("🖨️ PRINT REPORT", use_container_width=True):
        if st.session_state.outputs: st.session_state.print_trigger = True; st.rerun()

    if st.button("🚀 RUN SELECTED CHAIN", type="primary"):
        curr_dir = os.getcwd()
        for idx in st.session_state.selected_order:
            cmd = st.session_state.steps[idx]
            out, success = execute_smart_cmd(cmd, curr_dir)
            st.session_state.outputs[f"c_{idx}"] = {"out": out, "status": "✅" if success else "❌", "cmd": cmd}
            if success and cmd.startswith("cd "):
                raw_path = re.search(r"\[(.*?)\]", cmd).group(1) if "[" in cmd else cmd[3:]
                last_path = [p.strip() for p in re.split(r',|\s+', raw_path) if p.strip()][-1]
                curr_dir = os.path.abspath(os.path.join(curr_dir, last_path))
            if not success: break
        st.rerun()

with tab_help:
    st.markdown("""
    <div class='feature-box'>
        <div class='feature-title'>Smart-List Syntax <code>[ ]</code></div>
        <p>Enables batch execution by wrapping items in brackets. Supports comma and space separators.</p>
        <ul>
            <li><b>Auto-Quoting:</b> Multi-word filenames (e.g., <code>[test file.py]</code>) are automatically wrapped in quotes.</li>
            <li><b>Flexible Delimiters:</b> Works with <code>[a, b]</code> or <code>[a b]</code>.</li>
            <li><b>Recursive Pathing:</b> Handles sequential directory changes within brackets.</li>
        </ul>
    </div>

    <div class='feature-box'>
        <div class='feature-title'>Chaining Engine <code>(o1, o2...)</code></div>
        <p>Defines a logic-bound execution sequence based on user selection.</p>
        <ul>
            <li><b>Ordered Execution:</b> Commands run sequentially following the numeric order (o1 → o2).</li>
            <li><b>Failure Protection:</b> The chain automatically terminates if any step returns an error (❌).</li>
            <li><b>Working Directory Persistence:</b> Directory changes in one step carry over to the next within the same chain run.</li>
        </ul>
    </div>

    <div class='feature-box'>
        <div class='feature-title'>Output & Reporting Options</div>
        <ul>
            <li><b>▶ (Single Run):</b> Executes a specific step in isolation for testing.</li>
            <li><b>🖨️ Print Report:</b> Compiles all session logs into a standalone HTML/PDF document.</li>
            <li><b>🧹 Clear Logs:</b> Removes output data while maintaining the command configuration.</li>
            <li><b>🗑️ Reset:</b> Restores the system to factory state (wipes both configuration and logs).</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
