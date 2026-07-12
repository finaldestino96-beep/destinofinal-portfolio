# Destino Bounty Agent

Agente local para descubrir y ordenar oportunidades públicas de recompensas.

## Qué hace

- Consulta una lista configurable de plataformas públicas.
- Detecta enlaces relacionados con recompensas y desafíos.
- Genera `opportunities.json` con puntuación y estado de revisión.
- Clasifica por pago, dificultad, KYC, moneda y red.
- Considera cualquier criptomoneda con una ruta de cobro compatible configurada.
- Mantiene bloqueadas las reclamaciones, entregas y operaciones financieras hasta aprobación humana.

## Qué no hace

- No crea identidades falsas ni evita KYC.
- No acepta contratos o términos automáticamente.
- No almacena frases semilla ni claves privadas.
- No garantiza que una recompensa sea válida o que vaya a pagarse.

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

## Pagos multimoneda

El agente no prioriza únicamente USDC. Puede considerar SOL y tokens SPL en Solana,
ETH y tokens compatibles en la red EVM configurada, y BTC nativo. Antes de aceptar
un pago verifica moneda, red y dirección. Una dirección EVM no autoriza automáticamente
depósitos en todas las redes EVM: la red exacta debe estar admitida por tu cartera.

## Identidad

El nombre y correo constituyen una identidad operativa, no una persona jurídica. El propietario humano continúa siendo responsable de cuentas, contratos, impuestos, verificaciones y fondos.
