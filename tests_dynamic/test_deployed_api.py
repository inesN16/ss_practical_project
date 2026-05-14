import requests
import os

BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")

def test_unauthenticated_user_cannot_access_documents():
    """Verifica se um utilizador sem login é bloqueado em páginas sensíveis."""
    response = requests.get(f"{BASE_URL}/documents", allow_redirects=False)
    # Deve dar 302 (redirecionar para login) ou 401/403
    assert response.status_code in (302, 303, 401, 403)

def test_student_cannot_access_admin_area():
    """Verifica se um utilizador 'student' não consegue entrar na área de admin."""
    session = requests.Session()
    # Login como alice (estudante) - USA A PASSWORD QUE DEFINISTE NO TEU PROJETO
    login_data = {"username": "alice", "password": "tth1mJj5?£58"} 
    session.post(f"{BASE_URL}/login", data=login_data)
    
    # Tenta aceder a uma rota que deveria ser só para profs/admin (ajusta o URL se necessário)
    response = session.get(f"{BASE_URL}/admin", allow_redirects=False)
    assert response.status_code in (302, 303, 403)

def test_path_traversal_attack_blocked():
    """Verifica se o sistema bloqueia tentativas de ler ficheiros fora da pasta permitida."""
    # Simula um ataque de Path Traversal no endpoint de ficheiros
    payloads = ["../../etc/passwd", "..%2f..%2fetc%2fpasswd", "/etc/passwd"]
    
    for path in payloads:
        response = requests.get(f"{BASE_URL}/files", params={"path": path})
        # O sistema deve rejeitar (400) ou dizer que não encontrou/não tem autorização
        assert response.status_code in (400, 403, 404)


def test_logout_invalidates_session():
    """Verifica se o logout realmente termina a sessão[cite: 184]."""
    session = requests.Session()
    session.post(f"{BASE_URL}/login", data={"username": "alice", "password": "tth1mJj5?£58"})
    
    # Faz logout
    session.get(f"{BASE_URL}/logout")
    
    # Tenta aceder novamente
    response = session.get(f"{BASE_URL}/documents", allow_redirects=False)
    assert response.status_code in (302, 303, 401), "Sessão ainda ativa após logout!" [cite: 185]

def test_invalid_document_id_format():
    """Verifica se IDs malformados são rejeitados[cite: 251, 273]."""
    # Tentar aceder a um documento com ID que não é número
    response = requests.get(f"{BASE_URL}/documents/abc")
    assert response.status_code in (400, 404), "ID inválido não foi rejeitado corretamente" [cite: 277]