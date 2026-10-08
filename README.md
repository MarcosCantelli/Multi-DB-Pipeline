# Multi-DB-Pipeline

Esteira de CI/CD para gestão de mudanças em bancos de dados (*Database DevOps*), com suporte a múltiplas engines.

> 🚧 **Projeto em construção** — repositório de portfólio, desenvolvido de forma incremental.

## Objetivo

Inspirado em ferramentas corporativas de *Database Release Automation* como o DBMaestro, este projeto aplica ao banco de dados as mesmas práticas que já usamos no código da aplicação:

- **Versionamento** — todo script SQL vive no Git; nada é executado "na mão" direto no banco.
- **Segurança** — ninguém precisa de acesso direto ao banco para publicar uma mudança; credenciais ficam apenas no cofre de segredos da esteira.
- **Rastreabilidade** — cada mudança aplicada fica registrada no próprio banco (quem aplicou, quando e qual versão do arquivo).
- **Validação antes do deploy** — análise estática do SQL e de segurança antes de qualquer alteração chegar ao banco.

## Engines suportadas

Cada engine tem particularidades de conexão, sintaxe e ferramenta de linha de comando, por isso cada uma possui seu próprio adaptador na esteira.

| Engine | Hospedagem | Por que está no projeto |
|---|---|---|
| SQL Server | On-premises (VM no hypervisor OLVM) | Padrão em ambientes corporativos |
| PostgreSQL | On-premises (app em container no TrueNAS) | Banco que uso nos meus projetos pessoais |
| MySQL | On-premises (container Podman/Docker local) | Muito presente no mercado, especialmente em aplicações web |
| Supabase | Cloud (free tier) | Comum em produtos pequenos e SaaS |
| Databricks | Cloud (free tier) | Cada vez mais adotado para dados e analytics |

> **Por que Supabase separado do PostgreSQL?** Por baixo é Postgres, mas a forma de conexão é diferente: host gerenciado, SSL obrigatório, usuário no formato `postgres.<project-ref>` e uso do *Session Pooler* (a conexão direta é apenas IPv6). Tratar como engine própria deixa essas diferenças explícitas.

## Topologia de rede

A esteira é **híbrida**: parte dos bancos está na rede local e parte na nuvem.

| Banco | Runner que executa o deploy |
|---|---|
| SQL Server, PostgreSQL, MySQL | **Self-hosted runner** na rede local |
| Supabase, Databricks | Runner hospedado pelo GitHub (`ubuntu-latest`) |

Os runners hospedados pelo GitHub rodam na nuvem e não alcançam IPs da rede local. O self-hosted runner resolve isso: ele abre uma conexão **de saída** para o GitHub e busca os jobs, sem exigir nenhuma porta aberta no roteador.

## Branches

| Branch | Função |
|---|---|
| `main` | Única branch que **executa** a esteira de deploy |
| `mssqlserver`, `postgree`, `mysql`, `supabase`, `databricks` | Branches de desenvolvimento de cada engine — nada é executado nelas; entram na `main` via Pull Request |

O ambiente de destino **não** é definido por branch: o mesmo commit da `main` é promovido entre os ambientes (*build once, promote many*).

## Ambientes

O projeto foi desenhado para três ambientes, cada um com regras próprias:

| Ambiente | Aprovação | Backup antes do deploy |
|---|---|---|
| **DEV** — Desenvolvimento | Automático | Não |
| **HO** — Homologação | Manual | Sim |
| **PRD** — Produção | Manual | Sim |

> ⚠️ **Neste repositório de portfólio existe apenas um banco real por engine.** A estrutura (GitHub Environments, credenciais e configurações por ambiente) está pronta para DEV, HO e PRD; para usar em um cenário real, basta cadastrar as credenciais e as configurações de cada ambiente.

## Esteiras

- **GitHub Actions** — esteira principal: validação do código SQL e deploy nos bancos.
- **Jenkins** — esteira alternativa, com as mesmas regras de aprovação por ambiente e análise de segurança:
  - **Trivy** — vulnerabilidades e segredos expostos no repositório e nas imagens;
  - **SonarQube** — qualidade e análise estática do código;
  - **OWASP ZAP** — teste dinâmico de segurança.

## Roadmap

- [ ] Runner de migrations próprio (controle de versão e checksum)
- [ ] Adaptadores: SQL Server, PostgreSQL, MySQL, Supabase, Databricks
- [ ] Workflows do GitHub Actions (lint + deploy por ambiente)
- [ ] Jenkinsfile com Trivy, SonarQube e OWASP ZAP

## Escopo e adaptação

As engines deste projeto foram escolhidas com base nas ferramentas com que já trabalhei ou trabalho, e cada uma é validada em um ambiente real. Não é possível validar todos os bancos de dados existentes, por isso outras engines (Oracle, MariaDB, Snowflake etc.) **não estão cobertas**.

> 💡 **Usa outro banco?** Fique à vontade para usar este repositório como base: a estrutura de núcleo comum + adaptador por engine foi pensada justamente para que um novo banco seja adicionado criando apenas um novo adaptador.
