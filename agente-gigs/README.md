# Destino Bounty Agent

Agente local para descubrir y ordenar oportunidades públicas de recompensas.

También puede completar automáticamente tipos de trabajo expresamente admitidos,
si el propietario aprobó el trabajo y registró evidencia de escrow verificado.
Incluye además un servicio protegido que usa Claude para preparar propuestas
veraces sin enviarlas automáticamente.

## Qué hace

- Consulta una lista configurable de plataformas públicas.
- Detecta enlaces relacionados con recompensas y desafíos.
- Genera `opportunities.json` con puntuación y estado de revisión.
- Clasifica por pago, dificultad, KYC, moneda y red.
- Considera cualquier criptomoneda con una ruta de cobro compatible configurada.
- Mantiene bloqueadas las reclamaciones, entregas y operaciones financieras hasta aprobación humana.
- Ejecuta trabajos JSON→CSV dentro de un espacio de trabajo aislado.
- Produce un manifiesto de evidencia, hashes SHA-256 y una nota de entrega.
- Genera borradores de propuestas con Claude mediante `POST /proposal`.

## Qué no hace

- No crea identidades falsas ni evita KYC.
- No acepta contratos o términos automáticamente.
- No almacena frases semilla ni claves privadas.
- No garantiza que una recompensa sea válida o que vaya a pagarse.
- No ejecuta comandos arbitrarios ni código descargado de clientes.
- No expone la clave de Anthropic ni envía propuestas a plataformas.

## Inicio rápido

Requiere Python 3.10 o posterior y no necesita paquetes externos.

1. Copia `config.example.json` como `config.json`.
2. Completa únicamente nombre, correo y direcciones públicas. Nunca añadas claves privadas.
3. Prueba el agente:

```bash
python agent.py --config config.json --demo
```

4. Ejecuta descubrimiento real:

```bash
python agent.py --config config.json
```

El archivo resultante es una lista para revisar. La siguiente versión puede integrar GitHub y alertas una vez que el propietario conecte sus cuentas mediante autorización oficial.

## Ejecutar un trabajo aprobado

Actualmente el tipo admitido es `json_to_csv`. El agente bloquea el trabajo si
falta aprobación humana, si el pago es inferior al mínimo, si no existe una
referencia de escrow verificado o si una ruta intenta salir del directorio de
trabajo.

1. Copia `job.example.json` y completa sus datos.
2. Coloca el archivo de entrada dentro del espacio de trabajo.
3. Marca `approved_by_owner` y `payment.escrow_verified` como `true` solamente
   después de verificar el contrato y el escrow fuera del agente.
4. Ejecuta:

```bash
python worker.py job.json --config config.json --workspace .
```

El resultado queda en la ruta indicada por `output_path`. La carpeta `evidence/`
contiene un manifiesto JSON y una nota Markdown lista para acompañar la entrega.

## Pruebas

```bash
python -m unittest -v
```

## Servicio de propuestas con Claude

El servicio usa directamente la API Messages de Anthropic y no requiere un
framework web. Necesita dos secretos configurados como variables de entorno:

- `ANTHROPIC_API_KEY`: clave creada en tu cuenta de Anthropic.
- `APP_API_KEY`: contraseña larga para impedir que terceros consuman tu saldo.

Nunca subas esos valores al repositorio. `.env.example` contiene solamente los
nombres y valores de ejemplo.

Inicio local:

```bash
export ANTHROPIC_API_KEY="tu-clave"
export APP_API_KEY="una-contraseña-larga"
python service.py
```

Solicitud:

```bash
curl -X POST http://localhost:8000/proposal \
  -H "Authorization: Bearer $APP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Convert JSON to CSV","description":"Convert records and preserve fields","platform":"Marketplace","budget":"$50","skills":["Python"],"language":"Spanish"}'
```

La respuesta contiene un borrador y `submitted: false`. Debes revisar que cada
afirmación sea cierta antes de enviarlo.

### Railway

Conecta este repositorio y configura el directorio raíz como `/agente-gigs`.
`railway.json` ejecuta las pruebas, inicia `service.py` y comprueba `/health`.
Añade `ANTHROPIC_API_KEY` y `APP_API_KEY` en Variables; no las pongas en GitHub.

### Render

El archivo `/render.yaml` define el servicio, su directorio raíz y el endpoint
de salud. Al crear el Blueprint, Render solicitará `ANTHROPIC_API_KEY` y generará
`APP_API_KEY` sin guardarlas en el repositorio.

## Pagos multimoneda

El agente no prioriza únicamente USDC. Puede considerar SOL y tokens SPL en Solana,
ETH y tokens compatibles en la red EVM configurada, y BTC nativo. Antes de aceptar
un pago verifica moneda, red y dirección. Una dirección EVM no autoriza automáticamente
depósitos en todas las redes EVM: la red exacta debe estar admitida por tu cartera.

## Identidad

El nombre y correo constituyen una identidad operativa, no una persona jurídica. El propietario humano continúa siendo responsable de cuentas, contratos, impuestos, verificaciones y fondos.
