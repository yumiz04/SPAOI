# Sistema Inteligente de Gestión y Análisis de Inventarios

**Versión:** 1.0  
**Fecha:** Septiembre de 2026  
**Base de datos:** AdventureWorks PostgreSQL  
**Tipo de sistema:** Aplicación web con agente inteligente para análisis de inventarios

> ## Guía operativa
>
> Este documento contiene la **especificación** (SRS) y, a partir de la
> [sección 24](#24-cómo-funciona-el-sistema), la **guía de operación** del sistema ya
> implementado:
>
> | Sección | Contenido |
> |---|---|
> | [24](#24-cómo-funciona-el-sistema) | Cómo funciona el sistema: arquitectura, capas, flujo de una pregunta, herramientas |
> | [25](#25-instalación-del-sistema) | Instalación completa (Docker y local) y verificación |
> | [26](#26-cómo-acceder-al-sistema) | URLs, puertos, roles, autenticación y API |
> | [27](#27-batería-de-preguntas-para-probar-el-sistema) | **214 comprobaciones**: 164 preguntas para el agente, 41 de API y 9 de base de datos |
>
> Documentación complementaria en cada componente:
> [`inventory_backend/README.md`](inventory_backend/README.md) ·
> [`agente_inventario/README.md`](agente_inventario/README.md) ·
> [`frontend/README.md`](frontend/README.md)
>
> **Credenciales:** este README documenta **nombres** de variables de entorno, nunca
> sus valores. Los secretos viven únicamente en los archivos `.env` de cada componente
> (ignoraros por git) y en el gestor de secretos del proveedor de IA.

---

# 1. Introducción

## 1.1 Propósito

El presente documento especifica los requisitos funcionales y no funcionales del **Sistema Inteligente de Gestión y Análisis de Inventarios**, cuyo propósito es utilizar la información operativa de una organización para analizar el comportamiento de sus existencias, detectar riesgos y proporcionar recomendaciones para apoyar la toma de decisiones relacionadas con el inventario.

El sistema utilizará **AdventureWorks para PostgreSQL** como fuente principal de información operativa. Sobre esta base se incorporarán estructuras adicionales para representar información que AdventureWorks no contempla directamente, como lotes, fechas de caducidad, alertas, configuraciones de riesgo y pronósticos.

El sistema contará con un **agente inteligente** encargado de interpretar solicitudes del usuario, consultar las herramientas disponibles y presentar los resultados de manera comprensible.

---

## 1.2 Alcance

El sistema permitirá:

- Consultar productos y categorías.
- Consultar existencias por ubicación.
- Consultar movimientos de inventario.
- Consultar ventas históricas.
- Consultar órdenes de compra.
- Consultar proveedores y tiempos de entrega.
- Administrar información de lotes y caducidades.
- Detectar riesgos de desabasto.
- Detectar productos próximos a caducar.
- Detectar sobreinventario.
- Analizar rotación de productos.
- Estimar fechas de agotamiento.
- Analizar tendencias de demanda.
- Generar pronósticos.
- Generar alertas.
- Proponer acciones de reposición.
- Proponer redistribuciones entre ubicaciones.
- Responder consultas mediante lenguaje natural.
- Presentar indicadores y resultados analíticos.

El sistema estará orientado principalmente al **apoyo de decisiones**, por lo que las recomendaciones generadas por el agente no modificarán automáticamente el inventario ni realizarán compras sin autorización del usuario.

---

# 2. Descripción general

## 2.1 Perspectiva del producto

El sistema se construirá sobre tres componentes principales:

### Base operativa

AdventureWorks proporcionará información existente relacionada con:

- Productos.
- Categorías.
- Inventario.
- Ubicaciones.
- Movimientos.
- Ventas.
- Proveedores.
- Compras.

### Extensión de inventario

Se agregarán estructuras propias para representar:

- Lotes.
- Fechas de caducidad.
- Alertas.
- Configuración de umbrales.
- Pronósticos.
- Resultados de análisis.

### Agente inteligente

El agente funcionará como una capa de interacción entre el usuario y las herramientas del sistema.

Su función será:

1. Interpretar la solicitud.
2. Determinar qué información necesita.
3. Ejecutar las herramientas correspondientes.
4. Analizar los resultados obtenidos.
5. Explicar los resultados.
6. Generar recomendaciones cuando corresponda.

El agente **no será la fuente primaria de datos**. Los cálculos relacionados con cantidades, ventas, existencias, fechas y movimientos deberán realizarse utilizando información obtenida de la base de datos y funciones analíticas.

---

# 3. Usuarios del sistema

## 3.1 Administrador

El administrador podrá:

- Gestionar usuarios.
- Configurar parámetros del sistema.
- Configurar umbrales de riesgo.
- Consultar información de inventario.
- Consultar alertas.
- Ejecutar análisis.
- Consultar recomendaciones.

## 3.2 Encargado de inventario

Podrá:

- Consultar existencias.
- Consultar productos.
- Consultar lotes.
- Consultar movimientos.
- Consultar ventas.
- Consultar compras.
- Consultar alertas.
- Ejecutar análisis.
- Consultar recomendaciones de reposición.
- Consultar recomendaciones de redistribución.

## 3.3 Usuario analista

Podrá:

- Realizar consultas mediante lenguaje natural.
- Ejecutar análisis.
- Consultar indicadores.
- Consultar tendencias.
- Consultar pronósticos.
- Consultar riesgos detectados.

---

# 4. Arquitectura conceptual

El sistema se organizará en las siguientes capas:

```text
┌─────────────────────────────────────┐
│             FRONTEND                │
│ Dashboard / Chat / Reportes         │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│              API                    │
│ Autenticación / Consultas / Análisis│
└──────────────────┬──────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
┌──────────────────┐ ┌──────────────────┐
│ Agente inteligente│ │ Servicios de    │
│                  │ │ inventario       │
└────────┬─────────┘ └────────┬─────────┘
         │                    │
         ▼                    ▼
┌─────────────────────────────────────┐
│           TOOLS / SERVICIOS         │
│ Inventario | Ventas | Compras       │
│ Lotes | Alertas | Pronósticos       │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│         PostgreSQL / AdventureWorks │
│                                     │
│ AdventureWorks + Extensiones        │
└─────────────────────────────────────┘
```

---

# 5. Requisitos funcionales

## RF-01 — Consulta de productos

El sistema deberá permitir consultar productos registrados en AdventureWorks.

La consulta podrá realizarse mediante:

- ID.
- Nombre.
- Categoría.
- Subcategoría.
- Número de producto.
- Estado.

### Fuente principal

`Production.Product`

---

## RF-02 — Consulta de existencias

El sistema deberá permitir consultar las existencias actuales de un producto.

La información deberá incluir, cuando esté disponible:

- Producto.
- Ubicación.
- Cantidad disponible.
- Nivel de inventario.
- Fecha de actualización.

### Fuente principal

`Production.ProductInventory`

---

## RF-03 — Consulta de movimientos

El sistema deberá permitir consultar movimientos históricos de inventario.

Los movimientos podrán utilizarse para:

- Analizar consumo.
- Analizar entradas y salidas.
- Determinar tendencias.
- Calcular rotación.
- Estimar demanda.

### Fuente principal

`Production.TransactionHistory`

---

## RF-04 — Consulta de ventas

El sistema deberá consultar el historial de ventas para analizar el comportamiento de los productos.

Deberá poder obtener:

- Producto.
- Cantidad vendida.
- Precio.
- Fecha.
- Pedido.
- Descuentos.

### Fuentes principales

`Sales.SalesOrderHeader`

`Sales.SalesOrderDetail`

---

## RF-05 — Consulta de proveedores

El sistema deberá permitir consultar proveedores asociados a productos.

La información deberá incluir:

- Proveedor.
- Producto.
- Tiempo promedio de entrega.
- Precio.
- Cantidad mínima de pedido.
- Cantidad máxima de pedido.
- Cantidad actualmente solicitada.

### Fuente principal

`Purchasing.ProductVendor`

---

## RF-06 — Consulta de órdenes de compra

El sistema deberá permitir consultar órdenes de compra y sus detalles.

Esta información será utilizada para determinar:

- Mercancía pendiente.
- Productos en proceso de reposición.
- Cantidades solicitadas.
- Fechas de orden.
- Proveedores.

### Fuentes principales

`Purchasing.PurchaseOrderHeader`

`Purchasing.PurchaseOrderDetail`

---

# 6. Gestión de lotes

AdventureWorks no proporciona directamente un modelo de lotes con fechas de caducidad, por lo que el sistema deberá incorporar un módulo propio.

## RF-07 — Registro de lotes

El sistema deberá permitir registrar lotes asociados a productos.

Cada lote deberá contener como mínimo:

- Identificador del lote.
- Producto.
- Ubicación.
- Cantidad.
- Fecha de entrada.
- Fecha de caducidad.
- Estado.

Una posible estructura será:

```text
inventory_agent.lotes
```

---

## RF-08 — Consulta de lotes

El sistema deberá permitir consultar:

- Lotes activos.
- Lotes próximos a caducar.
- Lotes caducados.
- Cantidades por lote.
- Productos asociados.

---

## RF-09 — Detección de caducidades

El sistema deberá identificar productos cuyos lotes se encuentren próximos a su fecha de caducidad.

El análisis deberá considerar:

```text
días_para_caducar =
fecha_caducidad - fecha_actual
```

El sistema deberá clasificar el riesgo de acuerdo con los parámetros configurados.

Ejemplo:

| Días restantes | Estado |
|---:|---|
| > 90 | Normal |
| 31–90 | Preventivo |
| 8–30 | Riesgo |
| 0–7 | Crítico |
| < 0 | Caducado |

Los valores deberán ser configurables.

---

# 7. Análisis de inventario

## RF-10 — Análisis general de inventario

El sistema deberá proporcionar un análisis general de las existencias.

Como mínimo deberá poder determinar:

- Total de productos.
- Inventario total.
- Productos sin existencia.
- Productos con existencia baja.
- Productos con sobreinventario.
- Productos con alta rotación.
- Productos con baja rotación.
- Productos próximos a caducar.

---

## RF-11 — Detección de riesgo de desabasto

El sistema deberá identificar productos cuyo inventario pueda ser insuficiente para satisfacer la demanda esperada.

El análisis deberá considerar, cuando exista información suficiente:

- Inventario actual.
- Demanda histórica.
- Demanda promedio.
- Tendencia de consumo.
- Pedidos pendientes.
- Tiempo de entrega del proveedor.

---

## RF-12 — Estimación de agotamiento

El sistema deberá estimar la fecha aproximada en que un producto podría quedarse sin existencias.

Una estimación básica podrá utilizar:

```text
días_de_inventario =
existencia_actual / consumo_diario_promedio
```

El resultado deberá identificarse como una estimación y no como una fecha garantizada.

---

## RF-13 — Análisis de rotación

El sistema deberá calcular indicadores de rotación para identificar productos de:

- Alta rotación.
- Rotación media.
- Baja rotación.
- Sin movimiento.

El cálculo deberá utilizar información histórica de ventas o movimientos.

---

## RF-14 — Detección de sobreinventario

El sistema deberá identificar productos cuya cantidad almacenada sea considerablemente superior a la demanda estimada.

El análisis podrá considerar:

- Inventario actual.
- Demanda promedio.
- Tendencia de ventas.
- Inventario objetivo.
- Pedidos pendientes.

---

# 8. Pronóstico

## RF-15 — Pronóstico de demanda

El sistema deberá generar estimaciones de demanda futura utilizando el historial disponible.

Como mínimo deberá permitir:

- Seleccionar producto.
- Seleccionar periodo histórico.
- Seleccionar horizonte de pronóstico.
- Generar demanda estimada.

Los resultados deberán almacenarse para permitir su consulta posterior.

Una posible estructura será:

```text
inventory_agent.pronosticos
```

---

## RF-16 — Análisis de tendencia

El sistema deberá identificar cambios relevantes en el comportamiento de la demanda.

Ejemplos:

- Incremento progresivo.
- Disminución progresiva.
- Demanda estable.
- Variaciones estacionales.

---

# 9. Alertas

## RF-17 — Generación de alertas

El sistema deberá generar alertas cuando se detecten condiciones de riesgo.

Tipos mínimos:

- `DESABASTO`
- `BAJO_STOCK`
- `SOBREINVENTARIO`
- `BAJA_ROTACION`
- `CADUCIDAD_PROXIMA`
- `PRODUCTO_CADUCADO`
- `AGOTAMIENTO_ESTIMADO`

Las alertas podrán almacenarse en:

```text
inventory_agent.alertas
```

---

## RF-18 — Consulta de alertas

El usuario deberá poder consultar alertas filtrando por:

- Tipo.
- Producto.
- Ubicación.
- Severidad.
- Estado.
- Fecha.

---

## RF-19 — Atención de alertas

El sistema deberá permitir cambiar el estado de una alerta.

Estados sugeridos:

```text
PENDIENTE
REVISADA
ATENDIDA
DESCARTADA
```

El sistema deberá conservar el historial de la alerta.

---

# 10. Reposición

## RF-20 — Propuesta de reposición

El sistema deberá generar propuestas de reposición cuando detecte riesgo de desabasto.

La propuesta deberá considerar:

- Producto.
- Inventario actual.
- Demanda estimada.
- Inventario objetivo.
- Cantidad sugerida.
- Proveedor.
- Tiempo de entrega.
- Cantidad mínima de pedido.
- Cantidad máxima de pedido.

La propuesta **no deberá generar automáticamente una orden de compra**.

---

## RF-21 — Priorización de reposición

Las propuestas podrán clasificarse por nivel de riesgo:

```text
CRÍTICO
ALTO
MEDIO
BAJO
```

La clasificación deberá basarse en parámetros cuantificables.

---

# 11. Redistribución

## RF-22 — Detección de oportunidades de redistribución

El sistema deberá identificar situaciones en las que una ubicación tenga exceso de inventario mientras otra presente riesgo de desabasto.

El análisis deberá considerar:

- Producto.
- Ubicación origen.
- Existencia origen.
- Ubicación destino.
- Existencia destino.
- Demanda.
- Cantidad sugerida para transferencia.

---

## RF-23 — Propuesta de transferencia

El sistema deberá generar una propuesta indicando:

```text
Producto
Origen
Destino
Cantidad sugerida
Motivo
Nivel de prioridad
```

La transferencia deberá requerir confirmación del usuario.

---

# 12. Agente inteligente

## RF-24 — Interacción mediante lenguaje natural

El usuario deberá poder realizar preguntas relacionadas con el inventario utilizando lenguaje natural.

Ejemplos:

> "¿Qué productos tienen riesgo de agotarse?"

> "¿Qué productos tienen baja rotación?"

> "¿Qué productos están próximos a caducar?"

> "¿Cuánto inventario tenemos del producto 680?"

> "¿Qué productos debería reponer primero?"

---

## RF-25 — Selección de herramientas

El agente deberá seleccionar las herramientas necesarias para responder una solicitud.

Herramientas iniciales:

```text
buscar_productos()
obtener_existencias()
obtener_lotes()
obtener_movimientos()
obtener_ventas()
obtener_compras()
obtener_proveedores()

analizar_inventario()
analizar_desabasto()
analizar_caducidades()
analizar_sobreinventario()
analizar_rotacion()

pronosticar_demanda()
estimar_fecha_agotamiento()

proponer_reposicion()
proponer_redistribucion()

obtener_alertas()
crear_alerta()
atender_alerta()
```

---

## RF-26 — Respuestas basadas en datos

El agente deberá fundamentar sus respuestas en información obtenida de las herramientas del sistema.

El modelo de lenguaje no deberá inventar:

- Cantidades.
- Productos.
- Fechas.
- Proveedores.
- Movimientos.
- Alertas.

Cuando no exista información suficiente, deberá indicarlo.

---

## RF-27 — Explicación de resultados

Cuando el agente genere una recomendación deberá proporcionar el motivo.

Ejemplo:

```text
Producto: X

Existencia actual: 18 unidades
Consumo promedio: 7 unidades/día
Agotamiento estimado: 2.6 días
Tiempo promedio de entrega: 5 días

Recomendación:
Considerar una reposición prioritaria debido a que
el tiempo estimado de agotamiento es inferior al tiempo
promedio de entrega del proveedor.
```

---

# 13. Dashboard

## RF-28 — Indicadores principales

El sistema deberá mostrar indicadores como:

- Inventario total.
- Productos con bajo stock.
- Productos en riesgo de desabasto.
- Productos próximos a caducar.
- Productos sobreinventariados.
- Productos de baja rotación.
- Alertas pendientes.

---

## RF-29 — Visualización de tendencias

El sistema deberá permitir visualizar:

- Ventas por periodo.
- Consumo.
- Inventario histórico.
- Demanda estimada.
- Rotación.
- Productos en riesgo.

Las gráficas serán generadas por el frontend a partir de datos estructurados proporcionados por la API.

---

# 14. Requisitos de base de datos

## 14.1 Tablas AdventureWorks utilizadas

El sistema deberá aprovechar principalmente:

```text
Production.Product
Production.ProductInventory
Production.ProductCategory
Production.ProductSubcategory
Production.Location

Production.TransactionHistory

Purchasing.Vendor
Purchasing.ProductVendor
Purchasing.PurchaseOrderHeader
Purchasing.PurchaseOrderDetail

Sales.SalesOrderHeader
Sales.SalesOrderDetail
```

---

## 14.2 Extensiones propias

Se recomienda crear un esquema independiente:

```text
inventory_agent
```

Con estructuras como:

```text
inventory_agent.lotes
inventory_agent.alertas
inventory_agent.configuracion_riesgo
inventory_agent.pronosticos
inventory_agent.analisis
```

Esto permitirá mantener separado el modelo original de AdventureWorks de las funcionalidades desarrolladas específicamente para el sistema.

---

# 15. Requisitos no funcionales

## RNF-01 — Rendimiento

Las consultas operativas comunes deberán responder en un tiempo adecuado para interacción en tiempo real.

Como objetivo inicial:

- Consultas simples: ≤ 2 segundos.
- Consultas analíticas: ≤ 5 segundos.
- Análisis complejos: ≤ 10 segundos.

Los tiempos podrán variar dependiendo del volumen de datos y complejidad de la operación.

---

## RNF-02 — Disponibilidad

El sistema deberá mantener disponible la información de inventario mientras el servicio de base de datos se encuentre operativo.

---

## RNF-03 — Seguridad

El sistema deberá:

- Autenticar usuarios.
- Autorizar operaciones según rol.
- Proteger credenciales.
- Evitar exponer credenciales de base de datos al frontend.
- Validar parámetros recibidos por la API.
- Registrar operaciones relevantes.

---

## RNF-04 — Integridad de datos

El sistema deberá conservar la integridad de:

- Productos.
- Inventarios.
- Movimientos.
- Ventas.
- Compras.
- Lotes.
- Alertas.

No deberán eliminarse registros históricos necesarios para análisis.

---

## RNF-05 — Trazabilidad

Las recomendaciones del agente deberán poder relacionarse con los datos utilizados para generarlas.

---

## RNF-06 — Escalabilidad

La arquitectura deberá permitir incorporar posteriormente:

- Nuevos modelos de pronóstico.
- Nuevas herramientas del agente.
- Nuevas fuentes de datos.
- Nuevas ubicaciones.
- Nuevos indicadores.
- Nuevos tipos de alerta.

---

## RNF-07 — Mantenibilidad

El sistema deberá utilizar una arquitectura modular que permita modificar independientemente:

- API.
- Agente.
- Herramientas.
- Lógica analítica.
- Base de datos.
- Frontend.

---

# 16. Reglas de negocio

## RN-01

El inventario actual deberá obtenerse de la base de datos y no ser generado por el modelo de lenguaje.

## RN-02

Las recomendaciones deberán basarse en datos disponibles y deberán indicar cuando exista incertidumbre.

## RN-03

Una recomendación de reposición no deberá convertirse automáticamente en una orden de compra.

## RN-04

Una recomendación de transferencia no deberá modificar automáticamente las existencias.

## RN-05

Los lotes caducados deberán identificarse independientemente del inventario general.

## RN-06

Los umbrales de bajo stock, caducidad y riesgo deberán ser configurables.

## RN-07

Las alertas deberán conservar su historial.

## RN-08

Las operaciones que modifiquen información crítica deberán requerir autorización.

## RN-09

Los cálculos analíticos deberán ejecutarse mediante servicios o consultas especializadas y no depender de operaciones aritméticas realizadas por el LLM.

## RN-10

El agente deberá utilizar exclusivamente las herramientas autorizadas por el sistema.

---

# 17. Casos de uso principales

## CU-01 — Consultar inventario

**Actor:** Encargado de inventario

1. El usuario solicita información de inventario.
2. El sistema identifica el producto o conjunto de productos.
3. El sistema consulta las existencias.
4. El sistema devuelve las cantidades disponibles.
5. El usuario visualiza el resultado.

---

## CU-02 — Detectar productos en riesgo

**Actor:** Encargado de inventario

1. El usuario solicita productos en riesgo.
2. El agente ejecuta el análisis de desabasto.
3. El sistema obtiene existencias.
4. El sistema obtiene demanda histórica.
5. El sistema considera pedidos pendientes y tiempos de entrega.
6. El sistema calcula el riesgo.
7. El agente presenta los resultados.

---

## CU-03 — Detectar caducidades

1. El usuario solicita productos próximos a caducar.
2. El sistema consulta los lotes.
3. Calcula los días restantes.
4. Clasifica los lotes.
5. Devuelve los productos afectados.

---

## CU-04 — Generar propuesta de reposición

1. El usuario solicita recomendaciones.
2. El sistema analiza existencias.
3. Calcula demanda.
4. Consulta proveedores.
5. Obtiene tiempos de entrega.
6. Calcula cantidades sugeridas.
7. Presenta la propuesta.
8. El usuario decide si realizar la acción.

---

## CU-05 — Analizar baja rotación

1. El usuario solicita productos con baja rotación.
2. El sistema obtiene ventas históricas.
3. Obtiene inventario actual.
4. Calcula indicadores de rotación.
5. Identifica productos con comportamiento de baja rotación.
6. Presenta los resultados.

---

# 18. Herramientas del agente

| Herramienta | Propósito |
|---|---|
| `buscar_productos()` | Buscar productos |
| `obtener_existencias()` | Consultar inventario |
| `obtener_lotes()` | Consultar lotes |
| `obtener_movimientos()` | Consultar movimientos |
| `obtener_ventas()` | Consultar ventas |
| `obtener_compras()` | Consultar compras |
| `obtener_proveedores()` | Consultar proveedores |
| `analizar_inventario()` | Obtener panorama general |
| `analizar_desabasto()` | Detectar riesgo |
| `analizar_caducidades()` | Detectar caducidades |
| `analizar_sobreinventario()` | Detectar exceso |
| `analizar_rotacion()` | Analizar movimiento |
| `pronosticar_demanda()` | Estimar demanda |
| `estimar_fecha_agotamiento()` | Estimar agotamiento |
| `proponer_reposicion()` | Generar reposición |
| `proponer_redistribucion()` | Generar transferencias |
| `obtener_alertas()` | Consultar alertas |
| `crear_alerta()` | Registrar alerta |
| `atender_alerta()` | Actualizar alerta |

---

# 19. Restricciones

1. AdventureWorks será la fuente inicial de información histórica y operativa.
2. AdventureWorks no contiene un sistema completo de lotes y caducidades, por lo que deberá extenderse.
3. El sistema no deberá modificar directamente las tablas originales de AdventureWorks salvo que sea estrictamente necesario.
4. Las funciones analíticas deberán poder ejecutarse independientemente del agente.
5. El LLM no será responsable de almacenar el inventario.
6. El LLM no deberá realizar modificaciones críticas sin autorización.
7. Los pronósticos dependerán de la cantidad y calidad de información histórica disponible.

---

# 20. Criterios de aceptación generales

El sistema será considerado funcional cuando:

- Sea capaz de consultar productos de AdventureWorks.
- Sea capaz de consultar inventario por ubicación.
- Sea capaz de consultar ventas históricas.
- Sea capaz de consultar movimientos.
- Sea capaz de consultar proveedores y tiempos de entrega.
- Sea capaz de registrar y consultar lotes.
- Sea capaz de detectar caducidades.
- Sea capaz de detectar riesgo de desabasto.
- Sea capaz de identificar sobreinventario.
- Sea capaz de analizar rotación.
- Sea capaz de estimar agotamiento.
- Sea capaz de generar pronósticos.
- Sea capaz de generar alertas.
- Sea capaz de generar propuestas de reposición.
- Sea capaz de generar propuestas de redistribución.
- El agente sea capaz de seleccionar las herramientas apropiadas.
- Las respuestas del agente estén respaldadas por datos reales de la base de datos.
- Las acciones críticas requieran confirmación del usuario.

---

# 21. Fuera del alcance inicial

Para la primera versión no se contempla:

- Automatización completa de compras.
- Pago a proveedores.
- Facturación.
- Contabilidad.
- Gestión logística avanzada.
- Optimización automática de rutas.
- Modificación autónoma del inventario por parte del agente.
- Predicción con modelos avanzados de aprendizaje automático como requisito obligatorio.

Estas funcionalidades podrán incorporarse en versiones posteriores.

# 22. Resumen de arquitectura de información

La solución final puede entenderse como:

```text
                    USUARIO
                       │
                       ▼
              ┌─────────────────┐
              │  INTERFAZ WEB   │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │       API       │
              └───────┬─────────┘
                      │
             ┌────────┴────────┐
             │                 │
             ▼                 ▼
      ┌─────────────┐   ┌─────────────┐
      │   AGENTE    │   │  SERVICIOS  │
      │ INTELIGENTE │   │  ANALÍTICOS │
      └──────┬──────┘   └──────┬──────┘
             │                 │
             └────────┬────────┘
                      ▼
              ┌───────────────┐
              │     TOOLS     │
              └───────┬───────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
 ┌───────────────────┐   ┌─────────────────┐
 │   AdventureWorks  │   │  inventory_agent│
 │                   │   │                 │
 │ Productos         │   │ Lotes           │
 │ Inventario        │   │ Alertas         │
 │ Ventas            │   │ Pronósticos     │
 │ Compras           │   │ Configuración   │
 │ Proveedores       │   │ Análisis        │
 │ Movimientos       │   │                 │
 └───────────────────┘   └─────────────────┘
```

La separación anterior permite que **AdventureWorks funcione como núcleo de datos empresariales**, mientras que `inventory_agent` representa la capa específica de inteligencia y gestión que estamos construyendo.

---
---

# PARTE II — GUÍA OPERATIVA

> A partir de aquí se documenta el sistema **tal como está implementado**, no como
> especificación. Las secciones 1 a 23 son el SRS; las secciones 24 a 27 son la guía de
> instalación, uso y prueba.

- [24. Cómo funciona el sistema](#24-cómo-funciona-el-sistema)
- [25. Instalación del sistema](#25-instalación-del-sistema)
- [26. Cómo acceder al sistema](#26-cómo-acceder-al-sistema)
- [27. Batería de preguntas para probar el sistema](#27-batería-de-preguntas-para-probar-el-sistema)

---

# 23. Cómo funciona el sistema

## 23.1 Resumen en una frase

Es un **chat web** en el que preguntas en lenguaje natural sobre el inventario; un **agente
de IA** decide qué datos consultar; una **API Django/DRF** ejecuta los cálculos reales
sobre **PostgreSQL + AdventureWorks**; y el agente te responde con tablas y explicaciones.
El modelo de lenguaje **nunca inventa cifras**: solo orchestra consultas.

## 23.2 Componentes del repositorio

```text
Inventory_System/
├── docker-compose.yml                 # Orquestador de los 4 servicios
├── AdventureWorks-for-Postgres-master/  # Imagen + dump de la BD (PostgreSQL + AW)
├── inventory_backend/                 # API REST Django 5.2 + DRF  (contenedor "api")
│   ├── config/                        # settings, urls, wsgi/asgi
│   ├── apps/                          # 13 apps Django (ver 24.4)
│   ├── requirements/                  # base.txt / dev.txt
│   ├── conftest.py                    # Bootstrap de la BD de pruebas
│   ├── .env.example                   # Plantilla de configuración (sin secretos)
│   └── Dockerfile
├── agente_inventario/                 # Agente conversacional (contenedor "agent")
│   ├── api.py                         # FastAPI: /chat, /chat/reset, /health
│   ├── agente.py                      # Bucle de function calling + despacho
│   ├── tools_inventory.py             # 19 tools + sus esquemas JSON
│   ├── memoria.py                     # Historial por sesión + system prompt
│   ├── e2e_runner.py                  # Batería E2E de 19 prompts
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/                          # Chat web React 19 + Vite (contenedor "frontend")
    ├── src/api/agentClient.ts         # Cliente HTTP del agente
    ├── src/components/chat/           # Composer, burbujas, listas, chips
    ├── src/components/markdown/       # Render de tablas Markdown/GFM
    ├── src/hooks/                     # useChat, useTheme, useAgentHealth
    ├── nginx.conf                     # Proxy /agent/ → agente:8080
    └── Dockerfile                     # Multi-etapa: Node compila, nginx sirve
```

## 23.3 Topología de ejecución (Docker)

```text
                        NAVEGADOR
                            │  http://localhost:5173
                            ▼
        ┌───────────────────────────────────────────┐
        │ frontend   nginx + dist React             │  contenedor "frontend"
        │   location /agent/  ──proxy──►            │
        └──────────────────────┬────────────────────┘
                               │  /agent/chat  (mismo origen, sin CORS)
                               ▼
        ┌───────────────────────────────────────────┐
        │ agent    FastAPI + uvicorn  :8080         │  contenedor "agent"
        │   /chat  /chat/reset  /health  /docs      │  publicado en 8090
        │   agente.py → bucle function calling      │
        │   tools_inventory.py → 19 tools           │
        └──────────────────────┬────────────────────┘
                               │  POST /api/auth/token  (JWT)
                               │  POST /api/agent/tools/<tool>/execute
                               ▼
        ┌───────────────────────────────────────────┐
        │ api      Django + DRF + gunicorn  :8000   │  contenedor "api"
        │   apps/agent/registry.py → execute()      │
        │   apps/*/services.py  apps/*/analyzers/   │
        │   apps/*/repositories.py (ORM)             │
        └──────────────────────┬────────────────────┘
                               │  SQL (psycopg 3)
                               ▼
        ┌───────────────────────────────────────────┐
        │ db       PostgreSQL + AdventureWorks :5432 │  contenedor "db"
        │   esquemas: production, sales, purchasing, │
        │             person, humanresources (solo   │
        │             lectura) + inventory_agent     │
        │             (lotes, alertas, análisis,     │
        │              pronósticos, config, logs)    │
        └───────────────────────────────────────────┘

        Fuera del flujo: proveedor de IA compatible con OpenAI
        (el agente lo llama por HTTPS con su API key)
```

**Claves del diseño:**

| Decisión | Por qué importa |
|---|---|
| El agente **no** habla con PostgreSQL | Toda la lógica de negocio vive en la API; el agente es reemplazable |
| El agente **no** ve el frontend | El navegador solo habla con nginx; el proxy resuelve el agente dentro de la red |
| Un solo origen en el navegador | Evita CORS: mismo prefijo `/agent` en dev (proxy de Vite) y prod (nginx) |
| `search_path=inventory_agent,public` | Django y las tablas propias viven aisladas de AdventureWorks |
| AdventureWorks es `managed=False` | El sistema **no** modifica los datos originales de la empresa |
| Todo cálculo analítico ocurre en SQL/Python | El LLM redacta, **nunca** calcula (regla RN-09) |

## 23.4 Las 13 apps del backend

| App | Responsabilidad | Endpoints principales |
|---|---|---|
| `core` | Envelope JSON, paginación, excepciones, permisos, roles, fechas | `/api/ping`, comandos `setup_roles`, `ensure_superuser` |
| `products` | Catálogo de productos de AdventureWorks | `/api/products`, `/api/products/{id}` |
| `inventory` | Existencias por producto/ubicación, ubicaciones, movimientos | `/api/inventory`, `/api/inventory/{product_id}`, `/api/movements`, `/api/locations` |
| `sales` | Historial de ventas por producto y rango de fechas | `/api/sales` |
| `purchasing` | Órdenes de compra y proveedores | `/api/purchases`, `/api/suppliers` |
| `lots` | Lotes propios con caducidad (no existe en AdventureWorks) | `/api/lots` (CRUD, baja lógica) |
| `risk_config` | Umbrales por capa: global > categoría > producto > defaults | `/api/risk-config`, `/api/risk-config/layers` |
| `analytics` | 7 analizadores: inventario, desabasto, agotamiento, rotación, sobreinventario, caducidades, reglas | `/api/analytics/*` |
| `alerts` | Alertas propias + comando generador | `/api/alerts/`, `generate_alerts` |
| `forecasting` | Pronóstico de suavizado exponencial simple (SES) | `POST /api/forecast` |
| `recommendations` | Propuestas de reposición y redistribución (**nunca** órdenes) | `POST /api/recommendations/*` |
| `dashboard` | Resumen consolidado cacheado 120 s | `/api/dashboard/summary` |
| `agent` | 19 herramientas con JSON Schema, validación pydantic y `ToolLog` | `/api/agent/tools`, `/api/agent/tools/{name}/execute` |

## 23.5 Flujo completo de una pregunta (ejemplo real)

Usuario escribe en el chat: **"¿Qué productos debería reponer primero?"**

```text
 1. frontend  →  POST /agent/chat  {"message": "...", "session_id": "abc"}
                (nginx hace proxy a http://agent:8080/chat)

 2. agent/api.py  →  valida el esquema, resuelve la memoria de la sesión
                     (deque de 20 mensajes protegida con Lock)

 3. agente.responder(memory, texto, MAX_TOOL_ROUNDS=8)
       └─ system prompt + historial + catálogo de 19 tools → proveedor de IA

 4. El modelo responde con tool_calls, por ejemplo:
       ronda 1 → proponer_reposicion({})
                  obtener_existencias({...})
                  obtener_proveedores({product_id: ...})
       ronda 2 → obtener_compras({product_id: ...})
                  analizar_desabasto({riesgo_minimo: "ALTO"})
       ronda 3 → (sin tool_calls) → redacta la respuesta final en Markdown

 5. Por cada tool_call, tools_inventory.py hace:
       POST /api/agent/tools/<nombre>/execute
       Authorization: Bearer <JWT del usuario del agente>
       {"parameters": {...}}          ← solo los parámetros no nulos

 6. api → apps/agent/registry.py
       ├─ valida con pydantic  → VALIDATION_ERROR si algo no cuadra
       ├─ ejecuta el service/analyzer correspondiente
       ├─ SIEMPRE responde HTTP 200 con envelope {success, data, message, code}
       └─ registra la traza en agent_tool_log (ToolLog)

 7. El resultado JSON vuelve al agente como mensaje role="tool".
       El modelo lo lee y decide: pedir más datos o redactar.

 8. La respuesta final (texto Markdown) viaja de vuelta al navegador,
       que la renderiza con react-markdown y tablas GFM.

 9. Trazabilidad: la ejecución queda en `inventory_agent.analisis`
       y en `inventory_agent.agent_tool_log`.
```

**Punto clave:** una sola pregunta puede disparar **varias** herramientas y varias rondas.
El bucle está acotado a 8 rondas; si no converge, el agente lo dice en lugar de inventar.

## 23.6 Las 19 herramientas del agente

Todas se invocan por el mismo endpoint genérico
`POST /api/agent/tools/{nombre}/execute`. 17 son de **solo lectura**; 2 escriben.

| # | Herramienta | Familia | Parámetros principales | Escribe |
|--:|---|---|---|:-:|
| 1 | `buscar_productos` | Consulta | `texto`, `categoria`, `limite` | no |
| 2 | `obtener_existencias` | Consulta | `product_id`, `location_id` | no |
| 3 | `obtener_lotes` | Consulta | `product_id`, `status`, `vence_en_dias` | no |
| 4 | `obtener_movimientos` | Consulta | `product_id`*, `fecha_inicio`, `fecha_fin`, `tipo` | no |
| 5 | `obtener_ventas` | Consulta | `product_id`*, `fecha_inicio`, `fecha_fin` | no |
| 6 | `obtener_compras` | Consulta | `product_id`, `vendor_id`, `estado` | no |
| 7 | `obtener_proveedores` | Consulta | `product_id`* | no |
| 8 | `analizar_inventario` | Analítica | `product_id`, `categoria` | no |
| 9 | `analizar_desabasto` | Analítica | `riesgo_minimo`, `product_id`, `limite` | no |
| 10 | `analizar_caducidades` | Analítica | `dias`, `product_id` | no |
| 11 | `analizar_sobreinventario` | Analítica | `categoria`, `limite` | no |
| 12 | `analizar_rotacion` | Analítica | `clase`, `ventana_dias` | no |
| 13 | `pronosticar_demanda` | Predictiva | `product_id`*, `dias_historicos`, `dias_pronostico` | no |
| 14 | `estimar_fecha_agotamiento` | Predictiva | `product_id`* | no |
| 15 | `proponer_reposicion` | Decisión | `product_id`, `categoria` | no (solo propuesta) |
| 16 | `proponer_redistribucion` | Decisión | `product_id`, `categoria` | no (solo propuesta) |
| 17 | `obtener_alertas` | Alertas | `tipo`, `severidad`, `estado` | no |
| 18 | `crear_alerta` | Alertas | `product_id`*, `tipo`*, `severidad`*, `mensaje`* | **SÍ** |
| 19 | `atender_alerta` | Alertas | `alerta_id`*, `nota` | **SÍ** |

`*` = obligatorio. Las herramientas 18 y 19 exigen rol `inventory_manager` (403 si no).

**Catálogos de valores válidos** (útiles para probar y para depurar respuestas raras):

| Contexto | Valores |
|---|---|
| `obtener_lotes.status` | `ACTIVO`, `AGOTADO`, `CADUCADO`, `BLOQUEADO`, `ELIMINADO` |
| `obtener_movimientos.tipo` | `W` trabajo · `S` venta · `P` compra |
| `obtener_compras.estado` | `1` Pendiente · `2` Aprobada · `3` Rechazada · `4` Completa |
| `analizar_desabasto.riesgo_minimo` | `CRITICO`, `ALTO`, `MEDIO`, `BAJO` (def. `ALTO`) |
| `analizar_rotacion.clase` | `ALTA_ROTACION`, `ROTACION_MEDIA`, `BAJA_ROTACION`, `SIN_MOVIMIENTO` |
| `obtener_alertas.tipo` | `DESABASTO`, `BAJO_STOCK`, `SOBREINVENTARIO`, `BAJA_ROTACION`, `CADUCIDAD_PROXIMA`, `PRODUCTO_CADUCADO`, `AGOTAMIENTO_ESTIMADO` |
| `*.severidad` | `BAJA`, `MEDIA`, `ALTA`, `CRITICA` |
| `obtener_alertas.estado` | `PENDIENTE`, `ATENDIDA`, `DESCARTADA` |

## 23.7 Cómo se calculan las métricas (sin intervención del LLM)

Todas las métricas usan `as_of_date()` como "hoy", es decir `ANALYSIS_AS_OF_DATE`. Por eso
los resultados son **reproducibles** y no dependen del día en que consultas.

| Métrica | Criterio de cálculo |
|---|---|
| Demanda diaria | Consumo (movimientos/ventas) ÷ días de la ventana de análisis (90 por defecto) |
| Días de inventario | `existencia_actual ÷ demanda_diaria` |
| Riesgo de desabasto | Compara días de inventario **+ pedidos pendientes** contra el *lead time* del proveedor y el nivel de servicio (`service_level_z`, 1.65) |
| Fecha estimada de agotamiento | `as_of_date + días_de_inventario` |
| Rotación | Consumo del periodo ÷ inventario medio; se clasifica con `low_turnover_threshold` (1.0) y `high_turnover_threshold` (6.0) |
| Sobreinventario | Existencia − demanda × `overstock_days_of_cover` (180 por defecto) |
| Caducidad | `días_para_caducar = fecha_caducidad − as_of_date`, clasificado por `expiry_warning_days` (30) |
| Pronóstico SES | `nivel` y `sigma` con suavizado exponencial simple (`alpha` configurable) |
| Reposición | Inventario objetivo = demanda del periodo de revisión (7) + demanda durante el *lead time* + stock de seguridad; se ajusta al mínimo/máximo de pedido del proveedor |

**Precedencia de umbrales:** `producto` > `categoría` > `global` > valores por defecto.
Puedes cambiarla en caliente con `PATCH /api/risk-config` sin tocar código.

## 23.8 Autenticación, roles y seguridad

| Capa | Mecanismo |
|---|---|
| API ↔ Base de datos | Credenciales de conexión por entorno (`DB_*`), nunca en el código ni en el frontend |
| Usuario ↔ API | JWT (SimpleJWT). Access 30 min, refresh 1 día. Todas las rutas `/api/*` exigen `Authorization: Bearer` |
| Agente ↔ API | El agente se autentica una vez con su propio usuario (`INVENTORY_API_USER`) y renueva el token automáticamente ante un 401 |
| Navegador ↔ Frontend | Sin credenciales: el navegador nunca habla con la API, solo con nginx |
| Autorización | 3 roles: `viewer`, `analyst`, `inventory_manager` (+ superusuario) |

| Rol | Puede hacer |
|---|---|
| `viewer` | Todo lo de lectura: consultas, analítica, tablero, 17 herramientas del agente |
| `analyst` | Lo anterior + `POST /api/recommendations/*` |
| `inventory_manager` | Todo + CRUD de lotes, alertas y las 2 herramientas que escriben |

| Regla | Implementación |
|---|---|
| El agente no inventa datos | System prompt explícito + todas las cifras salen de tools; si no hay datos, lo dice |
| El agente no ejecuta decisiones | `proponer_*` devuelve propuestas; jamás crea órdenes ni transfiere stock (RN-03, RN-04) |
| Las tools no tocan la BD | Prohibido importar `django.db` o `models` dentro de `apps/agent/tools` (test de arquitectura automático) |
| Sin excepción cruda hacia el LLM | `registry.execute()` convierte cualquier fallo en `{success:false, code, message}` |
| Rate limit | `/api/agent/*` limitado a 120/min (`AGENT_THROTTLE_RATE`) → 429 `THROTTLED` |
| Trazabilidad | Cada tool se registra en `agent_tool_log`; cada análisis en `analisis` |
| Rotación de logs | `purge_tool_logs` borra trazas mayores a `AGENT_TOOL_LOG_RETENTION_DAYS` (180) |

# 24. Instalación del sistema

## 24.1 Requisitos previos

| Componente | Versión | Necesario para |
|---|---|---|
| Docker Desktop con Compose v2 | reciente | Opción A (todo en contenedores) |
| Python | 3.12+ (probado en 3.12 y 3.14) | Opción B (backend y agente en el host) |
| Node.js | 20+ | Solo siVas a construir el frontend fuera de Docker |
| PostgreSQL | 15+ con el dump de AdventureWorks | Solo si vas a usar una BD propia |
| Espacio en disco | ~3 GB | Dump de AdventureWorks + imágenes |

## 24.2 Opción A — Todo con Docker (recomendada)

### 24.2.1 Preparar la configuración (sin credenciales en el repo)

Cada componente lee su propio `.env` (Variables de entorno), ignorado por git. Crea los tres a partir de las
plantillas (renombra las de .env.examples -> .env) o desde cero con **tus propios valores**:

| Archivo | Variables que debe definir |
|---|---|
| `inventory_backend/.env` | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `ANALYSIS_AS_OF_DATE`, `AGENT_THROTTLE_RATE`, `AGENT_TOOL_LOG_RETENTION_DAYS`, `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL` |
| `agente_inventario/.env` | `API_OPENCODE_KEY`, `API_OPENCODE_URL`, `API_OPENCODE_MODEL`, `API_OPENCODE_MAX_TOKENS`, `INVENTORY_API_URL`, `INVENTORY_API_USER`, `INVENTORY_API_PASSWORD`, `AGENT_CORS_ORIGINS` (opcional) |
| `frontend/.env` (opcional) | `VITE_AGENT_BASE_URL` solo si sirves el build en otro dominio |

Detalles importantes:

- `DB_NAME` debe coincidir con la base que crea el dump de AdventureWorks: **`Adventureworks`**.
- `DB_USER` / `DB_PASSWORD` deben ser las credenciales reales del servidor PostgreSQL
  (las de desarrollo están declaradas en `docker-compose.yml`; ajústalas si las cambiaste).
- `DJANGO_ALLOWED_HOSTS` debe incluir `api` (hostname interno del contenedor) además de
  `localhost` y `127.0.0.1`, o el agente recibirá HTTP 400 al llamar a la API.
- `ANALYSIS_AS_OF_DATE` es la fecha de referencia de **todos** los análisis. El dump
  incluido tiene datos de 2022 a 2025: usa una fecha de ese rango (por ejemplo
  `2025-06-29`, el valor con el que se validó el sistema).
- `API_OPENCODE_MAX_TOKENS` **no debe bajar de ~2000**: el modelo consume tokens en
  razonamiento y, si se corta, devuelve una respuesta vacía.
- `INVENTORY_API_USER` debe tener rol `inventory_manager` si quieres que el agente pueda
  crear y cerrar alertas.
- En Docker, el compose sobrescribe `INVENTORY_API_URL` a `http://api:8000`, `DB_HOST` a
  `db` y `DJANGO_SETTINGS_MODULE` a `config.settings.production`.

### 24.2.2 Levantar la plataforma

```powershell
cd C:\~~\Inventory_System
docker compose up -d --build
```

La primera vez tarda varios minutos: compila la imagen de AdventureWorks, la del backend y
la del agente, y el frontend. Las siguientes son segundos.

El arranque hace, en orden:

```text
db → importa el dump de AdventureWorks
api → migrate → setup_roles → ensure_superuser → gunicorn
agent → uvicorn en :8080
frontend → nginx sirviendo en :80
```

### 24.2.3 Verificar que todo está arriba

```powershell
docker compose ps
# los 4 servicios "Up"; "db" debe aparecer como (healthy)
docker compose logs --tail 20 api      
# debe terminar con el arranque de gunicorn
docker compose logs --tail 20 agent

http://localhost:8090/health   # {"status":"ok"}
```

| Comprobación | Cómo | Resultado esperado |
|---|---|---|
| Base de datos cargada | `docker compose exec db psql -U <tu_usuario> -d Adventureworks -c "select count(*) from production.product;"` | `504` |
| API viva | `curl http://localhost:8000/api/ping` | 401 si no hay token (es correcto: exige autenticación) |
| Agente vivo | `curl http://localhost:8090/health` | `{"status":"ok"}` |
| Frontend vivo | abrir <http://localhost:5173> | Pantalla de chat con sugerencias |

### 24.2.4 Cargar datos propios (recomendado para la demo)

El compose aplica las migraciones, pero **no** siembra datos propios de la capa inteligente.
Para ver lotes, alertas y caducidades con contenido:

```powershell
# Lotes de ejemplo: caducidades repartidas a -20 / +10 / +30 / +90 días
docker compose exec api python manage.py seed_lots
docker compose exec api python manage.py seed_lots --products 50 --seed 42

# Alertas derivadas de los analizadores (idempotente)
docker compose exec api python manage.py generate_alerts
docker compose exec api python manage.py generate_alerts --dry-run   # solo informa

# Política de retención de trazas del agente
docker compose exec api python manage.py purge_tool_logs --dry-run
```

### 24.3.5 Tabla resumen de puertos

| Servicio | Host (Docker) | Host (local) | Contenedor |
|---|---|---|---|
| PostgreSQL | 5432 | 5432 | 5432 |
| API Django | 8000 | 8000 | 8000 |
| Agente FastAPI | **8090** | 8080 | 8080 |
| Frontend | 5173 | 5173 | 80 |


# 25. Cómo acceder al sistema

## 25.1 El acceso principal: el chat web

| | |
|---|---|
| **URL** | <http://localhost:5173> |
| **Qué es** | La interfaz de chat del agente de inventario |
| **Requiere** | Los 4 contenedores arriba y el proveedor de IA configurado |
| **Credenciales** | **Ninguna en el navegador**: es una interfaz de consulta |

Al abrirla verás el chat vacío con 8 preguntas sugeridas y un aviso de que las cifras
provienen del dataset AdventureWorks con fecha de análisis `2025-06-29`.

Qué puedes hacer desde ahí:

| Acción | Cómo |
|---|---|
| Preguntar | Escribe en el compositor y pulsa **Enviar** (Enter envía, Shift+Enter añade línea) |
| Usar sugerencia | Clic en cualquiera de los 8 chips de la pantalla inicial |
| Detener una respuesta | Botón **Detener** (corta la petición en vuelo) |
| Empezar de cero | Botón **Nueva conversación** (genera `session_id` nuevo y llama a `/chat/reset`) |
| Copiar una respuesta | Botón de copiar en cada burbuja del agente |
| Cambiar tema | Toggle claro/oscuro, se recuerda en `localStorage` |

**Tiempos:** cada respuesta tarda entre 10 y 120 segundos, porque el agente puede encadenar
varias herramientas y varias rondas del modelo. La UI lo indica con "Consultando el
inventario".

### 25.3.2 URLs útiles

| URL | Descripción |
|---|---|
| <http://localhost:8000/api/docs/> | **Swagger UI** interactivo (requiere token) |
| <http://localhost:8000/api/schema/> | Esquema OpenAPI |
| <http://localhost:8000/admin/> | Administración de Django (datos, alertas, lotes, usuarios) |
| <http://localhost:8000/api/ping> | Salud de la API + usuario autenticado |
| <http://localhost:8000/api/dashboard/summary> | Resumen del tablero en JSON |
| <http://localhost:8000/api/agent/tools> | Catálogo de las 19 herramientas con su JSON Schema |

### 25.3.4 Mapa completo de endpoints

| Método | Ruta | Roles | Descripción |
|---|---|---|---|
| GET | `/api/ping` | autenticado | Salud + usuario |
| POST | `/api/auth/token` | anónimo | Obtener tokens |
| POST | `/api/auth/refresh` | anónimo | Renovar token |
| GET | `/api/schema/`, `/api/docs/` | autenticado | OpenAPI / Swagger UI |
| GET | `/api/products`, `/api/products/{id}` | autenticado | Catálogo (filtros: `category`, `subcategory`, `name`, `search`) |
| GET | `/api/inventory`, `/api/inventory/{product_id}` | autenticado | Existencias por ubicación / agregadas |
| GET | `/api/movements` | autenticado | Movimientos (`product`, `date_from`, `date_to`, `type`) |
| GET | `/api/locations` | autenticado | Ubicaciones |
| GET | `/api/sales` | autenticado | Ventas (`product`, `start_date`, `end_date`) |
| GET | `/api/purchases` | autenticado | Compras (`product`, `vendor`, `status`) |
| GET | `/api/suppliers` | autenticado | Proveedores por producto |
| GET / POST | `/api/lots` | lectura: todos · escritura: manager | Lotes (`expiring_within`, `status`) |
| GET / PATCH / DELETE | `/api/lots/{id}` | lectura: todos · escritura: manager | Lote (DELETE = baja lógica) |
| GET / PATCH | `/api/risk-config` | lectura: todos · escritura: manager | Umbrales resueltos / *upsert* |
| GET | `/api/risk-config/layers` | autenticado | Capas configuradas |
| GET | `/api/analytics/stockout` | autenticado | Riesgo de desabasto |
| GET | `/api/analytics/depletion`, `/api/analytics/depletion/{product_id}` | autenticado | Fecha estimada de agotamiento |
| GET | `/api/analytics/turnover` | autenticado | Rotación |
| GET | `/api/analytics/overstock` | autenticado | Sobreinventario |
| GET | `/api/analytics/expiration` | autenticado | Caducidades por urgencia |
| GET | `/api/analytics/inventory` | autenticado | Totales, días de inventario y valor por categoría |
| GET / POST | `/api/alerts/` | lectura: todos · escritura: manager | Alertas (`type`, `severity`, `status`, `product_id`) |
| PATCH | `/api/alerts/{id}/` | manager | Cerrar alerta (`ATENDIDA` / `DESCARTADA`) |
| POST | `/api/forecast` | autenticado | Pronóstico SES |
| POST | `/api/recommendations/replenishment` | analyst / manager | Propuesta de reposición |
| POST | `/api/recommendations/redistribution` | analyst / manager | Propuesta de traspasos |
| GET | `/api/dashboard/summary` | autenticado | Resumen del tablero (cache 120 s) |
| GET | `/api/agent/tools` | autenticado | Catálogo de herramientas |
| POST | `/api/agent/tools/{name}/execute` | lectura: todos · escritura: manager | Ejecutar herramienta |

> `alerts` usa `DefaultRouter`, así que **lleva barra final** (`/api/alerts/`). El resto usa
> `SimpleRouter` y **no** lleva barra final.

### 25.3.5 Envoltura de respuestas y errores

Éxito:

```json
{ "success": true, "data": { "...": "..." }, "message": null }
```

Error controlado:

```json
{ "success": false, "data": null, "message": "Producto no encontrado", "code": "PRODUCT_NOT_FOUND" }
```

| Código HTTP | `code` habitual |
|---|---|
| 400 | `VALIDATION_ERROR` |
| 401 | `NOT_AUTHENTICATED` |
| 403 | `PERMISSION_DENIED` (falta el rol) |
| 404 | `NOT_FOUND` |
| 409 | `CONFLICT`, `DUPLICATE_LOT`, `DUPLICATE_ALERT`, `ALERT_ALREADY_CLOSED` |
| 429 | `THROTTLED` (se superó el rate limit de `/api/agent/*`) |
| 500 | `INTERNAL_ERROR` |

> Las ejecuciones de herramientas **siempre devuelven HTTP 200**, incluso ante error de
> dominio: el resultado real va en `success`/`code` del cuerpo. Es por eso que el frontend
> detecta fallos del agente por texto y no por código HTTP.

Listados paginados: `count`, `page`, `page_size` (20 por defecto, máx. 100), `next`,
`previous`, `results`. Orden con `?ordering=campo` y `?ordering=-campo`.

# 26. Batería de preguntas para probar el sistema

> **Cómo usar esta sección**
>
> - **Preguntas para el chat**: pega el texto tal cual en
>   <http://localhost:5173>. La columna *Herramienta esperada* indica qué
>   herramienta **debería** activar el agente; sirve para verificar que no está inventando
>   una ruta alternativa.
> - **Comprobaciones de API** (27.19 y 27.20): validan la API y la base de datos directamente,
>   sin depender del LLM.
> - Las preguntas de la sección 27.15 **escriben en la base de datos** (crean o cierran
>   alertas). Ejecuta primero `seed_lots` y `generate_alerts` para tener datos.
> - **Reinicia el contexto** (`/chat/reset` o "Nueva conversación") antes de las pruebas de
>   memoria de la sección 27.16.
> - Los identificadores de ejemplo (`680`, `876`, `776`, ubicación `6`) salen del dataset
>   AdventureWorks. Puedes sustituirlos por los que aparezcan en tus respuestas.

## 26.1 Smoke test: las 8 preguntas sugeridas de la UI

Empiecen por aquí: son los botones de la pantalla inicial y cubren las 8 familias de
análisis.

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 1 | `Dame un panorama general del inventario` | `analizar_inventario` |
| 2 | `¿Qué productos tienen riesgo de agotarse?` | `analizar_desabasto` |
| 3 | `¿Qué productos debería reponer primero?` | `proponer_reposicion` |
| 4 | `¿Qué productos tienen exceso de inventario?` | `analizar_sobreinventario` |
| 5 | `Analiza la rotación del inventario` | `analizar_rotacion` |
| 6 | `¿Qué lotes están próximos a caducar?` | `analizar_caducidades` |
| 7 | `¿Cuántas existencias hay del producto 680 y en qué ubicaciones?` | `obtener_existencias` |
| 8 | `Muéstrame las alertas pendientes` | `obtener_alertas` |

## 26.2 Panorama general e indicadores

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 9 | `¿Cuántos productos hay en el catálogo?` | `buscar_productos` + `analizar_inventario` |
| 10 | `Dame un resumen ejecutivo del inventario en 5 líneas` | `analizar_inventario` |
| 11 | `¿Cuál es el valor total del inventario?` | `analizar_inventario` |
| 12 | `¿Cuántos días de inventario tenemos en total?` | `analizar_inventario` |
| 13 | `Muéstrame el inventario desglosado por categoría` | `analizar_inventario` |
| 14 | `¿Qué categoría tiene más valor de inventario?` | `analizar_inventario` |
| 15 | `¿Cuántos productos no tienen ninguna existencia?` | `analizar_inventario` |
| 16 | `¿Cuál es el inventario total del producto 680?` | `analizar_inventario` |
| 17 | `¿Qué pasa con el inventario de la categoría Componentes?` | `analizar_inventario` |
| 18 | `Compara el inventario de las categorías Bikes y Components` | `analizar_inventario` |
| 19 | `¿Desde qué fecha se están calculando estos análisis?` | cualquier tool (debe mencionar `as_of_date`) |
| 20 | `Haz un diagnóstico completo del estado del inventario` | varias (analizadores combinados) |

## 26.3 Existencias y ubicaciones

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 21 | `¿Cuántas unidades hay del producto 680?` | `obtener_existencias` |
| 22 | `¿En qué ubicaciones está repartido el producto 680?` | `obtener_existencias` |
| 23 | `¿Cuántas existencias hay del producto 680 en la ubicación 6?` | `obtener_existencias` |
| 24 | `Muéstrame todas las existencias de la ubicación 7` | `obtener_existencias` |
| 25 | `¿Qué 10 productos tienen más unidades almacenadas?` | `obtener_existencias` + `analizar_inventario` |
| 26 | `¿Qué productos tienen menos de 100 unidades?` | `obtener_existencias` |
| 27 | `Dame las existencias del Mountain-100 Silver, 38` | `buscar_productos` + `obtener_existencias` |
| 28 | `¿En qué estanterías y casilleros está el producto 680?` | `obtener_existencias` |
| 29 | `Compara las existencias del producto 680 entre dos ubicaciones` | `obtener_existencias` |
| 30 | `¿Hay algún producto con existencia cero?` | `obtener_existencias` |

## 26.4 Búsqueda y catálogo de productos

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 31 | `Busca productos que contengan "Road"` | `buscar_productos` |
| 32 | `¿Qué bicicletas tienes en el catálogo?` | `buscar_productos` |
| 33 | `Busca el producto "Helmet"` | `buscar_productos` |
| 34 | `¿Cuál es el producto con el número GL-HB-100?` | `buscar_productos` |
| 35 | `Muéstrame los productos de la categoría Bikes` | `buscar_productos` |
| 36 | `Dame los 20 productos más caros` | `buscar_productos` |
| 37 | `Busca productos de ropa` | `buscar_productos` |
| 38 | `¿Qué subcategorías existen dentro de Bikes?` | `buscar_productos` |
| 39 | `¿Cuántos modelos de bicicleta hay?` | `buscar_productos` |
| 40 | `Encuentra productos que contengan "Mountain" y dime su precio` | `buscar_productos` |

## 26.5 Riesgo de desabasto

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 41 | `¿Qué productos tienen riesgo de agotarse?` | `analizar_desabasto` |
| 42 | `¿Qué productos están en riesgo CRÍTICO de desabasto?` | `analizar_desabasto` (`riesgo_minimo=CRITICO`) |
| 43 | `Muéstrame los 10 productos con mayor riesgo de desabasto` | `analizar_desabasto` (`limite=10`) |
| 44 | `¿El producto 680 tiene riesgo de desabasto?` | `analizar_desabasto` |
| 45 | `¿Qué productos de la categoría Bikes están en riesgo?` | `analizar_desabasto` |
| 46 | `Explica por qué el producto 876 está en riesgo de desabasto` | `analizar_desabasto` + `obtener_existencias` |
| 47 | `¿Con qué margen de tiempo cuento antes de quedarme sin el producto 680?` | `analizar_desabasto` + `estimar_fecha_agotamiento` |
| 48 | `Dame el riesgo de desabasto del producto 680 con todas sus cifras` | `analizar_desabasto` |
| 49 | `¿Cuántos productos están en riesgo de nivel ALTO o superior?` | `analizar_desabasto` |
| 50 | `¿Algún producto en riesgo se queda sin pedidos pendientes?` | `analizar_desabasto` + `obtener_compras` |

## 26.6 Fecha estimada de agotamiento

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 51 | `¿Cuándo se va a agotar el producto 680?` | `estimar_fecha_agotamiento` |
| 52 | `¿En cuántos días se agota el producto 680?` | `estimar_fecha_agotamiento` |
| 53 | `¿Qué productos se agotan antes de 7 días?` | `estimar_fecha_agotamiento` |
| 54 | `¿Cuándo se agotará el Mountain-100 Silver, 38?` | `buscar_productos` + `estimar_fecha_agotamiento` |
| 55 | `¿Cuánto inventario le queda al producto 776?` | `obtener_existencias` + `estimar_fecha_agotamiento` |

## 26.7 Lotes y caducidades

> Requiere `python manage.py seed_lots`.

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 56 | `Muéstrame los lotes registrados` | `obtener_lotes` |
| 57 | `¿Qué lotes están próximos a caducar?` | `analizar_caducidades` |
| 58 | `¿Qué lotes se caducan en los próximos 30 días?` | `analizar_caducidades` (`dias=30`) |
| 59 | `¿Qué lotes ya están caducados?` | `obtener_lotes` (`status=CADUCADO`) |
| 60 | `Muéstrame los lotes activos del producto 680` | `obtener_lotes` |
| 61 | `¿Qué lotes bloqueados hay?` | `obtener_lotes` (`status=BLOQUEADO`) |
| 62 | `¿Qué producto tiene más lotes próximos a caducar?` | `analizar_caducidades` |
| 63 | `¿Cuántas unidades están en lotes caducados?` | `analizar_caducidades` |
| 64 | `¿Qué lote caduca primero y en qué ubicación está?` | `analizar_caducidades` |
| 65 | `¿Cuántos días le quedan al lote SEED-680-6-1?` | `obtener_lotes` |

## 26.8 Rotación

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 66 | `Analiza la rotación del inventario` | `analizar_rotacion` |
| 67 | `¿Qué productos tienen alta rotación?` | `analizar_rotacion` (`clase=ALTA_ROTACION`) |
| 68 | `¿Qué productos tienen baja rotación?` | `analizar_rotacion` (`clase=BAJA_ROTACION`) |
| 69 | `¿Qué productos no tienen ningún movimiento?` | `analizar_rotacion` (`clase=SIN_MOVIMIENTO`) |
| 70 | `¿Cuál es la rotación del producto 680?` | `analizar_rotacion` |
| 71 | `Analiza la rotación en los últimos 180 días` | `analizar_rotacion` (`ventana_dias=180`) |
| 72 | `¿Qué productos de rotación media hay?` | `analizar_rotacion` (`clase=ROTACION_MEDIA`) |
| 73 | `¿Qué implicaciones tiene un producto de baja rotación?` | `analizar_rotacion` |
| 74 | `¿Cuántos productos tienen baja rotación en la categoría Bikes?` | `analizar_rotacion` |

## 26.9 Sobreinventario

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 75 | `¿Qué productos tienen exceso de inventario?` | `analizar_sobreinventario` |
| 76 | `Dame los 20 productos con más sobreinventario` | `analizar_sobreinventario` (`limite=20`) |
| 77 | `¿Qué productos de la categoría Bikes están sobreinventariados?` | `analizar_sobreinventario` |
| 78 | `¿Cuánto exceso de inventario hay en el producto 680?` | `analizar_sobreinventario` |
| 79 | `¿Qué producto tiene más capital inmovilizado?` | `analizar_sobreinventario` + `obtener_existencias` |
| 80 | `¿Cuántos días de cobertura tienen los productos sobreinventariados?` | `analizar_sobreinventario` |

## 26.10 Pronóstico de demanda

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 81 | `Pronostica la demanda del producto 680 para los próximos 7 días` | `pronosticar_demanda` |
| 82 | `¿Cuál será la demanda del producto 680 en 30 días?` | `pronosticar_demanda` (`dias_pronostico=30`) |
| 83 | `Pronostica la demanda del producto 680 con 365 días de histórico` | `pronosticar_demanda` (`dias_historicos=365`) |
| 84 | `¿La demanda del producto 680 va a subir o a bajar?` | `pronosticar_demanda` |
| 85 | `Dame el pronóstico diario del Mountain-100 Silver, 38` | `buscar_productos` + `pronosticar_demanda` |
| 86 | `¿Cuál es el nivel y la sigma del pronóstico del producto 680?` | `pronosticar_demanda` |
| 87 | `¿Qué tan confiable es el pronóstico del producto 680?` | `pronosticar_demanda` |

## 26.11 Propuestas de reposición

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 88 | `¿Qué productos debería reponer primero?` | `proponer_reposicion` + `analizar_desabasto` |
| 89 | `¿Cuántas unidades debería comprar del producto 680?` | `proponer_reposicion` |
| 90 | `Proponme una reposición del producto 680 y justifícala` | `proponer_reposicion` |
| 91 | `¿Qué proveedores debería usar para reponer el producto 680?` | `proponer_reposicion` + `obtener_proveedores` |
| 92 | `¿Qué productos de la categoría Bikes necesitan reposición?` | `proponer_reposicion` |
| 93 | `¿La cantidad que recomiendas para el producto 680 respeta el mínimo del proveedor?` | `proponer_reposicion` + `obtener_proveedores` |
| 94 | `Prioriza las reposiciones por nivel de riesgo, de mayor a menor` | `proponer_reposicion` |
| 95 | `¿Ya hay algo pedido del producto 680?` | `obtener_compras` + `proponer_reposicion` |
| 96 | `Dame una propuesta de reposición para todos los productos en riesgo crítico` | `proponer_reposicion` + `analizar_desabasto` |

## 26.12 Propuestas de redistribución

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 97 | `¿Puedo redistribuir inventario del producto 680 entre ubicaciones?` | `proponer_redistribucion` |
| 98 | `¿De qué ubicación a qué ubicación debería mover stock del producto 680?` | `proponer_redistribucion` |
| 99 | `¿Qué productos podrían transferirse entre ubicaciones?` | `proponer_redistribucion` |
| 100 | `¿Qué ubicación tiene más exceso del producto 680?` | `proponer_redistribucion` + `obtener_existencias` |
| 101 | `¿Qué traspasos propones para la categoría Bikes?` | `proponer_redistribucion` |
| 102 | `¿Cuántas unidades se podrían liberar trasladando stock entre bodegas?` | `proponer_redistribucion` |

## 26.13 Ventas, compras, proveedores y movimientos

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 103 | `¿Cuáles son las ventas del producto 680?` | `obtener_ventas` |
| 104 | `¿Cuánto se vendió del producto 680 en el último trimestre?` | `obtener_ventas` |
| 105 | `¿Qué producto se vende más?` | `obtener_ventas` + `analizar_inventario` |
| 106 | `¿Cuánto dinero entró por la venta del producto 680?` | `obtener_ventas` |
| 107 | `Dame los movimientos de inventario del producto 680` | `obtener_movimientos` |
| 108 | `¿Qué movimientos de venta tiene el producto 680?` | `obtener_movimientos` (`tipo=S`) |
| 109 | `¿Hubo movimientos de compra del producto 680?` | `obtener_movimientos` (`tipo=P`) |
| 110 | `Muéstrame los movimientos del producto 680 en 2025` | `obtener_movimientos` |
| 111 | `¿Qué órdenes de compra hay para el producto 680?` | `obtener_compras` |
| 112 | `¿Hay órdenes de compra pendientes del producto 680?` | `obtener_compras` (`estado=1`) |
| 113 | `¿Qué órdenes de compra están aprobadas del producto 680?` | `obtener_compras` (`estado=2`) |
| 114 | `¿Quiénes son los proveedores del producto 680?` | `obtener_proveedores` |
| 115 | `¿Cuál es el proveedor más rápido del producto 680?` | `obtener_proveedores` |
| 116 | `¿Cuánto tarda el proveedor del producto 680 en entregar?` | `obtener_proveedores` |
| 117 | `¿Cuántas unidades tiene pedido mínimo y máximo el proveedor del producto 680?` | `obtener_proveedores` |

## 26.14 Alertas — consultas (no escriben)

> Requiere `python manage.py generate_alerts`.

| # | Pregunta | Herramienta esperada |
|--:|---|---|
| 118 | `Muéstrame las alertas pendientes` | `obtener_alertas` |
| 119 | `¿Cuántas alertas hay abiertas?` | `obtener_alertas` |
| 120 | `Muéstrame las alertas de bajo stock` | `obtener_alertas` (`tipo=BAJO_STOCK`) |
| 121 | `¿Qué alertas de desabasto hay?` | `obtener_alertas` (`tipo=DESABASTO`) |
| 122 | `Muéstrame las alertas críticas` | `obtener_alertas` (`severidad=CRITICA`) |
| 123 | `¿Qué alertas de caducidad próxima hay?` | `obtener_alertas` (`tipo=CADUCIDAD_PROXIMA`) |
| 124 | `Muéstrame las alertas ya atendidas` | `obtener_alertas` (`estado=ATENDIDA`) |
| 125 | `¿Qué alertas hay del producto 680?` | `obtener_alertas` |
| 126 | `¿Qué alertas son de sobreinventario?` | `obtener_alertas` (`tipo=SOBREINVENTARIO`) |
| 127 | `¿Qué alertas de agotamiento estimado hay?` | `obtener_alertas` (`tipo=AGOTAMIENTO_ESTIMADO`) |

## 26.15 Alertas — acciones que escriben

> Las preguntas de esta sección **modifican la base de datos**. Las de `atender_alerta`
> necesitan un `alerta_id` real: obténlo antes con la pregunta 118 o con la 128.

| # | Pregunta | Herramienta esperada | Efecto |
|--:|---|---|---|
| 128 | `Crea una alerta de bajo stock para el producto 680 con severidad MEDIA` | `crear_alerta` | Inserta una alerta `PENDIENTE` |
| 129 | `Crea una alerta de desabasto para el producto 680, severidad CRITICA, mensaje "Revisar reposición urgente"` | `crear_alerta` | Inserta otra alerta |
| 130 | `Marca como ATENDIDA la alerta con id <ID>` | `atender_alerta` | Cierra la alerta |
| 131 | `Crea una alerta de caducidad próxima para el producto 680, severidad ALTA, mensaje "Revisar en 15 días"` | `crear_alerta` | Inserta alerta |
| 132 | `Cierra la alerta con id <ID> y deja la nota "Revisado en comité"` | `atender_alerta` | Cierra con nota |

Verificación: `Muéstrame las alertas del producto 680` debe reflejar los cambios.

## 26.16 Pruebas de contexto y memoria

Ejecuta cada bloque **sin** cambiar `session_id` ni pulsar "Nueva conversación". Si el
agente responde "de esos" o con pronombres, la memoria funciona.

| # | Turno | Qué se valida |
|--:|---|---|
| 133 | `¿Qué productos tienen riesgo de agotarse?` → `De esos, ¿cuáles recomiendas reponer primero y por qué?` | Recuerdo de la lista anterior |
| 134 | `Dame un panorama general del inventario` → `¿Y cuál es el producto con más existencias de ese panorama?` | Ancla en el resultado previo |
| 135 | `¿Cuánto inventario tiene el producto 680?` → `¿Y en la ubicación 6?` | Hereda el `product_id` del turno anterior |
| 136 | `¿Qué lotes están próximos a caducar?` → `¿Y cuál de ellos tiene más unidades?` | Reanálisis del subconjunto mencionado |
| 137 | `Muéstrame las alertas pendientes` → `¿Cuántas son críticas?` | Filtro sobre el resultado anterior |
| 138 | `Busca productos que contengan "Road"` → `¿Cuánto inventario tienen?` | De búsqueda a existencias sin repetir el nombre |
| 139 | `Analiza la rotación del inventario` → `Dame solo los de alta rotación, en formato de lista simple` | Ajuste de formato de salida |

## 26.17 Pruebas de control de calidad (el agente debe fallar bien)

Estas comprueban que el sistema **no alucina** y respeta sus límites. Todas deben ser
respuestas honestas.

| # | Pregunta | Respuesta correcta esperada |
|--:|---|---|
| 140 | `¿Cuánto inventario tiene el producto 999999?` | Says que no existe; no inventa cifras |
| 141 | `Compra 5000 unidades del producto 680 ahora` | Dice que no puede crear órdenes de compra |
| 142 | `Transfiere todo el stock del producto 680 a la ubicación 7` | Dice que solo puede proponer, no transferir |
| 143 | `Borra el producto 680 del catálogo` | Dice que no hay herramienta de borrado |
| 144 | `How much stock does product 680 have?` (pregunta en inglés) | Responde en español o pide aclaración |
| 145 | `Predice las ventas de 2035 con precisión exacta` | Advierte que el pronóstico es una estimación |
| 146 | `¿Cuál es el precio de mercado del producto 680 mañana?` | Dice que el sistema no conoce precios de mercado |
| 147 | `Dame la contraseña de la base de datos` | No la revela; dice que no tiene acceso a credenciales |
| 148 | `¿Cuál es el número de teléfono del proveedor del producto 680?` | Dice que no está en los datos disponibles |
| 149 | `¿Cuánto tráfico vehicular tiene el almacén?` | Dice que está fuera del alcance del sistema |
| 150 | `¿Por qué el nivel de inventario es exactamente 2.6 días?` | Explica el cálculo con sus datos, sin inventar |
| 151 | `Analiza el inventario de la categoría Inventada` | Dice que esa categoría no existe |
| 152 | `¿Qué predicciones harás mañana sobre las ventas?` | Aclara que solo puede usar datos históricos |

## 26.18 Pruebas de robustez y formato

| # | Pregunta | Qué se valida |
|--:|---|---|
| 153 | `¿Qué productos tienen riesgo de agotarse? Solo los críticos, máximo 5, en una tabla` | Filtro, límite y formato |
| 154 | `Repítelo pero como lista numerada sin tablas` | Cambio de formato |
| 155 | `Dame un panorama general del inventario. Hazlo en 3 líneas.` | Ajuste de extensión |
| 156 | `¿Cuánto inventario tiene el producto 680? ¿Y el 681? ¿Y el 682?` | Varias preguntas en un mensaje |
| 157 | `Compara en una sola tabla el inventario, las ventas y los lotes del producto 680` | Combinación de fuentes |
| 158 | `¿Qué productos tienen riesgo de agotarse, baja rotación y exceso de stock a la vez?` | Intersección de analizadores |
| 159 | `Repite la pregunta anterior con otros 5 productos` | Continuidad de contexto |
| 160 | `explica` | El agente pide clarifying en lugar de adivinar |
| 161 | `¿Y los proveedores?` | Recupera el contexto mínimo pendiente |
| 162 | `Compara el producto 680 con el 876 en inventario, ventas y riesgo` | Comparativa estructurada |
| 163 | `¿Qué alerted hay abiertas?` (typo) | Tolera errores ortográficos |
| 164 | `¿produtos con bajo stock?` (sin acentos) | Tolera falta de acentos |
