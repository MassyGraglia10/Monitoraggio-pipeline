import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import urllib.parse
import re

# --- CONFIGURAZIONE ---
PAT = "C2IOyo7XbxiJiQWjP6O0uxiZ9NWSeVsgIuyI6T5OCqyElje9mIzIJQQJ99CHACAAAAA4D5C9AAASAZDO4YEZ"
ORGANIZATION = "realeitesorg"
EXCEL_FILE = "Rilascio  evolutivo 09_2026- Copia.xlsx"

EXCLUDED_PROD_PIPELINES = [
    "prod"
]

st.set_page_config(page_title="Azure Pipelines Monitor", layout="wide")

CUSTOM_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 0.8rem; padding-bottom: 0rem;}
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.15; }
        100% { opacity: 1; }
    }
    .spinner-icon {
        display: inline-block;
        width: 12px;
        height: 12px;
        border: 2px solid #cbd5e1;
        border-top: 2px solid #0284c7;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        vertical-align: middle;
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        background: white;
        border-radius: 6px;
        overflow: hidden;
        table-layout: fixed;
    }
    .custom-table th, .custom-table td {
        padding: 6px 8px;
        border-bottom: 1px solid #e6e9ef;
        vertical-align: middle;
        color: #31333f;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .custom-table th {
        background-color: #f0f2f6;
        font-weight: 600;
        text-align: left;
    }
    .custom-table tr:hover {
        background-color: #f8f9fb;
    }
    .col-proj { width: 110px; white-space: normal; }
    .col-pipe { width: 140px; }
    .col-change { width: 90px; text-align: center; }
    .col-desc { width: 180px; }
    .col-link { width: 85px; text-align: center; }
    .col-build { width: 120px; }
    .col-stages { width: auto; white-space: normal; }
    .col-status { width: 175px; }

    .azure-link {
        color: #0284c7;
        text-decoration: none;
        font-weight: 500;
    }
    .azure-link:hover {
        text-decoration: underline;
    }
    code {
        background-color: #f1f5f9;
        padding: 2px 4px;
        border-radius: 4px;
        font-size: 11px;
        color: #0f172a;
    }
    .skipped-badge {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 1px 3px;
        display: inline-block;
        line-height: 1;
    }
    .success-bright {
        color: #00c853 !important;
        font-weight: 700;
        text-shadow: 0 0 1px rgba(0, 200, 83, 0.4);
    }
    .failed-bright {
        color: #ef4444 !important;
        font-weight: 700;
        text-shadow: 0 0 1px rgba(239, 68, 68, 0.4);
    }
    .prod-blinking-ok {
        display: inline-block;
        color: #00c853 !important;
        font-weight: 700;
        animation: blink 1s infinite ease-in-out;
    }
    
    /* Stile compatto per la mini-tabella delle metriche */
    .metrics-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #f8f9fb;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        font-size: 11px;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .metrics-table th {
        background-color: #edf2f7;
        color: #1e293b;
        padding: 4px 6px;
        border: 1px solid #e2e8f0;
        font-weight: 600;
        white-space: nowrap;
    }
    .metrics-table td {
        padding: 6px 6px;
        border: 1px solid #e2e8f0;
        font-size: 14px;
        font-weight: 700;
        color: #0f172a;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

col_title, col_btn = st.columns([5, 1])
with col_title:
    st.title("⚡ Azure Pipelines Monitor - Rilascio evolutivo 09_2026")
with col_btn:
    st.write("") 
    if st.button("🔄 Aggiorna Dati", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

def clean_text(val):
    if pd.isna(val):
        return ""
    return re.sub(r'\s+', ' ', str(val)).strip()

def parse_input(val):
    if "buildId=" in val:
        match = re.search(r'buildId=(\d+)', val)
        if match:
            return match.group(1), "build_id"
    if "definitionId=" in val:
        match = re.search(r'definitionId=(\d+)', val)
        if match:
            return match.group(1), "def_id"
    if val.isdigit():
        return val, "def_id"
    return val, "name"

@st.cache_data(ttl=3600, show_spinner=False)
def resolve_name_from_def(project, def_id):
    enc_proj = urllib.parse.quote(project, safe='')
    url = f"https://dev.azure.com/{ORGANIZATION}/{enc_proj}/_apis/build/definitions/{def_id}?api-version=7.0"
    try:
        r = requests.get(url, auth=HTTPBasicAuth('', PAT), timeout=2.0)
        if r.status_code == 200:
            return r.json().get('name')
    except:
        pass
    return f"ID: {def_id}"

@st.cache_data(ttl=3600, show_spinner=False)
def resolve_def_from_name(project, pipeline_name):
    enc_proj = urllib.parse.quote(project, safe='')
    url_all = f"https://dev.azure.com/{ORGANIZATION}/{enc_proj}/_apis/build/definitions?api-version=7.0"
    try:
        r = requests.get(url_all, auth=HTTPBasicAuth('', PAT), timeout=2.5)
        if r.status_code == 200:
            definitions = r.json().get('value', [])
            search_target = pipeline_name.lower().strip()
            for item in definitions:
                item_name = item.get('name', '')
                if search_target in item_name.lower():
                    return item['id'], item_name
    except:
        pass
    return None, pipeline_name

def clean_stage_name(name):
    n_lower = name.lower()
    if "maven" in n_lower or "build" in n_lower:
        return "Build"
    elif "intr1" in n_lower:
        return "INTR1"
    elif "intr2" in n_lower:
        return "INTR2"
    elif "sysr2" in n_lower or "sys/r2" in n_lower:
        return "SYSR2"
    elif "preprod" in n_lower:
        return "PREPROD"
    elif "prod" in n_lower:
        return "PROD"
    elif "merge" in n_lower:
        if "intr" in n_lower:
            return "Merge INTR"
        elif "sys" in n_lower:
            return "Merge SYSR2"
        return "Merge"
    elif "approval" in n_lower or "approvazione" in n_lower:
        return "Approvazione"
    elif "select" in n_lower or "interval" in n_lower:
        return "Interval"
    return name if len(name) <= 12 else name[:10] + ".."

def check_if_already_in_prod(session, project, build_id):
    enc_proj = urllib.parse.quote(project, safe='')
    url = f"https://dev.azure.com/{ORGANIZATION}/{enc_proj}/_apis/build/builds/{build_id}/timeline?api-version=7.0"
    try:
        r = session.get(url, timeout=2.0)
        if r.status_code == 200:
            records = r.json().get('records', [])
            for rec in records:
                if rec.get('type') == 'Stage':
                    name = rec.get('name', '').lower()
                    if 'prod' in name and rec.get('state') == 'completed' and rec.get('result') == 'succeeded':
                        return True
    except:
        pass
    return False

def analyze_build_progress(records):
    stages = [rec for rec in records if rec.get('type') == 'Stage']
    seen = set()
    unique_stages = []
    for idx, s in enumerate(stages):
        name = s.get('name')
        if name and name not in seen:
            seen.add(name)
            s['_original_index'] = idx
            unique_stages.append(s)
    
    def robust_sort_key(s):
        start_time = s.get('startTime') or ''
        orig_idx = s.get('_original_index', 0)
        return (0 if start_time else 1, start_time, orig_idx)

    unique_stages.sort(key=robust_sort_key)

    highest_successful_env = None
    failed_env = None
    waiting_for_preprod_approval = False

    for i, stage in enumerate(unique_stages):
        raw_name = stage.get('name', '').lower()
        state = stage.get('state')
        result = stage.get('result')

        is_succeeded = (state == 'completed' and result == 'succeeded')
        is_failed = (state == 'completed' and result == 'failed')
        is_in_progress = (state == 'inProgress')
        is_paused_waiting = (state in ['pending', 'inProgress'] or not state)

        if 'intr1' in raw_name and is_succeeded:
            highest_successful_env = "INTR1"
        elif 'intr2' in raw_name and is_succeeded:
            highest_successful_env = "INTR2"
        elif ('sysr2' in raw_name or 'sys/r2' in raw_name) and is_succeeded:
            highest_successful_env = "SYSR2"
        elif 'preprod' in raw_name and is_succeeded:
            highest_successful_env = "PREPROD"

        if is_failed:
            if 'intr1' in raw_name:
                failed_env = "INTR1"
            elif 'intr2' in raw_name:
                failed_env = "INTR2"
            elif 'sysr2' in raw_name or 'sys/r2' in raw_name:
                failed_env = "SYSR2"
            elif 'preprod' in raw_name:
                failed_env = "PREPROD"
            elif 'prod' in raw_name:
                failed_env = "PROD"
            else:
                failed_env = clean_stage_name(stage.get('name', 'Stage'))

        if 'preprod' in raw_name:
            if is_in_progress or is_paused_waiting:
                prev_all_ok = True
                for prev_s in unique_stages[:i]:
                    if prev_s.get('state') != 'completed' or prev_s.get('result') not in ['succeeded', 'skipped']:
                        prev_all_ok = False
                        break
                if prev_all_ok:
                    waiting_for_preprod_approval = True

    return highest_successful_env, failed_env, waiting_for_preprod_approval

def get_stages_html(session, project, build_id):
    enc_proj = urllib.parse.quote(project, safe='')
    url = f"https://dev.azure.com/{ORGANIZATION}/{enc_proj}/_apis/build/builds/{build_id}/timeline?api-version=7.0"
    try:
        r = session.get(url, timeout=2.0)
        if r.status_code == 200:
            records = r.json().get('records', [])
            stages = [rec for rec in records if rec.get('type') == 'Stage']
            
            seen = set()
            unique_stages = []
            for idx, s in enumerate(stages):
                name = s.get('name')
                if name and name not in seen:
                    seen.add(name)
                    s['_original_index'] = idx
                    unique_stages.append(s)
            
            def robust_sort_key(s):
                start_time = s.get('startTime') or ''
                orig_idx = s.get('_original_index', 0)
                return (0 if start_time else 1, start_time, orig_idx)

            unique_stages.sort(key=robust_sort_key)
            
            elements = []
            found_active = False

            for stage in unique_stages:
                raw_name = stage.get('name', 'Stage')
                short_name = clean_stage_name(raw_name)
                state = stage.get('state')
                result = stage.get('result')
                
                if state == "completed":
                    if result == "succeeded":
                        icon, status_label = '<span class="success-bright">🟢</span>', "Succeeded"
                    elif result == "failed":
                        icon, status_label = "🔴", "Failed"
                    elif result == "canceled":
                        icon, status_label = "⚪", "Canceled"
                    elif result == "skipped":
                        icon, status_label = '<span class="skipped-badge">⏭️</span>', "Skipped"
                    elif result in ["succeededWithIssues", "warning"]:
                        icon, status_label = "🔵", "Succeeded with issues"
                    else:
                        icon, status_label = "🔵", str(result)
                elif state == "inProgress":
                    icon, status_label = '<div class="spinner-icon"></div>', "In corso"
                    found_active = True
                else:
                    if not found_active and (state in ["pending", "inProgress"] or not state or result is None):
                        icon, status_label = "⏳", "In attesa"
                        found_active = True
                    else:
                        icon, status_label = "⚪", "Non avviato"
                
                tooltip_text = f"{raw_name}: {status_label}"
                stage_element = f'''
                <div style="display: flex; flex-direction: column; align-items: center; margin: 0 3px;" title="{tooltip_text}">
                    <span style="font-size: 13px; line-height: 1; cursor: pointer; height: 14px; display: flex; align-items: center;">{icon}</span>
                    <span style="font-size: 8px; color: #475569; font-weight: 600; margin-top: 2px; white-space: nowrap;">{short_name}</span>
                </div>
                '''
                elements.append(stage_element)
            
            container_html = f'''
            <div style="display: flex; align-items: center; flex-wrap: nowrap; gap: 2px; overflow-x: auto; padding: 1px 0;">
                {''.join(elements)}
            </div>
            '''
            return container_html if elements else "-"
    except:
        pass
    return "-"

def parse_build_data(session, project, b_data):
    status = b_data.get('status', 'Unknown')
    result = b_data.get('result')
    build_num = b_data.get('buildNumber', 'N/A')
    real_name = b_data.get('definition', {}).get('name')
    build_id = b_data.get('id')

    env_category = None
    failed_env = None
    waiting_preprod = False

    if status == "inProgress":
        active_icon, active_label = '<div class="spinner-icon" style="margin-right: 4px;"></div> In corso...', "In corso"
        enc_proj = urllib.parse.quote(project, safe='')
        timeline_url = f"https://dev.azure.com/{ORGANIZATION}/{enc_proj}/_apis/build/builds/{build_id}/timeline?api-version=7.0"
        try:
            r = session.get(timeline_url, timeout=2.0)
            if r.status_code == 200:
                records = r.json().get('records', [])
                env_cat, f_env, wait_p = analyze_build_progress(records)
                env_category = env_cat
                failed_env = f_env
                waiting_preprod = wait_p
        except:
            pass
        final_status = active_icon

    elif status == "completed":
        enc_proj = urllib.parse.quote(project, safe='')
        timeline_url = f"https://dev.azure.com/{ORGANIZATION}/{enc_proj}/_apis/build/builds/{build_id}/timeline?api-version=7.0"
        try:
            r = session.get(timeline_url, timeout=2.0)
            if r.status_code == 200:
                records = r.json().get('records', [])
                env_cat, f_env, wait_p = analyze_build_progress(records)
                env_category = env_cat
                failed_env = f_env
                waiting_preprod = wait_p
        except:
            pass

        if result == "succeeded":
            if waiting_preprod:
                final_status = '<span style="color: #d97706; font-weight: 600;">⏳ In attesa PreProd</span>'
            elif env_category:
                final_status = f'<span class="success-bright">🟢 Succeeded ({env_category})</span>'
            else:
                final_status = '<span class="success-bright">🟢 Succeeded</span>'
        elif result == "failed":
            if failed_env:
                final_status = f'<span class="failed-bright">🔴 Failed ({failed_env})</span>'
            else:
                final_status = '<span class="failed-bright">🔴 Failed</span>'
        elif result == "canceled":
            final_status = "⚪ Canceled"
        else:
            final_status = f"🟡 {result}"
    else:
        final_status = status

    if waiting_preprod and status == "inProgress":
        final_status = '<span style="color: #d97706; font-weight: 600;">⏳ In attesa PreProd</span>'

    return build_num, final_status, real_name, build_id

pipeline_counters = {}

def process_row(row, session):
    project = clean_text(row.get('Project'))
    pipeline_input = clean_text(row.get('PipelineId'))
    change_ev = clean_text(row.get('Change Ev'))
    description_rdma = clean_text(row.get('Description RDMA'))

    if not project or not pipeline_input:
        return None

    pipe_key = pipeline_input.lower()
    is_prod_pattern = any(prod_pattern in pipe_key for prod_pattern in EXCLUDED_PROD_PIPELINES)

    if pipe_key not in pipeline_counters:
        pipeline_counters[pipe_key] = 0
    current_occurrence = pipeline_counters[pipe_key]
    pipeline_counters[pipe_key] += 1

    link_url = pipeline_input if pipeline_input.startswith("http") else ""
    val_parsed, val_type = parse_input(pipeline_input)
    enc_proj = urllib.parse.quote(project, safe='')

    def_id = None
    if pipe_key in ["paspo evolutiva", "paspo_evolutiva"]:
        link_url = "https://dev.azure.com/realeitesorg/it.grma.rdna/_build?definitionId=4413"
        def_id = "4413"
    elif pipe_key in ["paspo correttiva", "paspo_correttiva"]:
        link_url = "https://dev.azure.com/realeitesorg/it.grma.rdna/_build?definitionId=4415"
        def_id = "4415"
    elif "deploy.documentale_8emc02a_evolutiva" in pipe_key:
        link_url = "https://dev.azure.com/realeitesorg/it.ites.deploy.documentale/_build?definitionId=4998"
        def_id = "4998"
    elif "documentum-portafoglio_evolutiva" in pipe_key:
        link_url = "https://dev.azure.com/realeitesorg/it.ites.deploy.documentale/_build?definitionId=2174"
        def_id = "2174"
    elif "it.integration" in pipe_key or "4506" in pipe_key:
        def_id = "4506"
    elif "it.ites.quadient" in project.lower() and ("x_prod" in pipe_key or "quadient" in pipe_key):
        link_url = "https://dev.azure.com/realeitesorg/it.ites.quadient/_build?definitionId=651"
        def_id = "651"
    
    status_override = None
    if is_prod_pattern:
        status_override = '<span class="prod-blinking-ok">🟢 Ok in Produzione</span>'

    if not def_id:
        if val_type == "build_id":
            url = f"https://dev.azure.com/{ORGANIZATION}/{enc_proj}/_apis/build/builds/{val_parsed}?api-version=7.0"
            try:
                r = session.get(url, timeout=2.0)
                if r.status_code == 200:
                    b_data = r.json()
                    build_id_val = b_data.get('id')
                    
                    if not status_override and build_id_val and check_if_already_in_prod(session, project, build_id_val):
                        status_override = '<span class="prod-blinking-ok">🟢 Ok in Produzione</span>'

                    build_num, final_status, real_name, build_id = parse_build_data(session, project, b_data)
                    stages_html = get_stages_html(session, project, build_id)
                    
                    if not link_url:
                        link_url = f"https://dev.azure.com/{ORGANIZATION}/{enc_proj}/_build/results?buildId={val_parsed}"
                    
                    return {
                        "Progetto": project,
                        "Nome Pipeline": pipeline_input,
                        "Change Ev": change_ev,
                        "Description RDMA": description_rdma,
                        "Link": link_url,
                        "Ultima Build": build_num,
                        "Stages": stages_html,
                        "Stato Attuale": status_override if status_override else final_status
                    }
            except:
                pass
            return {"Progetto": project, "Nome Pipeline": pipeline_input, "Change Ev": change_ev, "Description RDMA": description_rdma, "Link": link_url, "Ultima Build": "-", "Stages": "-", "Stato Attuale": status_override if status_override else "❌ Errore"}

        elif val_type == "def_id":
            def_id = val_parsed
            real_name = resolve_name_from_def(project, def_id)
            pipeline_name = real_name if real_name else pipeline_input
        else:
            def_id, pipeline_name = resolve_def_from_name(project, pipeline_input)

    if not def_id:
        return {"Progetto": project, "Nome Pipeline": pipeline_input, "Change Ev": change_ev, "Description RDMA": description_rdma, "Link": link_url if link_url else "-", "Ultima Build": "-", "Stages": "-", "Stato Attuale": status_override if status_override else "⚠️ Non trovata"}

    if not link_url:
        link_url = f"https://dev.azure.com/{ORGANIZATION}/{enc_proj}/_build?definitionId={def_id}"

    url = f"https://dev.azure.com/{ORGANIZATION}/{enc_proj}/_apis/build/builds?definitions={def_id}&queryOrder=queueTimeDescending&$top=15&api-version=7.0"
    try:
        r = session.get(url, timeout=2.0)
        if r.status_code == 200:
            data = r.json()
            builds = data.get('value', [])
            if builds:
                target_build = None
                
                if "siweb" in pipe_key or "card" in pipe_key:
                    suffix = "_ITA" if current_occurrence % 2 == 0 else "_RMA"
                    for b in builds:
                        if suffix in b.get('buildNumber', ''):
                            target_build = b
                            break
                
                if not target_build:
                    target_build = builds[0]

                build_id_val = target_build.get('id')
                
                if not status_override and build_id_val and check_if_already_in_prod(session, project, build_id_val):
                    status_override = '<span class="prod-blinking-ok">🟢 Ok in Produzione</span>'

                build_num, final_status, real_name, build_id = parse_build_data(session, project, target_build)
                stages_html = get_stages_html(session, project, build_id)
                
                return {
                    "Progetto": project,
                    "Nome Pipeline": pipeline_input,
                    "Change Ev": change_ev,
                    "Description RDMA": description_rdma,
                    "Link": link_url,
                    "Ultima Build": build_num,
                    "Stages": stages_html,
                    "Stato Attuale": status_override if status_override else final_status
                }
    except:
        pass
        
    return {"Progetto": project, "Nome Pipeline": pipeline_input, "Change Ev": change_ev, "Description RDMA": description_rdma, "Link": link_url, "Ultima Build": "-", "Stages": "-", "Stato Attuale": status_override if status_override else "⚠️ Nessuna build"}

# --- ESECUZIONE ---
try:
    df = pd.read_excel(EXCEL_FILE, header=1)
        
    results = []
    session = requests.Session()
    session.auth = HTTPBasicAuth('', PAT)

    pipeline_counters.clear()

    for _, row in df.iterrows():
        res = process_row(row, session)
        if res:
            results.append(res)

    totali = len(results)
    
    succeeded_tot = sum(1 for r in results if "Succeeded" in r["Stato Attuale"])
    succ_intr1 = sum(1 for r in results if "Succeeded (INTR1)" in r["Stato Attuale"])
    succ_intr2 = sum(1 for r in results if "Succeeded (INTR2)" in r["Stato Attuale"])
    succ_sysr2 = sum(1 for r in results if "Succeeded (SYSR2)" in r["Stato Attuale"])
    succ_preprod = sum(1 for r in results if "Succeeded (PREPROD)" in r["Stato Attuale"])
    
    ko_count = sum(1 for r in results if "Failed" in r["Stato Attuale"] or "Errore" in r["Stato Attuale"])
    in_corso_count = sum(1 for r in results if "In corso" in r["Stato Attuale"])
    in_attesa_count = sum(1 for r in results if "In attesa" in r["Stato Attuale"] and "PreProd" not in r["Stato Attuale"])
    in_attesa_preprod = sum(1 for r in results if "In attesa PreProd" in r["Stato Attuale"])
    prod_ok_count = sum(1 for r in results if "Ok in Produzione" in r["Stato Attuale"])

    metrics_table_html = f"""
    <table class="metrics-table">
        <thead>
            <tr>
                <th>Totale</th>
                <th>🟢 Succeeded</th>
                <th>↳ INTR1</th>
                <th>↳ INTR2</th>
                <th>↳ SYSR2</th>
                <th>↳ PREPROD</th>
                <th>🔴 Failed</th>
                <th>🔵 In corso</th>
                <th>⏳ In attesa</th>
                <th>⏳ Attesa PreProd</th>
                <th><span class="prod-blinking-ok">🟢 In Produzione</span></th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{totali}</td>
                <td style="color: #00c853;">{succeeded_tot}</td>
                <td>{succ_intr1}</td>
                <td>{succ_intr2}</td>
                <td>{succ_sysr2}</td>
                <td>{succ_preprod}</td>
                <td style="color: #ef4444;">{ko_count}</td>
                <td style="color: #0284c7;">{in_corso_count}</td>
                <td>{in_attesa_count}</td>
                <td style="color: #d97706;">{in_attesa_preprod}</td>
                <td><span class="prod-blinking-ok">{prod_ok_count}</span></td>
            </tr>
        </tbody>
    </table>
    """
    st.html(metrics_table_html)

    filtro_stato = st.selectbox(
        "Filtra per stato:",
        [
            "Tutte", 
            "🟢 Solo Succeeded (Tutti)", 
            "↳ Succeeded (INTR1)", 
            "↳ Succeeded (INTR2)", 
            "↳ Succeeded (SYSR2)", 
            "↳ Succeeded (PREPROD)", 
            "🔴 Solo Failed (KO)", 
            "🔵 Solo In corso", 
            "⏳ Solo In attesa", 
            "⏳ Solo In attesa PreProd", 
            "🟢 Solo Ok in Produzione"
        ],
        index=0
    )

    filtered_results = results
    if filtro_stato == "🟢 Solo Succeeded (Tutti)":
        filtered_results = [r for r in results if "Succeeded" in r["Stato Attuale"]]
    elif filtro_stato == "↳ Succeeded (INTR1)":
        filtered_results = [r for r in results if "Succeeded (INTR1)" in r["Stato Attuale"]]
    elif filtro_stato == "↳ Succeeded (INTR2)":
        filtered_results = [r for r in results if "Succeeded (INTR2)" in r["Stato Attuale"]]
    elif filtro_stato == "↳ Succeeded (SYSR2)":
        filtered_results = [r for r in results if "Succeeded (SYSR2)" in r["Stato Attuale"]]
    elif filtro_stato == "↳ Succeeded (PREPROD)":
        filtered_results = [r for r in results if "Succeeded (PREPROD)" in r["Stato Attuale"]]
    elif "Failed" in filtro_stato:
        filtered_results = [r for r in results if "Failed" in r["Stato Attuale"] or "Errore" in r["Stato Attuale"]]
    elif "Solo In corso" in filtro_stato:
        filtered_results = [r for r in results if "In corso" in r["Stato Attuale"]]
    elif filtro_stato == "⏳ Solo In attesa":
        filtered_results = [r for r in results if "In attesa" in r["Stato Attuale"] and "PreProd" not in r["Stato Attuale"]]
    elif filtro_stato == "⏳ Solo In attesa PreProd":
        filtered_results = [r for r in results if "In attesa PreProd" in r["Stato Attuale"]]
    elif "Ok in Produzione" in filtro_stato:
        filtered_results = [r for r in results if "Ok in Produzione" in r["Stato Attuale"]]

    rows_html = ""
    for row in filtered_results:
        if row["Link"] and row["Link"] != "-":
            link_html = f'<a class="azure-link" href="{row["Link"]}" target="_blank" rel="opener">Azure ↗</a>'
        else:
            link_html = "-"

        rows_html += f"""<tr>
<td class="col-proj"><b>{row["Progetto"]}</b></td>
<td class="col-pipe" title="{row["Nome Pipeline"]}">{row["Nome Pipeline"]}</td>
<td class="col-change"><code>{row["Change Ev"]}</code></td>
<td class="col-desc" title="{row["Description RDMA"]}">{row["Description RDMA"]}</td>
<td class="col-link">{link_html}</td>
<td class="col-build"><code title="{row["Ultima Build"]}">{row["Ultima Build"]}</code></td>
<td class="col-stages">{row["Stages"]}</td>
<td class="col-status">{row["Stato Attuale"]}</td>
</tr>"""

    full_table_html = f"""<table class="custom-table">
<thead>
<tr>
<th class="col-proj">Progetto</th>
<th class="col-pipe">Nome Pipeline</th>
<th class="col-change">Change Ev</th>
<th class="col-desc">Description RDMA</th>
<th class="col-link">Link Azure</th>
<th class="col-build">Ultima Build</th>
<th class="col-stages">Stages</th>
<th class="col-status">Stato Attuale</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>"""

    st.html(full_table_html)

except FileNotFoundError:
    st.error(f"File **{EXCEL_FILE}** non trovato.")
except Exception as e:
    st.error(f"Errore generale: {e}")