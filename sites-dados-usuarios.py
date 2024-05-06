import firebase_admin
from firebase_admin import credentials, firestore

import streamlit as st
import re
import pandas as pd

# Função para validar o formato do email
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Função para verificar se o número de telefone já existe
def is_phone_number_exists(number, ref):
    user_data = ref.where('number', '==', number).get()
    return len(user_data) > 0

# Função para adicionar dados do usuário ao Firebase
def add_userdata(name, email, number, problema, cod_matricula, ref):
    ref.add({
        'name': name,
        'email': email,
        'number': number,
        'problema': problema,
        'cod_matricula': cod_matricula
    })

# Função para obter todos os dados do Firebase
def get_all_data(ref):
    return ref.stream()

# Inicialize o SDK Firebase apenas uma vez
if not firebase_admin._apps:
    cred = credentials.Certificate("banco-de-dados-technos-firebase-adminsdk-tpj1r-129abfded5.json") # Substitua pelo caminho para o arquivo de chave de serviço
    firebase_admin.initialize_app(cred)

# Referência para a coleção "users" no Firestore
db = firestore.client()
ref = db.collection('users')

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

# Interface do Streamlit
st.title("Registro de dados Cliente Technos")
name = st.text_input('Nome')
email = st.text_input('Email')
number = st.text_input('Numero')
problema = st.text_input('Problema')
cod_matricula = st.text_input('Cod. Matricula')

# Verifica se todos os campos estão preenchidos e se o email é válido
if st.button('Enviar dados'):
    if not name or not email or not number or not problema or not cod_matricula:
        st.error("Preencha todos os campos")
    elif not is_valid_email(email):
        st.error("Por favor, insira um endereço de e-mail válido.")
    elif is_phone_number_exists(number, ref):
        st.error("O número de telefone já existe.")
    else:
        try:
            add_userdata(name, email, number, problema, cod_matricula, ref)
            st.success("Registro concluído")
        except Exception as e:
            st.error(f"Ocorreu um erro: {str(e)}")

# Mostra todos os dados enviados, se solicitado
if st.checkbox('Ver todos os dados enviados'):
    try:
        data = get_all_data(ref)
        for doc in data:
            st.write(f'ID: {doc.id}, Nome: {doc.to_dict()["name"]}, Email: {doc.to_dict()["email"]}, Numero: {doc.to_dict()["number"]}, Problema: {doc.to_dict()["problema"]}, Cod. Matricula: {doc.to_dict()["cod_matricula"]}')
    except Exception as e:
        st.error(f"Ocorreu um erro: {str(e)}")

# Botão para gerar arquivo CSV
if st.button('Gerar Planilha'):
    try:
        data = get_all_data(ref)
        data_list = [doc.to_dict() for doc in data]
        df = pd.DataFrame(data_list)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="dados_usuarios_technos.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o arquivo CSV: {str(e)}")
