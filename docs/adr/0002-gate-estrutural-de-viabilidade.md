# ADR 0002 — Gate estrutural de viabilidade em código, não em prompt

## Status

Aceito — 2026-11-14

## Contexto

O enunciado exige que o agente nunca deixe a Dona Maria aceitar (e comprar ingredientes para) um prato que ela não consegue produzir — é declarado "o coração do desafio". A elicitação cobre utensílios/equipamentos, técnicas/habilidades e restrições operacionais, e o agente deve perguntar ativamente o que ela não mencionar.

Instruir isso apenas no system prompt não é garantia: modelos esquecem instruções em conversas longas, e uma única falha é exatamente o cenário que o desafio proíbe.

## Decisão

O checklist de viabilidade vive no **estado estruturado** (não no texto da conversa), com cada dimensão marcada como pendente até ser confirmada. A operação de aceite de prato **valida o checklist e recusa** enquanto houver pendência, devolvendo ao agente a lista do que falta perguntar.

O LLM decide *como* conduzir a conversa; o código decide *se* o aceite é válido.

## Consequências

- A elicitação vira comportamento demonstrável e testável, não promessa de prompt — inclusive é o momento central da demo em vídeo.
- O agente precisa tolerar a recusa da tool com graciosidade (voltar e perguntar), o que exige testar esse caminho de conversa.
- Custo: mais uma máquina de estados para manter. Aceitamos porque a alternativa é falhar no requisito principal.
