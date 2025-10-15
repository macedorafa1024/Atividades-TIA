# FIAP - Faculdade de Informática e Administração Paulista


## Rastreabilidade Sustentável no Agronegócio

### Nome do Grupo:
Rafael Gomes de Macedo

---

Integrantes:
Rafael Gomes de Macedo

---

**Tutor(a):**
Sabrina Otoni

**Coordenador(a):**
André Godoi

---

## Descrição

O projeto **Rastreabilidade Sustentável** tem como objetivo promover uma agricultura mais eficiente, segura e ambientalmente responsável, utilizando a tecnologia como aliada.  
A solução proposta permite **registrar, rastrear e analisar lotes de produção agrícola**, integrando **Python**, **Banco de Dados Oracle** e **boas práticas de sustentabilidade**.  

Cada lote é monitorado por meio de eventos (colheita, transporte, armazenagem e inspeção), com foco em critérios de **uso de água de reuso** e **carbono neutro**, elementos fundamentais na certificação de uma produção sustentável.  

O sistema foi desenvolvido como parte da **Fase 2 – Python e Banco de Dados**, aplicando os conceitos de:
- Funções e subalgoritmos;  
- Estruturas de dados (listas, dicionários e tuplas);  
- Manipulação de arquivos JSON;  
- Conexão e persistência em banco de dados Oracle;  
- Tratamento de erros e validação de dados;  
- Criação automática de tabelas e índices via Python.

O resultado é uma aplicação modular e escalável, que permite a pequenos e médios produtores **registrarem suas produções com transparência e rastreabilidade**, abrindo caminho para práticas agrícolas mais sustentáveis e inteligentes.

---

## Estrutura de pastas

Dentre os arquivos e pastas presentes na raiz do projeto, definem-se:

rastreabilidade_sustentavel/
- data/ # Base local de dados (JSON)
  - dados.json
- logs/ # Arquivos de log de execução
  - app.log
- src/ # Código-fonte principal
  - main.py
  - dominio.py
  - casos_uso.py
  - persistencia_json.py
  - persistencia_oracle.py
  - relatorios.py
  - utils.py

---

## Como executar o código

### Pré-requisitos

- **Python 3.10+**  
- **Bibliotecas:**  
  ```bash
  pip install oracledb pandas python-dotenv

Banco Oracle (acesso FIAP ou local):
Configure o arquivo .env na raiz do projeto com suas credenciais:
- ORACLE_HOST=HOST
- ORACLE_PORT=PORT
- ORACLE_SERVICE=ORCL
- ORACLE_USER=SEU_USUARIO
- ORACLE_PASSWORD=SUA_SENHA
- ORACLE_AUTO_INIT=1

---

## Execução do sistema

Abra o terminal na pasta raiz do projeto:

_cd rastreabilidade_sustentavel_

Execute o módulo principal:

_python -m src.main_


O menu principal será exibido:

_[Rastreabilidade Sustentável]_
- _1) Cadastrar lote_
- _2) Registrar evento_
- _3) Listar lotes_
- _4) Relatório de sustentabilidade_
- _5) Exportar CSV / Importar JSON_
- _6) Inicializar tabelas no Oracle_
- _0) Sair_


Caso o Oracle esteja conectado, o sistema criará automaticamente as tabelas:

LOTE: informações de cada produção;

EVENTO: histórico de etapas do lote;

Índices de otimização e relacionamento.

### Exemplo de uso

Cadastro de lote:

- _Produto: Soja_
- _Produtor: AgroVale_
- _UF (ex: SP): MT_
- _Data da colheita (DD/MM/YYYY): 15/04/2025_
- _Peso (kg): 2800_
- _Usa reuso de água? [s/n]: s_
- _É carbono neutro? [s/n]: s_
- _✅ Lote cadastrado com sucesso._


Consulta de relatório:

- _ RELATÓRIO DE SUSTENTABILIDADE _
- _Total de lotes: 8_
- _% água de reuso: 62.5%_
- _% carbono neutro: 50.0%_
- _Peso total (kg): 14700.0_
- _Lotes sem evento > 7 dias: 2_
- _Distribuição por UF:_
  - _SP: 3_
  - _MT: 5_

---

### Histórico de lançamentos

0.1.0 | 15/10/2025 | Aplicação completa
