# Contrato de linha de comando

Ambos os comandos ficam em `apps/alertas/management/commands/` e rodam com
`python manage.py <comando>` (no Docker: `docker compose exec app python manage.py <comando>` —
serviço `app` da 001).

---

## `varrer_estoque` — varredura de reposição no terminal (FR-027 a FR-031)

### Sinopse

```text
python manage.py varrer_estoque [--formato {texto,csv,json}] [--todos] [--falhar-se-alerta] [--no-color]
```

| Opção | Padrão | Efeito |
|-------|--------|--------|
| `--formato` | `texto` | `texto` (humano), `csv` (mesmo layout do CSV web, sem BOM), `json` |
| `--todos` | desligado | inclui produtos OK depois dos em alerta (mesma chave de ordenação) |
| `--falhar-se-alerta` | desligado | código de saída 1 se `total_em_alerta > 0` |
| `--no-color` | (Django) | desliga o estilo de alerta no formato texto |

Somente leitura (FR-031): nenhuma escrita no banco, nenhum arquivo criado.

### Códigos de saída

| Código | Quando | stdout | stderr |
|-------:|--------|--------|--------|
| 0 | sucesso (com ou sem alertas, sem `--falhar-se-alerta`); ou sem alertas; ou nenhum produto cadastrado | relatório | — |
| 1 | `--falhar-se-alerta` e há ≥ 1 produto em alerta | relatório completo (impresso **antes**) | `Há 4 produto(s) em alerta de reposição.` |
| 2 | opção/valor inválido (argparse) ou erro de banco | — | mensagem de uso / `Não foi possível consultar o estoque: …` |

Implementação: código 1 via `CommandError(msg, returncode=1)`; erro de banco via
`CommandError(msg, returncode=2)`; argumento inválido pelo `CommandParser` (sai com 2).

### Formato `texto` (exemplo com os dados de demonstração)

```text
CONSUS — VARREDURA DE ESTOQUE
Executada em 20/10/2026 14:32
Produtos analisados: 12
Em alerta: 4 (1 sem estoque)

⚠ REPOSIÇÃO NECESSÁRIA · SEM ESTOQUE  #0005  Cola branca 90 g                  atual 0 / mín. 15     déficit 15   repor 30
⚠ REPOSIÇÃO NECESSÁRIA                #0003  Parafuso sextavado M6 x 20        atual 60 / mín. 100   déficit 40   repor 140
⚠ REPOSIÇÃO NECESSÁRIA                #0007  Luva de nitrilo (caixa c/ 100)    atual 3 / mín. 10     déficit 7    repor 17
⚠ REPOSIÇÃO NECESSÁRIA                #0004  Fita adesiva transparente 48 mm   atual 24 / mín. 24    déficit 0    repor 24
```

- Linhas em alerta com `self.style.WARNING` (sem cor se `--no-color` ou saída não-TTY).
- Com `--todos`, os OK aparecem depois como `OK                                    #0006  Grampeador …  atual 6 / mín. 5`.
- Sem alertas: `Nenhum produto precisa de reposição.`; sem produtos: `Nenhum produto cadastrado.`
- Números com separador de milhar "." (saída para humanos).
- Nomes com mais de 40 caracteres são encurtados para 39 + "…" (somente no formato texto; csv e
  json trazem o nome completo).
- Se a codificação do stdout não representar "⚠" (ex.: cp1252), o marcador vira `(!)`.

### Formato `csv`

Idêntico a `exportacao.para_csv(resultado, bom=False)`: cabeçalho
`ID;Produto;Quantidade atual;Estoque mínimo;Déficit;Cobertura (%);Sugestão de reposição;Situação`
e uma linha por item; números sem separador de milhar.

### Formato `json`

```json
{
  "executada_em": "2026-10-20T14:32:05-03:00",
  "total_analisado": 12,
  "total_em_alerta": 4,
  "total_sem_estoque": 1,
  "itens": [
    {
      "id": 5,
      "codigo": "#0005",
      "nome": "Cola branca 90 g",
      "quantidade_atual": 0,
      "estoque_minimo": 15,
      "deficit": 15,
      "cobertura_percentual": 0,
      "sugestao_reposicao": 30,
      "situacao": "SEM_ESTOQUE",
      "situacao_rotulo": "SEM ESTOQUE"
    }
  ]
}
```

`cobertura_percentual` e `sugestao_reposicao` podem ser `null` (não se aplica / produto OK com
`--todos`). `executada_em` em ISO 8601 com deslocamento do fuso do sistema.

---

## `popular_demo` — dados de demonstração (FR-034, FR-035)

### Sinopse

```text
python manage.py popular_demo
```

Sem opções. Cria os 12 produtos de [data-model.md](../data-model.md#6-dados-de-demonstração) que
ainda não existirem (comparação de nome sem diferenciar maiúsculas/minúsculas) e, para cada
produto criado, registra o roteiro de movimentações pelos serviços oficiais, numa transação por
produto. Produtos já existentes não são alterados; nada é apagado.

### Saída e códigos

| Situação | stdout | Código |
|----------|--------|-------:|
| Base vazia | `Dados de demonstração: 12 produto(s) criado(s), 0 já existia(m).` + `Movimentações registradas: 16.` | 0 |
| Segunda execução | `Dados de demonstração: 0 produto(s) criado(s), 12 já existia(m).` + `Movimentações registradas: 0.` | 0 |
| Falha em um produto (ex.: erro de banco) | produtos anteriores mantidos; o produto com falha é revertido inteiro | 2 (`CommandError`) |
