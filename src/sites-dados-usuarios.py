import firebase_admin
from firebase_admin import credentials, firestore, auth
import streamlit as st
import re
import pandas as pd
from dotenv import load_dotenv
import os
from io import BytesIO

# Carrega as variáveis do arquivo .env
load_dotenv()

# Obtém as variáveis de ambiente do Firebase
firebase_type = os.getenv("FIREBASE_TYPE")
firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
firebase_private_key_id = os.getenv("FIREBASE_PRIVATE_KEY_ID")
firebase_private_key = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n").strip()
firebase_client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
firebase_client_id = os.getenv("FIREBASE_CLIENT_ID")
firebase_auth_uri = os.getenv("FIREBASE_AUTH_URI")
firebase_token_uri = os.getenv("FIREBASE_TOKEN_URI")
firebase_auth_provider_x509_cert_url = os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL")
firebase_client_x509_cert_url = os.getenv("FIREBASE_CLIENT_X509_CERT_URL")

# Depuração: Exibir as credenciais

# Função para validar o formato do email
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Função para verificar se o número de telefone já existe
def is_phone_number_exists(number, ref):
    user_data = ref.where('number', '==', number).get()
    return len(user_data) > 0

# Função para adicionar dados do usuário ao Firebase
def add_userdata(name, email, number, problema, cursosetor, ref):
    ref.add({
        'name': name,
        'email': email,
        'number': number,
        'problema': problema,
        'curso/setor': cursosetor
    })

# Função para obter todos os dados do Firebase
def get_all_data(ref):
    return ref.stream()

# Função para deletar um usuário pelo ID
def delete_user(user_id, ref):
    ref.document(user_id).delete()

# Inicialize o SDK Firebase apenas uma vez
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate({
            "type": firebase_type,
            "project_id": firebase_project_id,
            "private_key_id": firebase_private_key_id,
            "private_key": firebase_private_key,
            "client_email": firebase_client_email,
            "client_id": firebase_client_id,
            "auth_uri": firebase_auth_uri,
            "token_uri": firebase_token_uri,
            "auth_provider_x509_cert_url": firebase_auth_provider_x509_cert_url,
            "client_x509_cert_url": firebase_client_x509_cert_url
        })
        firebase_admin.initialize_app(cred)
        st.write("Firebase initialized successfully.")
    except Exception as e:
        st.error(f"Failed to initialize Firebase: {e}")

# Referência para a coleção "users" no Firestore
db = firestore.client()
ref = db.collection('users')

# Página de login
def login_page():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Senha", type='password')

    if st.button("Login"):
        try:
            user = auth.get_user_by_email(email)
            st.success(f"Bem-vindo, {user.email}")
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = email
        except:
            st.error("Erro de autenticação. Verifique suas credenciais.")

# Configuração de estilo do Streamlit
st.markdown("""
    <style>
    body {
        background-color: #000000;
    }
    .stTextInput input {
        transition: all 0.3s ease;
    }
    .stTextInput input:focus {
        border-color: #4d90fe;
        box-shadow: inset 0 1px 1px rgba(0,0,0,0.075),0 0 8px rgba(77,144,254,0.6);
    }
    </style>
    """, unsafe_allow_html=True)

# Autenticação do usuário
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    # Interface do Streamlit para usuários autenticados
    st.title("Registro de dados Cliente Technos")
    name = st.text_input('Nome')
    email = st.text_input('Email')
    number = st.text_input('Numero')
    problema = st.text_input('Problema')
    curso_setor = st.text_input('curso/setor')

    # Verifica se todos os campos estão preenchidos e se o email é válido
    if st.button('Enviar dados'):
        if not name or not email or not number or not problema or not curso_setor:
            st.error("Preencha todos os campos")
        elif not is_valid_email(email):
            st.error("Por favor, insira um endereço de e-mail válido.")
        elif is_phone_number_exists(number, ref):
            st.error("O número de telefone já existe.")
        else:
            try:
                add_userdata(name, email, number, problema, curso_setor, ref)
                st.success("Registro concluído")
            except Exception as e:
                st.error(f"Ocorreu um erro: {str(e)}")

    # Mostra todos os dados enviados, se solicitado
    if st.checkbox('Ver todos os dados enviados'):
        try:
            data = get_all_data(ref)
            for doc in data:
                st.write(f' Nome: {doc.to_dict()["name"]}, Email: {doc.to_dict()["email"]}, Numero: {doc.to_dict()["number"]}, Problema: {doc.to_dict()["problema"]}, Curso/Setor: {doc.to_dict()["curso/setor"]}')
                if st.button(f'Deletar', key=doc.id):
                    delete_user(doc.id, ref)
                    st.success(f'Usuário deletado')
        except Exception as e:
            st.error(f"Ocorreu um erro: {str(e)}")

    # Botão para gerar arquivo Excel
    if st.button('Gerar Planilha'):
        try:
            data = get_all_data(ref)
            data_list = [doc.to_dict() for doc in data]
            df = pd.DataFrame(data_list)
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            st.download_button(
                label="Download Excel",
                data=buffer,
                file_name="dados_usuarios_technos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar o arquivo Excel: {str(e)}")

    # Botão para fazer upload de uma planilha
    uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            for index, row in df.iterrows():
                if is_valid_email(row['email']) and not is_phone_number_exists(row['number'], ref):
                    add_userdata(row['name'], row['email'], row['number'], row['problema'], row['curso/setor'], ref)
            st.success("Dados inseridos no banco de dados com sucesso.")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {str(e)}")
