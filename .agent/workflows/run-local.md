---
description: Como abrir o app no localhost pelo terminal (passo a passo)
---
1) Vá para a pasta do projeto
Se o rxconfig.py está em App:
```bash
cd /home/vinicius/Documentos/Ikigai/espaco_voce/App
```

2) Ative virtualenv (opcional, mas recomendado)
```bash
source /home/vinicius/Documentos/Ikigai/espaco_voce/.venv/bin/activate
```

3) Rode Reflex
```bash
python3 -m reflex run
```
ou, se estiver no diretório raiz:
```bash
python3 -m reflex run --env App
```

4) Abra o navegador
http://localhost:3000
(ou 3001/3002 se ele indicar outras portas no log)

🛑 Se der “port already in use”
```bash
lsof -ti:3000 | xargs kill -9
python3 -m reflex run
```

💡 Dica rápida para testes
- `pwd` (confirme raiz App)
- `ps aux | grep reflex` (veja se já tem processo)
- `curl -I localhost:3000` (checa se servidor responde)
