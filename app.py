import streamlit as st
import requests
import json
import os
import hashlib
import time

# --- ARQUIVOS DE DADOS (BANCO DE DADOS JSON) ---
DB_SISTEMAS = "sistemas_taxbase.json"
DB_USUARIOS = "usuarios_taxbase.json"

# --- CREDENCIAIS PADRÃO DO ADM MASTER ---
# Lembrete: Se já rodou o script antes, apague 'usuarios_taxbase.json' para resetar a senha.
ADM_EMAIL = "admin@taxbase.com.br"
ADM_SENHA_PADRAO = "Taxbase2025"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Taxbase Hub", page_icon="🔷", layout="wide")

# --- CSS CUSTOMIZADO (VISUAL) ---
st.markdown("""
    <style>
    /* 1. Remover itens padrão do Streamlit */
    div[data-testid="stToolbar"] {visibility: hidden; height: 0%; position: fixed;}
    div[data-testid="stDecoration"] {visibility: hidden; height: 0%; position: fixed;}
    div[data-testid="stStatusWidget"] {visibility: hidden; height: 0%; position: fixed;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 2. Variáveis de Cores Taxbase */
    :root { 
        --taxbase-blue: #009BD6; 
        --taxbase-dark: #2C3E50; 
        --bg-color: #F8F9FA; 
        --border-color-padrao: #E0E0E0;
    }
    .stApp { background-color: var(--bg-color); }
    h1, h2, h3, h4, h5 { color: var(--taxbase-dark) !important; }

    /* 3. Estilo dos Botões de Ação */
    div.stButton > button {
        background-color: var(--taxbase-blue);
        color: white; 
        border-radius: 10px; 
        border: none;
        white-space: pre-wrap !important; 
        min-height: 60px; 
        line-height: 1.4 !important;
        width: 100%;
        transition: all 0.2s;
    }
    div.stButton > button:hover { 
        background-color: #007CA3; 
        color: white; 
        transform: scale(1.02);
    }

    /* 4. Estilo dos Cartões */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: white; 
        padding: 1.2rem; 
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid var(--border-color-padrao);
    }

    /* 5. CORREÇÃO DEFINITIVA DA BORDA DOS CAMPOS DE TEXTO */
    /* Altera a cor do cursor */
    input, textarea {
        caret-color: var(--taxbase-blue) !important;
    }
    /* Mira o contêiner principal do input e força a cor da borda */
    div[data-baseweb="base-input"] {
        border-color: var(--border-color-padrao) !important;
        transition: all 0.2s !important;
    }
    /* Quando o campo está em foco (clicado) ou com o mouse em cima */
    div[data-baseweb="base-input"]:focus-within,
    div[data-baseweb="base-input"]:hover {
        border-color: var(--taxbase-blue) !important;
        box-shadow: 0 0 0 1px var(--taxbase-blue) !important; /* Cria um brilho azul */
        outline: none !important;
    }
    </style>
    """, unsafe_allow_html=True)


# --- FUNÇÕES DE SEGURANÇA E ARQUIVOS ---
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def carregar_json(arquivo):
    if not os.path.exists(arquivo): return []
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# --- VERIFICAÇÃO INICIAL (CRIAR ADMIN SE NÃO EXISTIR) ---
if not os.path.exists(DB_USUARIOS) or not carregar_json(DB_USUARIOS):
    usuarios_iniciais = [{
        "email": ADM_EMAIL,
        "senha": hash_senha(ADM_SENHA_PADRAO)
    }]
    salvar_json(DB_USUARIOS, usuarios_iniciais)


# --- FUNÇÕES DE LÓGICA ---
def verificar_login(email, senha):
    usuarios = carregar_json(DB_USUARIOS)
    senha_hash = hash_senha(senha)
    for u in usuarios:
        if u['email'] == email and u['senha'] == senha_hash:
            return True
    return False


def criar_novo_usuario(email, senha):
    usuarios = carregar_json(DB_USUARIOS)
    if any(u['email'] == email for u in usuarios):
        return False, "E-mail já cadastrado."
    usuarios.append({"email": email, "senha": hash_senha(senha)})
    salvar_json(DB_USUARIOS, usuarios)
    return True, "Usuário criado com sucesso!"


@st.cache_data(ttl=60)
def check_ping(url):
    try:
        r = requests.get(url, timeout=2)
        return True if r.status_code == 200 else False
    except:
        return False


def obter_status_sistema(sistema):
    modo = sistema.get("status_manual", "Automático")
    if modo == "Manutenção":
        return "🟠 Manutenção", "orange"
    elif modo == "Forçar Offline":
        return "🔴 Offline", "red"
    elif modo == "Forçar Online":
        return "🟢 Online", "green"
    else:
        online = check_ping(sistema['url'])
        return ("🟢 Online", "green") if online else ("🔴 Offline", "red")


# --- CONTROLE DE SESSÃO ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario_atual' not in st.session_state: st.session_state['usuario_atual'] = ""

# ==============================================================================
# 1. TELA DE LOGIN
# ==============================================================================
if not st.session_state['logado']:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("")
        st.write("")
        st.write("")
        with st.container(border=True):
            try:
                st.image("Sem-nome-172-x-50-px-1.png", width=200)
            except:
                st.markdown("## 🔷 Taxbase Hub")

            st.markdown("##### Acesso Restrito")

            email_login = st.text_input("E-mail corporativo")
            senha_login = st.text_input("Senha", type="password")

            if st.button("Entrar no Hub", use_container_width=True):
                if verificar_login(email_login, senha_login):
                    st.session_state['logado'] = True
                    st.session_state['usuario_atual'] = email_login
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
    st.stop()

# ==============================================================================
# 2. ÁREA LOGADA
# ==============================================================================
SISTEMAS = carregar_json(DB_SISTEMAS)
usuario_atual = st.session_state['usuario_atual']
is_admin_master = (usuario_atual == ADM_EMAIL)


# --- MODAL (POP-UP) ---
@st.dialog("⚙️ Painel de Gestão")
def abrir_painel_gestao():
    lista_abas = ["➕ Novo Sistema", "✏️ Editar/Excluir"]
    if is_admin_master:
        lista_abas.append("👤 Novo Usuário")

    tabs = st.tabs(lista_abas)

    # ABA 1: ADICIONAR
    with tabs[0]:
        st.caption("Preencha para adicionar um novo atalho.")
        with st.form("form_novo_sys", clear_on_submit=True):
            f_nome = st.text_input("Nome do Sistema")
            f_url = st.text_input("URL (Link Completo)")
            f_cat = st.text_input("Categoria (Ex: Fiscal, RH)")
            f_desc = st.text_input("Descrição Curta")

            if st.form_submit_button("Salvar Sistema"):
                if f_nome and f_url:
                    SISTEMAS.append({
                        "nome": f_nome, "url": f_url, "categoria": f_cat,
                        "desc": f_desc, "status_manual": "Automático"
                    })
                    salvar_json(DB_SISTEMAS, SISTEMAS)
                    st.success("Adicionado com sucesso!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Nome e URL são obrigatórios.")

    # ABA 2: EDITAR / EXCLUIR
    with tabs[1]:
        if not SISTEMAS:
            st.info("Nenhum sistema cadastrado.")
        else:
            opcoes = [f"{i}: {s['nome']}" for i, s in enumerate(SISTEMAS)]
            sel = st.selectbox("Selecione para editar:", options=opcoes)

            if sel:
                idx = int(sel.split(":")[0])
                sis = SISTEMAS[idx]

                st.markdown(f"**Editando:** {sis['nome']}")
                st.caption("Controle de Status (TI)")
                st_atual = sis.get("status_manual", "Automático")
                l_st = ["Automático", "Manutenção", "Forçar Online", "Forçar Offline"]
                novo_st = st.selectbox("Status:", l_st, index=l_st.index(st_atual))

                c_salvar, c_del = st.columns(2)
                if c_salvar.button("💾 Atualizar Status"):
                    SISTEMAS[idx]["status_manual"] = novo_st
                    salvar_json(DB_SISTEMAS, SISTEMAS)
                    st.success("Atualizado!")
                    time.sleep(1)
                    st.rerun()

                if c_del.button("🗑️ Excluir Sistema", type="primary"):
                    SISTEMAS.pop(idx)
                    salvar_json(DB_SISTEMAS, SISTEMAS)
                    st.rerun()

    # ABA 3: USUÁRIOS
    if is_admin_master and len(tabs) > 2:
        with tabs[2]:
            st.caption("Cadastrar acesso para equipe.")
            with st.form("form_user", clear_on_submit=True):
                u_mail = st.text_input("E-mail")
                u_pass = st.text_input("Senha Temporária")
                if st.form_submit_button("Criar Usuário"):
                    ok, msg = criar_novo_usuario(u_mail, u_pass)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


# --- TELA PRINCIPAL ---
col_logo, col_titulo, col_botoes = st.columns([1, 3, 1.5])

with col_logo:
    try:
        st.image("Sem-nome-172-x-50-px-1.png", width=160)
    except:
        st.write("🟦 Taxbase")

with col_titulo:
    st.markdown("### Hub Corporativo")
    st.markdown(f"<small style='color:gray'>Logado como: {usuario_atual}</small>", unsafe_allow_html=True)

with col_botoes:
    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚙️\nGestão", use_container_width=True):
            abrir_painel_gestao()
    with b2:
        if st.button("🚪\nSair", use_container_width=True):
            st.session_state['logado'] = False
            st.session_state['usuario_atual'] = ""
            st.rerun()

st.divider()

# --- FILTRO E LISTAGEM ---
busca = st.text_input("🔎", placeholder="Buscar sistema...", label_visibility="collapsed").lower()

sistemas_finais = [
    s for s in SISTEMAS
    if busca in s['nome'].lower() or busca in s['categoria'].lower() or busca in s['desc'].lower()
]

if not sistemas_finais:
    st.info("Nenhum sistema encontrado.")
else:
    cols = st.columns(3)
    for i, sis in enumerate(sistemas_finais):
        with cols[i % 3]:
            with st.container(border=True):
                txt_status, cor_status = obter_status_sistema(sis)

                l1_col1, l1_col2 = st.columns([3, 1])
                l1_col1.subheader(sis['nome'])
                l1_col2.markdown(
                    f"<div style='text-align:right; color:{cor_status}; font-weight:bold; font-size:1.2em'>●</div>",
                    unsafe_allow_html=True)

                st.caption(f"📂 {sis['categoria']}")
                st.write(f"<small>{sis['desc']}</small>", unsafe_allow_html=True)
                st.write("")
                st.link_button("Acessar Sistema", sis['url'], use_container_width=True)
                st.markdown(
                    f"<div style='text-align:center; color:{cor_status}; font-size:0.8em; margin-top:5px'>{txt_status}</div>",
                    unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align:center; color:#AAA'><small>© 2026 Taxbase • Tecnologia</small></div>",
            unsafe_allow_html=True)