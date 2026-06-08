from modules.integrations.projuris.phone import phone_candidates


def test_formato_com_pontuacao():
    assert phone_candidates("(85)9 9708-5202") == ["85997085202", "8597085202"]


def test_formato_com_espaco():
    assert phone_candidates("85 99708-5202") == ["85997085202", "8597085202"]


def test_ja_normalizado():
    assert phone_candidates("85997085202") == ["85997085202", "8597085202"]


def test_digisac_com_codigo_pais():
    # 558597085202 -> tira 55 -> 8597085202 (10 díg) -> insere o 9
    assert phone_candidates("558597085202") == ["85997085202", "8597085202"]


def test_digisac_13_digitos_com_9():
    # 5585997085202 -> tira 55 -> 85997085202 (11 díg)
    assert phone_candidates("5585997085202") == ["85997085202", "8597085202"]


def test_vazio():
    assert phone_candidates("") == []
