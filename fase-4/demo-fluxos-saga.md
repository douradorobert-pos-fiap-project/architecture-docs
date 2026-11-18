# Demonstração da Saga pelo terminal

Use Bash, `curl` com suporte a `--fail-with-body`, `jq` e `python3`. Mantenha os port-forwards abaixo ativos em terminais separados. Use os três no mesmo cluster em que os clientes e veículos foram cadastrados.

```bash
kubectl -n oficina port-forward svc/os-service 8001:80
kubectl -n oficina port-forward svc/billing-service 8002:80
kubectl -n oficina port-forward svc/execution-service 8003:80
```

Cada script é independente. Copie o bloco inteiro do caminho desejado, incluindo a primeira e a última linha, e cole no terminal. O bloco abre um Bash separado, então uma falha aparece no terminal e devolve o prompt. Você também pode salvar o bloco inteiro em um arquivo `.sh` e executar com `bash nome-do-arquivo.sh`. Cada execução cria uma OS e um item de catálogo. Os IDs abaixo são os pares já cadastrados para a demonstração. Se precisar trocar o par, defina `CUSTOMER_ID` e `VEHICLE_ID` ao executar.

Os scripts consultam o estado da OS a cada dois segundos enquanto esperam as transições. Ao final, exibem também o histórico persistido pela API. A conclusão do reparo aparece como `COMPLETED` no Execution e como `PAYMENT_PENDING` na OS, pois o orquestrador avança essas duas ações na mesma transação.

## Caminho feliz

Abre a OS, conclui o diagnóstico, cria e aprova o orçamento de R$ 1,00 e conclui o reparo. O Billing gera o QR e o script para com o pagamento pendente. O conteúdo do QR fica em um arquivo local. Se `qrencode` estiver instalado, o script também gera um PNG para escanear com o aplicativo do Mercado Pago em modo de teste. O webhook da compra chega pela URL pública da AWS, que precisa alcançar o Billing para confirmar o pagamento.

```bash
bash <<'CAMINHO_FELIZ'
CUSTOMER_ID=${CUSTOMER_ID:-25f68add-c514-411b-b792-819bb1698918}
VEHICLE_ID=${VEHICLE_ID:-bba7d272-160b-4957-9705-d4df3c350d2e}

set -Eeuo pipefail
trap 'printf "Falha na linha %s (código %s).\n" "$LINENO" "$?" >&2' ERR

OS_URL=${OS_URL:-http://localhost:8001}
BILLING_URL=${BILLING_URL:-http://localhost:8002}
EXECUTION_URL=${EXECUTION_URL:-http://localhost:8003}
WAIT_SECONDS=${WAIT_SECONDS:-120}

for tool in curl jq python3; do
  command -v "$tool" >/dev/null || { echo "Instale $tool para continuar." >&2; exit 1; }
done
if [[ ! $WAIT_SECONDS =~ ^[1-9][0-9]*$ ]]; then
  echo "WAIT_SECONDS deve ser um inteiro positivo." >&2
  exit 1
fi

uuid() { python3 -c 'import uuid; print(uuid.uuid4())'; }
correlation_id=$(uuid)

post() {
  curl --silent --show-error --fail-with-body --max-time 15 -X POST \
    -H "X-Correlation-ID: $correlation_id" \
    -H "X-Event-ID: $(uuid)" \
    -H 'Content-Type: application/json' \
    --data "$2" "$1"
}

get() {
  curl --silent --show-error --fail-with-body --max-time 15 \
    -H "X-Correlation-ID: $correlation_id" "$1"
}

wait_for_status() {
  local label=$1 url=$2 expected=$3
  local deadline=$((SECONDS + WAIT_SECONDS)) raw code observed previous=
  while (( SECONDS < deadline )); do
    raw=$(curl --silent --show-error --max-time 15 -w $'\n%{http_code}' \
      -H "X-Correlation-ID: $correlation_id" "$url") || return 1
    code=${raw##*$'\n'}
    response=${raw%$'\n'*}
    case "$code" in
      200)
        observed=$(jq -er '.status' <<<"$response") || return 1
        if [[ $observed != "$previous" ]]; then
          printf '[%s] %s → %s\n' "$(date +%T)" "$label" "$observed"
          previous=$observed
        fi
        if [[ $observed == "$expected" ]]; then
          return 0
        fi
        if [[ $observed == CANCELLED || $observed == MANUAL_INTERVENTION ||
              $observed == REJECTED || $observed == REFUNDED ]]; then
          printf '%s terminou em %s. Esperado: %s.\n' "$label" "$observed" "$expected" >&2
          return 1
        fi
        ;;
      404) ;; # O recurso pode ainda estar sendo criado pelo worker.
      *) printf 'GET %s respondeu HTTP %s\n' "$url" "$code" >&2; return 1 ;;
    esac
    sleep 2
  done
  printf 'Tempo esgotado esperando %s → %s.\n' "$label" "$expected" >&2
  return 1
}

for service in "$OS_URL" "$BILLING_URL" "$EXECUTION_URL"; do
  if ! get "$service/health" >/dev/null; then
    printf 'API indisponível em %s. Confira o port-forward.\n' "$service" >&2
    exit 1
  fi
done

catalog=$(post "$BILLING_URL/api/v1/catalog-items" \
  "$(jq -cn --arg name "Serviço demo $correlation_id" \
    '{name:$name,item_type:"SERVICE",unit_price:"1.00"}')")
catalog_item_id=$(jq -er '.id' <<<"$catalog")

order=$(post "$OS_URL/api/v1/service-orders" \
  "$(jq -cn --arg customer "$CUSTOMER_ID" --arg vehicle "$VEHICLE_ID" \
    '{customer_id:$customer,vehicle_id:$vehicle}')")
order_id=$(jq -er '.id' <<<"$order")
saga_id=$(jq -er '.saga_id' <<<"$order")
order_url="$OS_URL/api/v1/service-orders/$order_id"
execution_lookup="$EXECUTION_URL/api/v1/executions/by-order/$order_id"
printf '\nOS %s | Saga %s | Correlação %s\n' "$order_id" "$saga_id" "$correlation_id"
printf '[%s] OS → %s\n' "$(date +%T)" "$(jq -er '.status' <<<"$order")"

wait_for_status "Execution" "$execution_lookup" DIAGNOSING
execution_id=$(jq -er '.id' <<<"$response")
execution_url="$EXECUTION_URL/api/v1/executions/$execution_id"
post "$execution_url/diagnosis/complete" \
  "$(jq -cn --arg item "$catalog_item_id" \
    '{diagnosis:"Inspeção de demonstração concluída.",recommended_service_ids:[$item]}')" >/dev/null
wait_for_status "OS" "$order_url" DIAGNOSIS_COMPLETED

quote=$(post "$BILLING_URL/api/v1/quotes" \
  "$(jq -cn --arg order "$order_id" --arg saga "$saga_id" --arg item "$catalog_item_id" \
    '{order_id:$order,saga_id:$saga,items:[{catalog_item_id:$item,quantity:1}]}')")
quote_id=$(jq -er '.id' <<<"$quote")
wait_for_status "OS" "$order_url" AWAITING_APPROVAL
quote_url="$BILLING_URL/api/v1/quotes/$quote_id"

show_history() {
  printf '\nHistórico da OS registrado pelo OS Service\n'
  get "$order_url/history" | jq -r '.[] | "  \(.occurred_at)  \(.status)"'
}

decision=$(post "$quote_url/approval" '{"action":"APPROVE"}')
printf 'Orçamento %s → %s\n' "$quote_id" "$(jq -er '.status' <<<"$decision")"
wait_for_status "OS" "$order_url" EXECUTION_PENDING
wait_for_status "Execution" "$execution_lookup" QUEUED

post "$execution_url/repair/start" '' >/dev/null
wait_for_status "OS" "$order_url" IN_EXECUTION

repair=$(post "$execution_url/repair/complete" \
  '{"notes":"Reparo concluído e validado em teste de rodagem."}')
printf 'Reparo → %s\n' "$(jq -er '.status' <<<"$repair")"
wait_for_status "OS" "$order_url" PAYMENT_PENDING

payment_url="$BILLING_URL/api/v1/payments/by-order/$order_id"
wait_for_status "Pagamento" "$payment_url" PENDING
payment=$response
qr_data=$(jq -er '.qr_data | select(type == "string" and length > 0)' <<<"$payment")
qr_dir=$(mktemp -d)
printf '%s' "$qr_data" >"$qr_dir/qr_data.txt"
printf 'Valor: R$ %s\n' "$(jq -er '.amount' <<<"$payment")"
printf 'Conteúdo do QR: %s\n' "$qr_dir/qr_data.txt"
if command -v qrencode >/dev/null; then
  qrencode -s 8 -o "$qr_dir/pagamento.png" <"$qr_dir/qr_data.txt"
  printf 'Imagem do QR: %s\n' "$qr_dir/pagamento.png"
fi

show_history
printf '\nPagamento de teste aguardando ação manual no aplicativo do Mercado Pago.\n'
CAMINHO_FELIZ
```

## Caminho triste

Abre outra OS, conclui o diagnóstico e recusa o orçamento. O Billing publica `QuoteRejectedV1`, e o OS Service aplica a compensação. O script espera a OS chegar a `CANCELLED` e imprime o histórico para mostrar a mudança.

```bash
bash <<'CAMINHO_TRISTE'
CUSTOMER_ID=${CUSTOMER_ID:-c6c144f8-a4bb-4776-bb5e-798fe54ae184}
VEHICLE_ID=${VEHICLE_ID:-fe5811a5-e95a-420e-b817-1910dd9db714}

set -Eeuo pipefail
trap 'printf "Falha na linha %s (código %s).\n" "$LINENO" "$?" >&2' ERR

OS_URL=${OS_URL:-http://localhost:8001}
BILLING_URL=${BILLING_URL:-http://localhost:8002}
EXECUTION_URL=${EXECUTION_URL:-http://localhost:8003}
WAIT_SECONDS=${WAIT_SECONDS:-120}

for tool in curl jq python3; do
  command -v "$tool" >/dev/null || { echo "Instale $tool para continuar." >&2; exit 1; }
done
if [[ ! $WAIT_SECONDS =~ ^[1-9][0-9]*$ ]]; then
  echo "WAIT_SECONDS deve ser um inteiro positivo." >&2
  exit 1
fi

uuid() { python3 -c 'import uuid; print(uuid.uuid4())'; }
correlation_id=$(uuid)

post() {
  curl --silent --show-error --fail-with-body --max-time 15 -X POST \
    -H "X-Correlation-ID: $correlation_id" \
    -H "X-Event-ID: $(uuid)" \
    -H 'Content-Type: application/json' \
    --data "$2" "$1"
}

get() {
  curl --silent --show-error --fail-with-body --max-time 15 \
    -H "X-Correlation-ID: $correlation_id" "$1"
}

wait_for_status() {
  local label=$1 url=$2 expected=$3
  local deadline=$((SECONDS + WAIT_SECONDS)) raw code observed previous=
  while (( SECONDS < deadline )); do
    raw=$(curl --silent --show-error --max-time 15 -w $'\n%{http_code}' \
      -H "X-Correlation-ID: $correlation_id" "$url") || return 1
    code=${raw##*$'\n'}
    response=${raw%$'\n'*}
    case "$code" in
      200)
        observed=$(jq -er '.status' <<<"$response") || return 1
        if [[ $observed != "$previous" ]]; then
          printf '[%s] %s → %s\n' "$(date +%T)" "$label" "$observed"
          previous=$observed
        fi
        if [[ $observed == "$expected" ]]; then
          return 0
        fi
        if [[ $observed == CANCELLED || $observed == MANUAL_INTERVENTION ||
              $observed == REJECTED || $observed == REFUNDED ]]; then
          printf '%s terminou em %s. Esperado: %s.\n' "$label" "$observed" "$expected" >&2
          return 1
        fi
        ;;
      404) ;; # O recurso pode ainda estar sendo criado pelo worker.
      *) printf 'GET %s respondeu HTTP %s\n' "$url" "$code" >&2; return 1 ;;
    esac
    sleep 2
  done
  printf 'Tempo esgotado esperando %s → %s.\n' "$label" "$expected" >&2
  return 1
}

for service in "$OS_URL" "$BILLING_URL" "$EXECUTION_URL"; do
  if ! get "$service/health" >/dev/null; then
    printf 'API indisponível em %s. Confira o port-forward.\n' "$service" >&2
    exit 1
  fi
done

catalog=$(post "$BILLING_URL/api/v1/catalog-items" \
  "$(jq -cn --arg name "Serviço demo $correlation_id" \
    '{name:$name,item_type:"SERVICE",unit_price:"1.00"}')")
catalog_item_id=$(jq -er '.id' <<<"$catalog")

order=$(post "$OS_URL/api/v1/service-orders" \
  "$(jq -cn --arg customer "$CUSTOMER_ID" --arg vehicle "$VEHICLE_ID" \
    '{customer_id:$customer,vehicle_id:$vehicle}')")
order_id=$(jq -er '.id' <<<"$order")
saga_id=$(jq -er '.saga_id' <<<"$order")
order_url="$OS_URL/api/v1/service-orders/$order_id"
execution_lookup="$EXECUTION_URL/api/v1/executions/by-order/$order_id"
printf '\nOS %s | Saga %s | Correlação %s\n' "$order_id" "$saga_id" "$correlation_id"
printf '[%s] OS → %s\n' "$(date +%T)" "$(jq -er '.status' <<<"$order")"

wait_for_status "Execution" "$execution_lookup" DIAGNOSING
execution_id=$(jq -er '.id' <<<"$response")
execution_url="$EXECUTION_URL/api/v1/executions/$execution_id"
post "$execution_url/diagnosis/complete" \
  "$(jq -cn --arg item "$catalog_item_id" \
    '{diagnosis:"Inspeção de demonstração concluída.",recommended_service_ids:[$item]}')" >/dev/null
wait_for_status "OS" "$order_url" DIAGNOSIS_COMPLETED

quote=$(post "$BILLING_URL/api/v1/quotes" \
  "$(jq -cn --arg order "$order_id" --arg saga "$saga_id" --arg item "$catalog_item_id" \
    '{order_id:$order,saga_id:$saga,items:[{catalog_item_id:$item,quantity:1}]}')")
quote_id=$(jq -er '.id' <<<"$quote")
wait_for_status "OS" "$order_url" AWAITING_APPROVAL
quote_url="$BILLING_URL/api/v1/quotes/$quote_id"

show_history() {
  printf '\nHistórico da OS registrado pelo OS Service\n'
  get "$order_url/history" | jq -r '.[] | "  \(.occurred_at)  \(.status)"'
}

decision=$(post "$quote_url/approval" '{"action":"REJECT"}')
printf 'Orçamento %s → %s\n' "$quote_id" "$(jq -er '.status' <<<"$decision")"
wait_for_status "OS" "$order_url" CANCELLED

show_history
printf '\nO OS Service cancelou a ordem após receber QuoteRejectedV1.\n'
CAMINHO_TRISTE
```
