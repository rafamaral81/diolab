import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import uuid
import json
import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Handle case where python-dotenv is not installed
    pass

# Configure SQL availability - set to False since we can't install pymssql
SQL_AVAILABLE = False

# Azure Blob Storage configuration
blobconnectionstring = os.getenv("BLOB_CONNECTION_STRING")
blobcontainername = os.getenv("BLOB_CONTAINER_NAME")
blobaccountname = os.getenv("BLOB_ACCOUNT_NAME")

# Initialize session state for products if it doesn't exist
if 'products' not in st.session_state:
    st.session_state.products = []

#save image on blob storage
def upload_blob(file):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(blobconnectionstring)
        container_client = blob_service_client.get_container_client(blobcontainername)
        blob_name = str(uuid.uuid4()) + "_" + file.name
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(file, overwrite=True)
        image_url = f"https://{blobaccountname}.blob.core.windows.net/{blobcontainername}/{blob_name}"
        return image_url
    except Exception as e:
        st.error(f"Erro ao fazer upload da imagem: {e}")
        return ""

#insert product into local storage
def insert_product(product_name, product_description, product_price, product_image):
    try:
        # Validate input
        if not product_name:
            st.warning("O nome do produto é obrigatório.")
            return False
            
        # Process image if provided
        image_url = ""
        if product_image:
            image_url = upload_blob(product_image)
            
        # Create a new product with timestamp and ID
        new_product = {
            'id': len(st.session_state.products) + 1,
            'name': product_name,
            'description': product_description,
            'price': product_price,
            'image_url': image_url,
            'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to session state
        st.session_state.products.append(new_product)
        return True
    except Exception as e:  
        st.error(f"Erro ao cadastrar produto: {e}")
        return False
    
def list_products():
    try:
        # Return products from session state
        return st.session_state.products
    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")
        return []

# mostrar na tela os produtos cadastrados
def list_products_screen():
    products = list_products()
    if products:
        # Create a grid layout for products
        cols = st.columns(3)
        for idx, product in enumerate(products):
            with cols[idx % 3]:
                st.subheader(product['name'])
                st.write(f"**Descrição:** {product['description']}")
                st.write(f"**Preço:** R$ {product['price']:.2f}")
                if product['image_url']:
                    st.image(product['image_url'], use_column_width=True)
                st.caption(f"ID: {product['id']} | Criado em: {product['created_at']}")
                st.divider()
    else:
        st.info("Nenhum produto cadastrado.")
        
# Export products to JSON file
def export_products():
    try:
        if st.session_state.products:
            export_data = json.dumps(st.session_state.products, indent=4)
            st.download_button(
                label="Baixar produtos como JSON",
                data=export_data,
                file_name="produtos_exportados.json",
                mime="application/json"
            )
        else:
            st.info("Não há produtos para exportar.")
    except Exception as e:
        st.error(f"Erro ao exportar produtos: {e}")

# Import products from JSON file
def import_products():
    uploaded_file = st.file_uploader("Carregar produtos de um arquivo JSON", type=["json"])
    if uploaded_file is not None:
        try:
            content = uploaded_file.read()
            data = json.loads(content)
            st.session_state.products = data
            st.success(f"Importados {len(data)} produtos com sucesso!")
        except Exception as e:
            st.error(f"Erro ao importar produtos: {e}")

# Create tabs for different functionality
tab1, tab2, tab3 = st.tabs(["Cadastrar", "Listar", "Importar/Exportar"])

with tab1:
    st.header("Cadastro de Produtos")
    product_name = st.text_input("Nome do Produto")
    product_description = st.text_area("Descrição do Produto")
    product_price = st.number_input("Preço do Produto", min_value=0.0, format="%.2f")
    product_image = st.file_uploader("Imagem do Produto", type=["jpg", "jpeg", "png"])
    
    if st.button("Cadastrar Produto"):
        if insert_product(product_name, product_description, product_price, product_image):
            st.success("Produto cadastrado com sucesso!")
        
with tab2:
    st.header("Produtos Cadastrados")
    if st.button("Atualizar Lista"):
        pass  # Just a trigger to refresh the page
    list_products_screen()
        
with tab3:
    st.header("Importar/Exportar Dados")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Exportar")
        export_products()
        
    with col2:
        st.subheader("Importar")
        import_products()