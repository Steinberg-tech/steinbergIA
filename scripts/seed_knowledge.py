"""
Seeds the knowledge base with initial FAQ content.
Run: python scripts/seed_knowledge.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.settings import settings
from modules.knowledge.embeddings import EmbeddingGenerator
from modules.knowledge.repository import KnowledgeRepository
from modules.knowledge.service import KnowledgeService
from modules.knowledge.vector_store import VectorStore

FAQ_CONTENT = [
    {
        "title": "O que é o Escritório Steinberg?",
        "content": "O Escritório Steinberg Advogados Associados é especializado em Direito Bancário. "
                   "Atuamos em casos de cartão de crédito consignado não reconhecido (RCC), "
                   "reserva de margem de cartão (RMC) e contratos bancários passíveis de anulação. "
                   "Atendemos clientes em todo o Brasil, com foco no Norte e Nordeste.",
        "source": "Institucional",
    },
    {
        "title": "Horário de atendimento",
        "content": "Nossa equipe humana atende de segunda a sexta, das 9h às 17h. "
                   "Fora desse horário, a Helena (assistente virtual) continua disponível para tirar dúvidas. "
                   "Transferências para advogados são tratadas no próximo dia útil quando feitas fora do expediente.",
        "source": "Operacional",
    },
    {
        "title": "Quais casos o escritório atende?",
        "content": "Atendemos exclusivamente casos de Direito Bancário: "
                   "1) Cartão de crédito consignado não reconhecido (RCC) — quando o cliente não reconhece ter contratado; "
                   "2) Reserva de Margem de Cartão (RMC) — desconto indevido no benefício; "
                   "3) Contratos bancários não reconhecidos ou passíveis de anulação. "
                   "Casos de outras áreas (trabalhista, previdenciário, família) não são atendidos.",
        "source": "Escopo de atuação",
    },
    {
        "title": "Fases do processo bancário — do início ao recebimento",
        "content": "O processo bancário passa pelas seguintes etapas: "
                   "1. Recebimento e checagem dos documentos (1 dia); "
                   "2. Elaboração da pasta e cálculo (1 dia); "
                   "3. Elaboração da petição inicial (5 dias); "
                   "4. Revisão da petição (3 dias); "
                   "5. Distribuição da ação no tribunal (1 dia); "
                   "6. Réplica ou prazo intermediário e audiência de conciliação (1 a 2 meses); "
                   "7. Alegações finais (3 meses); "
                   "8. Julgamento (8 meses a 1 ano); "
                   "9. Recursos (6 meses); "
                   "10. Cumprimento da sentença e recebimento (1 ano). "
                   "O tempo total pode variar conforme o tribunal.",
        "source": "Processo interno",
    },
    {
        "title": "Marcos importantes que comunicamos ao cliente",
        "content": "O escritório entra em contato com o cliente nas seguintes etapas importantes: "
                   "recebimento da pasta, distribuição da ação no tribunal, data da audiência, "
                   "sentença do juiz, acórdão (decisão do tribunal em caso de recurso) e "
                   "cumprimento da sentença (hora de receber). "
                   "Caso passe mais de 2 meses sem movimentação relevante, o cliente também é informado.",
        "source": "Comunicação ao cliente",
    },
    {
        "title": "O que é RCC e RMC?",
        "content": "RCC é o Cartão de Crédito Consignado — um cartão de crédito cujas faturas são descontadas "
                   "direto do benefício do INSS ou salário. "
                   "RMC é a Reserva de Margem Consignada — um valor reservado na margem do benefício para "
                   "um cartão de crédito. "
                   "Muitas pessoas não sabem que contrataram esses produtos ou foram enganadas. "
                   "Nesses casos, é possível entrar com ação judicial para cancelar e recuperar os valores.",
        "source": "Conteúdo técnico bancário",
    },
    {
        "title": "O que é necessário para abrir um caso?",
        "content": "Para análise inicial do caso bancário, precisamos saber: "
                   "se o senhor(a) reconhece o contrato; se recebeu e usou o cartão; "
                   "se a contratação foi presencial ou online; se tem cópia do contrato; "
                   "se foi informado de que era um cartão consignado; "
                   "e se já tentou resolver diretamente com o banco. "
                   "Com essas informações, nossa equipe analisa se o caso pode ser aceito.",
        "source": "Triagem de leads",
    },
    {
        "title": "Por que meu benefício está com desconto?",
        "content": "Descontos no benefício do INSS podem ser por empréstimo consignado ou cartão consignado. "
                   "Se o senhor(a) não reconhece esse desconto ou não autorizou, pode ser um caso de cobrança indevida. "
                   "Entre em contato conosco para analisarmos o seu extrato do INSS e verificar se há irregularidade.",
        "source": "Dúvidas frequentes",
    },
    {
        "title": "Quanto tempo demora para receber?",
        "content": "O tempo total de um processo bancário varia bastante — pode levar de 1 a 3 anos, dependendo do tribunal. "
                   "As etapas mais demoradas são o julgamento (8 meses a 1 ano) e o cumprimento da sentença (1 ano). "
                   "Não é possível dar uma data exata, mas mantemos o senhor(a) informado a cada passo importante.",
        "source": "Dúvidas frequentes",
    },
    {
        "title": "O escritório cobra para analisar o caso?",
        "content": "A análise inicial é feita pela nossa equipe. "
                   "Para informações sobre honorários e condições do contrato, "
                   "é necessário falar diretamente com um dos nossos advogados. "
                   "Nossa equipe atende de segunda a sexta, das 9h às 17h.",
        "source": "Comercial",
    },
    {
        "title": "Como enviar documentos para o escritório?",
        "content": "O senhor(a) pode enviar os documentos diretamente por aqui pelo WhatsApp, em foto ou PDF. "
                   "Documentos que geralmente precisamos: documento de identidade (RG ou CPF), "
                   "extrato do INSS ou contracheque, e cópia do contrato (se tiver). "
                   "Após o envio, nossa equipe analisa e o advogado responsável entra em contato se precisar de mais informações.",
        "source": "Operacional",
    },
    {
        "title": "Não consigo falar com meu advogado, o que faço?",
        "content": "Nossa equipe atende de segunda a sexta, das 9h às 17h. "
                   "Se o senhor(a) enviou mensagem fora desse horário, será atendido no próximo dia útil. "
                   "Se preferir, posso registrar sua dúvida agora e garantir que o advogado responsável retorne o contato.",
        "source": "Operacional",
    },
]


async def seed():
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        async with session.begin():
            service = KnowledgeService(
                repo=KnowledgeRepository(session),
                vector_store=VectorStore(),
                embeddings=EmbeddingGenerator(),
            )
            for item in FAQ_CONTENT:
                doc_id = await service.add_document(
                    title=item["title"],
                    content=item["content"],
                    source=item.get("source"),
                )
                print(f"  Indexed: {item['title']} (id={doc_id})")

    await engine.dispose()
    print(f"\nSeeded {len(FAQ_CONTENT)} documents into knowledge base.")


if __name__ == "__main__":
    asyncio.run(seed())
