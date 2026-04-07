# Guía: Esquema de Impresión — Plantas y Rangos de Paquetes

## ¿Qué es una "planta"?

En el sistema de impresión electoral, una **planta** es una línea de producción física donde se imprimen las tarjetas electorales. Cada kit (mesa de votación) queda asignado a una planta específica según el tipo de tarjeta y el tamaño del papel.

Las plantas activas en la base de datos son: `PL01`, `PL03`, `PL04`, `PL05`, `PL06`, `PL08`.

---

## Tabla central: `impresion.pub_ttarjetas_x_planta`

Es la tabla que relaciona cada kit con su planta de impresión.

```
pub_nkit      → número de kit (= div_nkit en ele_edivipol)
pub_cprefijo  → tipo de tarjeta (ej: '01' = Senado, '02' = Cámara)
pub_ctamano   → tamaño del papel (ej: '8.5 X 11', '11 X 17')
pub_cplanta   → planta asignada (ej: 'PL08')
```

**Ejemplo de registros:**
```
pub_nkit | pub_cprefijo | pub_ctamano | pub_cplanta
---------|--------------|-------------|------------
  16401  |     05       |  8.5 X 11   |    PL06
  16402  |     05       |  8.5 X 11   |    PL06
```

> No tiene llave primaria definida ni restricciones NOT NULL.

---

## Tabla de reportes: `configura.ele_preportes`

Define cada tipo de tarjeta/documento imprimible. Es el origen del dropdown **"Descripción del Reporte"** en la UI.

```
rep_norden       → ID del reporte (parámetro para las funciones SQL)
rep_ctitulo      → nombre visible (ej: 'TARJETA SENADO')
rep_cprefijo     → código de tarjeta (ej: '01')
rep_ccampo_ini   → campo de rango inicial en ele_edivipol (ej: 'div_nte_01_ini')
rep_ccampo_fin   → campo de rango final  en ele_edivipol (ej: 'div_nte_01_fin')
rep_ctipo        → tipo: 'RTC' = tarjetas con rango de paquete
rep_impreso      → 'S'/'N' — si aplica flujo de impresión
```

**Tarjetas principales:**

| rep_norden | rep_ctitulo               | rep_cprefijo |
|------------|---------------------------|--------------|
| 113        | TARJETA SENADO            | 01           |
| 114        | TARJETA CAMARA            | 02           |
| 115        | TARJETA SENADO INDIGENA   | 03           |
| 116        | TARJETA CAMARA INDIGENA   | 04           |
| 117        | TARJETA CAMARA AFRODESCENDIENTE | 05     |
| 126        | TARJETA SENADO [C]        | 30           |

---

## Las dos funciones SQL clave

### 1. `public.vst_rangos_te(nreporte, pstr_planta)`

**¿Qué hace?**
Genera los ítems del dropdown **"Rango Paq."** Toma todos los kits de una planta/tarjeta y los agrupa en lotes de **625**, produciendo etiquetas como `"626-1250=625"`.

**Parámetros:**
- `nreporte` → `rep_norden` de `configura.ele_preportes`
- `pstr_planta` → código de planta (ej: `'PL08'`). Si se pasa vacío `''`, devuelve todos los kits sin filtrar por planta.

**Retorna:**
```
div_nkit   → número del último kit del lote (usado como ID del rango)
cadena     → lista de kit numbers separados por coma del lote
rango      → etiqueta legible: 'paq_ini-paq_fin=cantidad' (ej: '626-1250=625')
sentencia  → SQL interno generado dinámicamente (para debug)
```

**Lógica interna:**
1. Consulta `configura.ele_preportes` para obtener el `rep_cprefijo` del reporte.
2. Une `ele_edivipol` con `pub_ttarjetas_x_planta` filtrando por prefijo y planta.
3. Ordena los kits por número de paquete (`div_nte_XX_paq`).
4. Cada 625 kits, emite una fila con el rango correspondiente.

> **Importante:** los números en `rango` (ej: `626-1250`) son **números de paquete**, no de kit.

---

### 2. `impresion.fn_rango_kitsxpaquete(num_reporte, planta)`

**¿Qué hace?**
Devuelve los kits individuales (panel derecho de la UI) para un rango de paquete seleccionado.

**Parámetros:**
- `num_reporte` → mismo `rep_norden`
- `planta` → mismo código de planta

**Retorna:**
```
div_nkit      → número de kit
rango         → etiqueta del lote al que pertenece (ej: '626-1250=625')
rango_inicio  → primer div_nkit del bloque consecutivo
rango_fin     → último div_nkit del bloque consecutivo
```

**Lógica interna:**
1. Llama internamente a `vst_rangos_te` para obtener la `cadena` de kits por rango.
2. Descompone la cadena con `unnest(string_to_array(cadena, ','))`.
3. Agrupa los kits consecutivos usando `LAG()` y `SUM()` acumulado.
4. Retorna los bloques de kits consecutivos con su rango de inicio y fin.

> La función puede devolver **múltiples filas por rango** si los kits no son todos consecutivos.

---

## Flujo completo de la UI

```
Usuario selecciona tarjeta
        ↓
  configura.ele_preportes
  (rep_norden, rep_cprefijo)
        ↓
Usuario selecciona planta
        ↓
  impresion.pub_ttarjetas_x_planta
  (plantas disponibles para ese prefijo)
        ↓
Se puebla dropdown "Rango Paq."
        ↓
  vst_rangos_te(nreporte, planta)
  → devuelve ítems tipo '626-1250=625'
        ↓
Usuario selecciona un rango
        ↓
Se puebla panel derecho (lista de kits)
        ↓
  fn_rango_kitsxpaquete(nreporte, planta)
  filtrado por rango = '626-1250=625'
```

---

## Consultas para replicar el ejemplo

**Ejemplo:** TARJETA SENADO (`nreporte=113`), planta `PL08`, rango `626-1250`.

> **Nota sobre `search_path`:** Las funciones referencian `pub_ttarjetas_x_planta` sin schema. Si la conexión no tiene `impresion` en el `search_path`, hay que forzarlo en la misma query con `set_config`.

### Consulta 1 — Poblar dropdown "Rango Paq."

```sql
SELECT r.div_nkit, r.rango, r.cadena
FROM (SELECT set_config('search_path', 'public,impresion', true)) cfg,
     LATERAL (
         SELECT * FROM public.vst_rangos_te(113, 'PL08')
         ORDER BY div_nkit
     ) r;
```

**Resultado esperado (extracto):**
```
div_nkit |     rango      | cadena
---------|----------------|--------
   625   | 1-625=625      | 1,2,3,...,625
  1250   | 626-1250=625   | 626,627,...,1250
  1875   | 1251-1875=625  | 1251,...,1875
  ...
```

### Consulta 2 — Listar kits del rango seleccionado (panel derecho)

```sql
SELECT r.div_nkit, r.rango, r.rango_inicio, r.rango_fin
FROM (SELECT set_config('search_path', 'public,impresion', true)) cfg,
     LATERAL (
         SELECT * FROM impresion.fn_rango_kitsxpaquete(113, 'PL08')
         WHERE rango = '626-1250=625'
     ) r
ORDER BY r.rango_inicio;
```

**Resultado esperado:**
```
div_nkit |     rango     | rango_inicio | rango_fin
---------|---------------|--------------|----------
  1250   | 626-1250=625  |     342      |    661
  1250   | 626-1250=625  |     662      |    662
```

> Los kits del rango 626-1250 (de paquetes) se corresponden con los `div_nkit` 342 a 662. Aparecen en dos filas porque hubo un salto en la numeración consecutiva de kits.

---

## Tabla de parámetros rápida

| Elemento UI               | Parámetro SQL  | Valor ejemplo | Fuente                          |
|---------------------------|----------------|---------------|---------------------------------|
| Descripción del Reporte   | `nreporte`     | `113`         | `configura.ele_preportes.rep_norden` |
| Planta                    | `planta`       | `'PL08'`      | `impresion.pub_ttarjetas_x_planta.pub_cplanta` |
| Rango Paq. (dropdown)     | `rango`        | `'626-1250=625'` | Resultado de `vst_rangos_te`  |

---

## Consideraciones técnicas

- **Tamaño de lote fijo:** siempre 625 kits por rango. El último lote puede tener menos.
- **Columnas dinámicas:** la función construye el SQL internamente según el prefijo. Para prefijo `01` usa `div_nte_01_paq` y `div_va_te_01`; para prefijo `02`, `div_nte_02_paq` y `div_va_te_02`, etc.
- **LEFT JOIN en vistas:** las vistas `vst_rel_te_01` al `vst_rel_te_07` hacen LEFT JOIN con `pub_ttarjetas_x_planta`, por lo que un kit puede tener `pub_cplanta = NULL` si no tiene planta asignada.
- **search_path:** la conexión a la BD debe incluir el schema `impresion` o usar el truco `set_config` mostrado arriba.
