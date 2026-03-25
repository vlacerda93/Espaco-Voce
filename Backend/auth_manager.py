import os
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Inicializa o Firebase Admin (O Cofre do Blue Team)
def initialize_firebase():
    """Inicializa o app do Firebase Admin se ainda não foi inicializado."""
    try:
        # Verifica se já existe um app inicializado para evitar erros de re-inicialização
        firebase_admin.get_app()
    except ValueError:
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        if service_account_path and os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print("🛡️ Firebase Admin inicializado com sucesso.")
        else:
            print("⚠️ Aviso: Arquivo Service Account não encontrado. Algumas funções de Auth podem falhar.")

# Chama na importação do módulo
initialize_firebase()

def verify_google_token(id_token: str):
    """
    Valida o login do usuário usando o Token de ID enviado pelo frontend.
    Retorna os dados do usuário decodificados (uid, email, name) ou None em caso de erro.
    """
    try:
        # Verifica e decodifica o token
        decoded_token = auth.verify_id_token(id_token)
        print(f"✅ Token validado para o usuário: {decoded_token.get('email')}")
        return decoded_token
    except auth.ExpiredIdTokenError:
        print("❌ Erro: O Token do Google expirou.")
        return {"error": "Token expirado. Por favor, faça login novamente."}
    except auth.InvalidIdTokenError:
        print("❌ Erro: Token do Google inválido.")
        return {"error": "Token de autenticação inválido."}
    except Exception as e:
        print(f"❌ Erro crítico de Autenticação: {e}")
        return {"error": f"Falha na verificação: {str(e)}"}

if __name__ == "__main__":
    # Teste de importação e inicialização
    print("Módulo de Autenticação Ativo.")
