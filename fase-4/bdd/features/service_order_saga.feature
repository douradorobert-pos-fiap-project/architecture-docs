# language: pt
Funcionalidade: Saga distribuída da ordem de serviço
  Como operador da oficina
  Quero coordenar diagnóstico, orçamento, execução e pagamento
  Para entregar a ordem uma única vez ou compensá-la com segurança

  Cenário: concluir o fluxo feliz da ordem de serviço
    Dado uma ordem de serviço aberta com rastreabilidade
    Quando o diagnóstico, orçamento aprovado, reparo e pagamento forem concluídos
    Então a ordem deve ser entregue uma única vez
    E todos os participantes devem preservar o mesmo identificador de correlação

  Cenário: compensar uma falha antes do início do reparo
    Dado uma ordem de serviço aberta com rastreabilidade
    Quando a execução falhar antes do início do reparo
    Então a saga deve cancelar a ordem sem exigir intervenção manual

  Cenário: ignorar confirmação de pagamento duplicada
    Dado uma ordem de serviço pronta para receber o pagamento
    Quando a mesma confirmação de pagamento for recebida duas vezes
    Então a ordem deve ser entregue uma única vez
    E o provedor de pagamento deve registrar uma única confirmação
