# Destino Bounty Agent

Agente local para descubrir y ordenar oportunidades públicas de recompensas.

También puede completar automáticamente tipos de trabajo expresamente admitidos,
si el propietario aprobó el trabajo y registró evidencia de escrow verificado.

## Qué hace

- Consulta una lista configurable de plataformas públicas.
- Detecta enlaces relacionados con recompensas y desafíos.
- Genera `opportunities.json` con puntuación y estado de revisión.
- Clasifica por pago, dificultad, KYC, moneda y red.
- Considera cualquier criptomoneda con una ruta de cobro compatible configurada.
- Mantiene bloqueadas las reclamaciones, entregas y operaciones financieras hasta aprobación humana.
- Ejecuta trabajos JSON→CSV dentro de un espacio de trabajo aislado.
- Produce un manifiesto de evidencia, hashes SHA-256 y una nota de entrega.

## Qué no hace

- No crea identidades falsas ni evita KYC.
- No acepta contratos o términos automáticamente.
- No almacena frases semilla ni claves privadas.
- No garantiza que una recompensa sea válida o que vaya a pagarse.
- No ejecuta comandos arbitrarios ni código descargado de clientes.

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

## Pagos multimoneda

El agente no prioriza únicamente USDC. Puede considerar SOL y tokens SPL en Solana,
ETH y tokens compatibles en la red EVM configurada, y BTC nativo. Antes de aceptar
un pago verifica moneda, red y dirección. Una dirección EVM no autoriza automáticamente
depósitos en todas las redes EVM: la red exacta debe estar admitida por tu cartera.

## Identidad

El nombre y correo constituyen una identidad operativa, no una persona jurídica. El propietario humano continúa siendo responsable de cuentas, contratos, impuestos, verificaciones y fondos.
