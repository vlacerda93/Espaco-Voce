import os
from cryptography.fernet import Fernet

class DataSecurity:
    def __init__(self):
        # Lê a chave que geramos lá no passo 1.2
        self.key = os.getenv('DB_ENCRYPTION_KEY')
        if not self.key:
            raise ValueError("ERRO: DB_ENCRYPTION_KEY não encontrada no ambiente!")
        self.cipher = Fernet(self.key.encode())

    def encrypt_data(self, plain_text: str) -> str:
        """Transforma texto comum em um hash ilegível."""
        return self.cipher.encrypt(plain_text.encode()).decode()

    def decrypt_data(self, cipher_text: str) -> str:
        """Transforma o hash de volta em texto legível."""
        return self.cipher.decrypt(cipher_text.encode()).decode()

# Instância pronta para uso
security = DataSecurity()
