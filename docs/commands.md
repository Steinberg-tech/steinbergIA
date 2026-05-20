# Comandos Disponíveis

Estes comandos podem ser enviados como mensagem no chat e são processados diretamente pelo sistema (não passam pela IA).

## /reset

**O que faz:** Apaga toda a memória da sessão atual — histórico de conversa, estado de fluxo e dados persistentes do usuário (nome, pedido, preferências).

**Quando usar:** Ideal para testes ou quando o usuário quiser começar uma conversa do zero.

**Exemplo de uso:**
```
Usuário: /reset
Sistema: Memória resetada com sucesso. Pode começar uma nova conversa!
```

**O que é limpo:**
- Memória de sessão (estado de workflow, última intenção detectada)
- Memória de usuário (nome, último pedido, preferências persistentes)
- Conversa ativa marcada como resolvida (próxima mensagem inicia nova conversa com histórico zerado)
