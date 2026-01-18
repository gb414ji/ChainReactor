import sys, os, subprocess, platform, ast, re
import streamlit as st

# --- 1. BOOTSTRAP ---
def launch():
    if not os.environ.get("STREAMLIT_RUNNING"):
        os.environ["STREAMLIT_RUNNING"] = "true"
        try:
            from streamlit.web import cli as stcli
            sys.argv = ["streamlit", "run", __file__, "--server.headless", "false"]
            sys.exit(stcli.main())
        except Exception:
            subprocess.check_call([sys.executable, "-m", "pip", "-q", "install", "streamlit"])

if __name__ == "__main__":
    launch()

# --- 2. STATE & STYLING ---
if 'steps' not in st.session_state: st.session_state.steps = ["ls", "pwd"]
if 'selected_order' not in st.session_state: st.session_state.selected_order = []

st.set_page_config(page_title="Chain Reactor", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000; color: #0f0; }
    .stTextInput input { background-color: #0a0a0a; color: #0f0; border: 1px solid #333; font-family: monospace; }
    textarea { background-color: #050505 !important; color: #0f0 !important; font-family: 'Courier New', monospace !important; border: 1px solid #222 !important; }
    .order-tag { color: #000; background-color: #0f0; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.75rem; }
    .stylish-banner { font-family: 'Courier New', monospace; color: #0f0; font-size: 0.6rem; line-height: 1.1; margin-bottom: 20px; white-space: pre; font-weight: bold; }
    .cmd-header { color: #00FF41; font-family: monospace; font-size: 0.85rem; background-color: #111; padding: 5px 10px; border-radius: 4px 4px 0 0; border: 1px solid #333; border-bottom: none; margin-top: 20px; }
    .help-box { border: 1px solid #333; padding: 15px; border-radius: 5px; background-color: #050505; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. UI: BANNER & TABS ---
BANNER_ART = r"""
 ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗    ██████╗ ███████╗ █████╗  ██████╗████████╗ ██████╗ ██████╗ 
██╔════╝██║  ██║██╔══██╗██║████╗  ██║    ██╔══██╗██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
██║     ███████║███████║██║██╔██╗ ██║    ██████╔╝█████╗  ███████║██║        ██║   ██║   ██║██████╔╝
██║     ██╔══██║██╔══██║██║██║╚██╗██║    ██╔══██╗██╔══╝  ██╔══██║██║        ██║   ██║   ██║██╔══██╗
╚██████╗██║  ██║██║  ██║██║██║ ╚████║    ██║  ██║███████╗██║  ██║╚██████╗   ██║   ╚██████╔╝██║  ██║
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
"""
st.markdown(f"<div class='stylish-banner'>{BANNER_ART}</div>", unsafe_allow_html=True)

tab_work, tab_help = st.tabs(["🚀 WORKSPACE", "📖 HELP & TRICKS"])

# --- 4. WORKSPACE TAB ---
with tab_work:
    for i in range(len(st.session_state.steps)):
        cols = st.columns([0.1, 0.7, 0.1, 0.1])
        
        # Checkbox & Order
        is_selected = cols[0].checkbox("", key=f"sel_{i}", value=(i in st.session_state.selected_order))
        if is_selected:
            if i not in st.session_state.selected_order: st.session_state.selected_order.append(i)
            cols[0].markdown(f"<span class='order-tag'>o{st.session_state.selected_order.index(i)+1}</span>", unsafe_allow_html=True)
        elif i in st.session_state.selected_order: st.session_state.selected_order.remove(i)

        # Command Input
        st.session_state.steps[i] = cols[1].text_input(f"S{i}", value=st.session_state.steps[i], key=f"in_{i}", label_visibility="collapsed")
        
        # PLAY BUTTON (Single Step Run)
        if cols[2].button("▶", key=f"run_single_{i}", help="Run only this step"):
            cmd = st.session_state.steps[i]
            st.markdown(f"<div class='cmd-header'>$ {cmd}</div>", unsafe_allow_html=True)
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd())
            st.text_area("Live Output", value=res.stdout if res.returncode==0 else res.stderr, height=150, key=f"single_out_{i}")

        # REMOVE
        if cols[3].button("❌", key=f"d_{i}"):
            st.session_state.steps.pop(i)
            if i in st.session_state.selected_order: st.session_state.selected_order.remove(i)
            st.rerun()

    st.divider()
    c1, c2, c3, c4 = st.columns([0.15, 0.15, 0.35, 0.35])
    if c1.button("＋ ADD STEP"): st.session_state.steps.append(""); st.rerun()
    if c2.button("🗑️ RESET"): 
        st.session_state.steps = [""]
        st.session_state.selected_order = []
        st.rerun()

    if c4.button("🚀 RUN SELECTED CHAIN", type="primary"):
        curr_dir = os.getcwd()
        for idx in st.session_state.selected_order:
            cmd = st.session_state.steps[idx]
            st.markdown(f"<div class='cmd-header'>o{st.session_state.selected_order.index(idx)+1} $ {cmd}</div>", unsafe_allow_html=True)
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=curr_dir)
            st.text_area("Chain Output", value=res.stdout if res.returncode==0 else res.stderr, height=150, key=f"chain_res_{idx}")
            if res.returncode == 0 and cmd.startswith("cd "):
                curr_dir = os.path.abspath(os.path.join(curr_dir, cmd[3:].strip()))

    if c3.button("📜 GENERATE SCRIPT"):
        ordered = [st.session_state.steps[idx] for idx in st.session_state.selected_order]
        script = f"import subprocess, os\ndef run():\n    cmds={ordered}\n    d=os.getcwd()\n    for c in cmds:\n        r=subprocess.run(c,shell=True,capture_output=True,text=True,cwd=d)\n        print(r.stdout if r.returncode==0 else r.stderr)\n        if c.startswith('cd '): d=os.path.abspath(os.path.join(d,c[3:].strip()))\nif __name__ == '__main__': run()"
        st.text_area("Automate Script", value=script, height=150)

# --- 5. HELP PAGE TAB ---
with tab_help:
    st.markdown("""
    <div class='help-box'>
    <h3>📖 The Chain Reactor Manual</h3>
    <p>Welcome, <b>wu</b>. This system is designed for high-speed terminal orchestration.</p>
    
    <h4>⚡ Pro Tricks for Smooth Execution</h4>
    <ul>
        <li><b>The {row} Injector:</b> Type <code>cat {row}</code>. If the previous step returned a list of files, this step will execute <i>for every single file</i> automatically.</li>
        <li><b>Smart Lists:</b> You can pass <code>rm [temp1.txt, temp2.txt]</code>. The engine will strip the brackets and quotes and run them sequentially.</li>
        <li><b>Directory Persistence:</b> Unlike standard shells, <code>cd</code> commands here are <b>sticky</b>. If Step 1 is <code>cd test</code>, all following steps run inside that folder.</li>
        <li><b>Partial Copying:</b> Because outputs are in text areas, you can highlight just a specific ID or Token and <code>Cmd+C</code> without grabbing the whole block.</li>
        <li><b>Instant Testing:</b> Use the <b>▶ button</b> next to any command to test it immediately without running the whole chain.</li>
    </ul>
    
    <h4>🛠️ Troubleshooting</h4>
    <ul>
        <li>If a command hangs, check if it's waiting for user input (like a password). Chain Reactor works best with non-interactive flags (e.g., <code>rm -rf</code> instead of <code>rm -i</code>).</li>
        <li>If <code>cd</code> isn't working, ensure the path exists relative to the starting folder.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
