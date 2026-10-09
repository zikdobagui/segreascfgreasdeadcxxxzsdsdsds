# 🎯 Sistema de Afiliados - Documentação

## 📋 Visão Geral

O novo sistema de afiliados permite que os usuários ganhem saldo no bot através de indicações. Cada vez que um novo usuário entra no bot usando o link de indicação de outro usuário, o indicador recebe um valor em saldo configurável pelo administrador.

## 🚀 Funcionalidades Implementadas

### Para Usuários:
- **Link de Indicação Único**: Cada usuário possui um link personalizado
- **Ganho Automático**: Recebe saldo automaticamente quando alguém usa seu link
- **Histórico de Indicações**: Visualiza todas as suas indicações e ganhos
- **Ranking**: Compete com outros usuários no ranking de indicadores

### Para Administradores:
- **Ativar/Desativar Sistema**: Controle total sobre o sistema
- **Configurar Valor**: Define quanto cada indicação vale
- **Estatísticas**: Visualiza dados completos do sistema
- **Painel Integrado**: Gerencia tudo pelo painel admin existente

## 📱 Comandos Disponíveis

### Comandos do Usuário:
- `/meulink` - Obtém o link de indicação pessoal
- `/minhasindicacoes` - Visualiza histórico de indicações
- `/rankingindicadores` - Vê o ranking dos top indicadores
- `/afiliados` - Redireciona para /meulink (compatibilidade)

### Comandos Admin:
- Acesse via `/admin` → "👥 Configurar Afiliados"

## ⚙️ Configurações

### Arquivo de Configuração (`settings/credenciais.json`):
```json
{
  "user_bot": "rlfornecedor_bot",
  "afiliados_sistema": {
    "ativo": true,
    "valor_por_indicacao": 5.0
  }
}
```

### Parâmetros:
- **ativo**: `true/false` - Ativa ou desativa o sistema
- **valor_por_indicacao**: Valor em R$ que cada indicação vale
- **user_bot**: Nome do bot (usado automaticamente para gerar links)

## 🔄 Como Funciona

1. **Usuário solicita link**: Usa `/meulink` para obter seu link único
2. **Compartilha o link**: Envia para amigos/grupos/redes sociais
3. **Novo usuário entra**: Clica no link e inicia o bot com `/start`
4. **Sistema processa**: Detecta a referência e registra a indicação
5. **Indicador recebe saldo**: Valor é adicionado automaticamente
6. **Notificações**: Ambos recebem notificação da indicação

## 📊 Estrutura do Banco de Dados

### Novos Campos no Usuário:
```json
{
  "indicado_por": null,
  "indicacoes": [],
  "total_ganho_indicacoes": 0.0
}
```

### Estrutura de uma Indicação:
```json
{
  "user_id": 123456789,
  "data": "09/10/2025 22:24:31",
  "valor_ganho": 5.0
}
```

## 🛠️ Arquivos Modificados/Criados

### Arquivos Criados:
- `afiliados_sistema.py` - Lógica principal do sistema
- `SISTEMA_AFILIADOS.md` - Esta documentação

### Arquivos Modificados:
- `bot.py` - Integração dos comandos e callbacks
- `database.py` - Funções de banco de dados para afiliados
- `central.py` - Classe SistemaAfiliados para configurações
- `settings/credenciais.json` - Configurações do sistema

## 🎮 Exemplo de Uso

### Usuário Normal:
1. Digite `/meulink`
2. Copie o link recebido
3. Compartilhe com amigos
4. Ganhe R$ 5,00 (ou valor configurado) para cada novo usuário

### Administrador:
1. Digite `/admin`
2. Clique em "👥 Configurar Afiliados"
3. Use os botões para:
   - Ativar/Desativar sistema
   - Alterar valor por indicação
   - Ver estatísticas

## 🔧 Manutenção

### Para alterar o valor por indicação:
1. Acesse o painel admin
2. Clique em "💰 Alterar Valor"
3. Digite o novo valor (ex: 10.50)

### Para ver estatísticas:
- Top indicadores são calculados automaticamente
- Dados são atualizados em tempo real
- Histórico completo mantido no banco

## 🚨 Observações Importantes

1. **Apenas novos usuários**: Sistema só funciona para usuários que nunca usaram o bot
2. **Uma indicação por usuário**: Cada usuário só pode ser indicado uma vez
3. **Auto-indicação bloqueada**: Usuário não pode usar seu próprio link
4. **Sistema ativo**: Precisa estar ativo nas configurações para funcionar

## 📈 Benefícios

- **Crescimento orgânico**: Usuários trazem novos usuários
- **Engajamento**: Incentiva compartilhamento
- **Retenção**: Usuários ganham saldo e ficam mais ativos
- **Controle total**: Admin pode ajustar valores e ativar/desativar

## 🎯 Próximos Passos

O sistema está completo e pronto para uso. Para ativar:

1. Certifique-se que `"ativo": true` em `credenciais.json`
2. Configure o valor desejado por indicação
3. Teste com usuários de confiança
4. Monitore via painel admin

---

**Sistema implementado com sucesso! 🎉**
