def render(template: str, **kwargs) -> str:
    """Simple template renderer using str.format_map with safe defaults."""
    return template.format_map(_SafeDict(**kwargs))


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


CONTEXT_INJECTION = """
Informações do cliente:
- Sessão: {session_id}
- Nome: {user_name}

Histórico recente:
{history_summary}
"""

ORDER_STATUS_TEMPLATE = """
Pedido #{order_id}
Status: {status}
Previsão de entrega: {estimated_delivery}
Transportadora: {carrier}
Código de rastreio: {tracking_code}
"""

TICKET_CREATED_TEMPLATE = """
Chamado registrado com sucesso!
Protocolo: {protocol}
Previsão de retorno: {sla}
Você receberá uma atualização em breve.
"""
