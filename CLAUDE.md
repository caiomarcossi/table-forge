# Table Forge – AGENTS.md

## PAPEL DO AGENTE

Você é um agente de engenharia de software responsável por modificar o código do Table Forge.

Você trabalha exclusivamente sobre:

* código existente no repositório
* AGENTS.md
* instruções fornecidas pelo usuário

Você NÃO:

* executa o sistema
* executa testes
* afirma que testou
* afirma que executou
* afirma que validou runtime
* afirma que algo funciona sem evidência objetiva no código
* inventa APIs
* inventa modelos
* inventa atributos
* inventa eventos
* inventa endpoints
* inventa consumidores Channels
* inventa traduções
* inventa comportamento não presente no código
* substitui arquitetura existente sem solicitação explícita

Seu objetivo é:

* preservar a arquitetura
* preservar acessibilidade
* preservar internacionalização
* produzir alterações seguras
* produzir diffs pequenos
* manter consistência estrutural
* evitar regressões arquiteturais

---

# CONTEXTO DO PROJETO

Table Forge é uma plataforma para gerenciamento de mesas de RPG de mesa.

O projeto possui foco prioritário em acessibilidade para pessoas cegas.

Todo recurso desenvolvido deve considerar simultaneamente:

* jogadores cegos
* jogadores com baixa visão
* jogadores videntes
* mestres

A acessibilidade não é opcional.

A acessibilidade é requisito arquitetural.

---

# STACK OFICIAL

Tecnologias aprovadas:

* Python
* Django
* Django Channels
* HTML
* CSS
* JavaScript
* WebSocket

O backend é a fonte oficial de verdade da aplicação.

Novas dependências somente devem ser introduzidas quando existir justificativa técnica clara.

Antes de adicionar bibliotecas externas:

* verificar se a solução já existe no projeto
* verificar se a stack atual resolve o problema
* verificar impacto arquitetural

---

# IDIOMA DO PROJETO

Toda comunicação do agente deve ser realizada em português.

Devem permanecer em inglês:

* nomes de classes
* nomes de funções
* nomes de métodos
* nomes de atributos
* nomes de variáveis
* nomes de módulos
* nomes de constantes
* nomes de eventos
* nomes de payloads
* nomes de APIs
* nomes de tecnologias

Documentação do projeto deve ser escrita em português.

Comentários de código devem ser evitados.

Quando forem realmente necessários:

* utilizar inglês

---

# VISÃO ARQUITETURAL

## Backend Driven UI

O projeto adota Backend Driven UI como princípio arquitetural central.

O backend controla:

* estrutura de páginas
* menus
* ações disponíveis
* estados
* permissões
* fluxo da aplicação
* internacionalização
* navegação lógica

O frontend atua apenas como camada de renderização.

O agente NÃO deve:

* mover regras de negócio para JavaScript
* transformar o frontend em fonte de verdade
* duplicar regras entre frontend e backend
* criar estados paralelos no cliente

Toda regra relevante deve permanecer no backend.

---

## Internacionalização

A internacionalização é obrigatória.

Todo novo recurso deve nascer preparado para múltiplos idiomas.

Evitar:

* textos espalhados sem organização
* duplicação desnecessária
* lógica dependente de idioma

Sempre considerar expansão futura para novos idiomas.

---

## Tempo Real

Comunicação em tempo real deve utilizar Django Channels.

Não criar mecanismos paralelos de polling quando Channels for apropriado.

Eventos devem ser:

* simples
* previsíveis
* serializáveis
* acessíveis

Payloads devem conter apenas as informações necessárias.

---

## Cliente Desktop Futuro

O projeto possuirá cliente nativo em wxPython.

Toda implementação deve buscar:

* desacoplamento de domínio
* desacoplamento de apresentação
* reutilização de lógica
* reutilização de serviços

Evitar implementar regras que dependam exclusivamente do navegador.

---

# ACESSIBILIDADE

## Regra Fundamental

Nenhuma funcionalidade pode reduzir acessibilidade existente.

Toda alteração deve ser analisada sob perspectiva de:

* leitores de tela
* navegação por teclado
* semântica HTML
* feedback textual
* ordem lógica de leitura

---

## HTML

Priorizar:

* header
* nav
* main
* section
* article
* aside
* footer
* form
* button
* label

Preferir elementos semânticos nativos.

Evitar uso de div para simular componentes nativos.

---

## Formulários

Todo campo deve possuir associação adequada entre:

* label
* input

Mensagens de erro devem ser acessíveis.

Estados devem ser anunciáveis por leitores de tela.

---

## ARIA

Utilizar ARIA apenas quando HTML semântico não resolver.

Não adicionar atributos ARIA desnecessários.

Preferir semântica nativa.

---

## Navegação

Toda funcionalidade deve ser operável exclusivamente por teclado.

Não assumir uso de mouse.

Não assumir uso de gestos.

Não assumir percepção visual.

---

## Feedback

Mudanças de estado devem possuir feedback textual.

Informações importantes não podem depender exclusivamente de:

* cor
* posição visual
* animação
* ícones

---

# ORGANIZAÇÃO DO PROJETO

Preservar estrutura existente.

Não:

* mover módulos sem necessidade
* criar arquiteturas paralelas
* duplicar responsabilidades
* reorganizar apps sem solicitação

Preferir extensão incremental da arquitetura atual.

---

# PRIORIDADE DE REFERÊNCIA

Ao modificar código existente:

1. código existente
2. AGENTS.md
3. instruções do usuário
4. internet

Ao criar código novo:

1. instruções do usuário
2. arquitetura existente
3. AGENTS.md
4. internet

Quando existir conflito entre documentação e implementação:

* considerar o código existente como referência principal

---

# MODELOS DE DOMÍNIO

Preservar responsabilidades existentes.

Não:

* duplicar lógica
* espalhar regras de negócio
* mover regras arbitrariamente

Novas funcionalidades devem integrar-se ao domínio existente.

---

# DJANGO

Priorizar recursos nativos do Django antes de bibliotecas externas.

Preferir:

* ORM
* Forms
* ModelForms quando apropriado
* Validators
* Middleware
* Signals apenas quando justificadas

Evitar soluções excessivamente complexas.

---

# DJANGO CHANNELS

Não assumir existência de:

* grupos
* consumers
* eventos
* payloads

Tudo deve ser confirmado pelo código existente.

Ao adicionar eventos:

* utilizar nomenclatura consistente
* manter payloads mínimos
* evitar duplicações

---

# SEGURANÇA

Não remover:

* autenticação
* autorização
* validações
* verificações de permissão
* proteções CSRF
* proteções existentes

Sem evidência explícita de obsolescência.

Toda alteração deve preservar o nível atual de segurança.

---

# PERFORMANCE

Priorizar simplicidade.

Evitar:

* consultas redundantes
* loops desnecessários
* serializações excessivas
* abstrações prematuras

Otimizações devem possuir justificativa objetiva.

---

# REGRA DE DIFF MÍNIMO

Modificar apenas o necessário.

Evitar:

* refactors amplos
* reorganizações cosméticas
* renomeações sem necessidade
* alterações de estilo irrelevantes

Toda modificação deve possuir justificativa funcional.

---

# PADRÃO DE CÓDIGO

## Indentação

Utilizar exclusivamente TAB.

Nunca converter TAB para espaços.

Nunca misturar TAB e espaços.

Nunca utilizar indentações em html ou javaScript, pois é apenas cosmético.

---

## Identificadores

Todos os identificadores devem utilizar inglês.

Exemplos:

* UserProfile
* Table
* Character
* create_character
* update_table_state

---

## Estilo

Preferir código compacto, legível e consistente.

Evitar abstrações sem necessidade real.

Evitar criação de helpers sem reutilização clara.

Evitar wrappers desnecessários.

---

## Fechamentos

Evitar fechamentos isolados quando isso prejudicar legibilidade.

Manter consistência com o padrão já utilizado no projeto.

---

# BACKEND DRIVEN UI

## Regra Fundamental

O backend define comportamento.

O frontend renderiza comportamento.

Sempre que possível:

* estados devem vir do backend
* ações devem vir do backend
* permissões devem vir do backend
* estrutura lógica deve vir do backend

Evitar decisões importantes exclusivamente no cliente.

---

# INTERNACIONALIZAÇÃO DE INTERFACE

Novos elementos visíveis ao usuário devem ser planejados considerando tradução futura.

Evitar:

* concatenação de frases
* textos duplicados
* lógica dependente de idioma

Mensagens devem ser previsíveis e organizadas.

---

# COMPATIBILIDADE

Preservar compatibilidade existente.

Não remover:

* validações defensivas
* fallbacks
* proteções
* verificações de segurança

Sem evidência clara de obsolescência.

Priorizar estabilidade em:

* autenticação
* sessão
* permissões
* WebSockets
* persistência
* navegação

---

# CÓDIGO MORTO

Não adicionar código morto.

Não adicionar estruturas preparatórias sem uso imediato.

Toda implementação deve possuir finalidade concreta.

---

# CHECAGEM ESTÁTICA OBRIGATÓRIA

Antes de finalizar qualquer alteração:

* revisar imports
* revisar referências
* revisar nomes
* revisar consistência arquitetural
* revisar acessibilidade
* revisar internacionalização
* revisar segurança
* revisar permissões
* revisar compatibilidade
* revisar código morto evidente
* revisar indentação
* revisar uso exclusivo de TAB

---

# SAÍDA DO AGENTE

A resposta final deve conter:

* arquivos alterados
* resumo objetivo das alterações
* riscos identificados
* premissas utilizadas

Não afirmar:

* que executou
* que testou
* que validou runtime
* que verificou funcionamento em produção
* que confirmou comportamento sem evidência no código

---

# PROIBIÇÕES

Não executar:

* git add
* git commit
* git push
* migrações sem solicitação explícita
* reorganizações estruturais amplas sem solicitação explícita

Não inventar:

* modelos
* APIs
* endpoints
* consumers
* eventos
* traduções
* dependências

---

# ORDEM DE PRIORIDADE

1. acessibilidade
2. preservação da arquitetura
3. Backend Driven UI
4. internacionalização
5. segurança
6. consistência de domínio
7. não inventar APIs
8. não inventar modelos
9. diff mínimo
10. estabilidade
11. compatibilidade retroativa
12. reutilização de padrões existentes
13. simplicidade
14. legibilidade
15. performance
