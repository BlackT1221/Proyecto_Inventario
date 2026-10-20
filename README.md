## Reto para los aprendices

La API ya cuenta con una estructura base funcional. En este laboratorio, deberán ampliar su funcionalidad agregando **tres nuevos endpoints HTTP de tipo `GET`** en el archivo `main.py`.

El objetivo es combinar conceptos básicos de programación en Python, manipulación de datos y desarrollo de APIs con **FastAPI**.

Los nuevos endpoints deberán trabajar directamente con la información almacenada en el archivo `inventario.json`.

---

## 1. Ruta de Categorías

Crear el siguiente endpoint:

```python
@app.get("/categorias")
```

### Requerimiento

La ruta debe:

1. Leer el archivo `inventario.json`.
2. Recorrer los productos registrados.
3. Extraer el valor del campo `categoria` de cada producto.
4. Eliminar las categorías duplicadas.
5. Devolver una lista con las categorías disponibles.

### Pista

Utilizar un `set` de Python para evitar elementos repetidos.

Ejemplo conceptual:

```python
categorias = set()
```

El resultado debe contener cada categoría una sola vez.

---

## 2. Ruta de Stock Crítico

Crear el siguiente endpoint:

```python
@app.get("/alertas/stock")
```

### Requerimiento

La ruta debe:

1. Leer el archivo `inventario.json`.
2. Revisar el stock de cada producto.
3. Identificar únicamente los productos cuyo stock sea **menor o igual a 3**.
4. Devolver una lista con los productos que cumplen esta condición.

La condición de filtrado debe ser equivalente a:

```python
stock <= 3
```

Los productos cuyo stock sea superior a `3` no deben aparecer en la respuesta.

---

## 3. Ruta de Búsqueda Avanzada

Crear el siguiente endpoint:

```python
@app.get("/productos/buscar/{palabra_clave}")
```

### Requerimiento

La ruta debe recibir una palabra clave directamente desde la URL y devolver todos los productos cuyo **nombre contenga dicha palabra clave**.

La búsqueda debe ser **insensible a mayúsculas y minúsculas**.

Por ejemplo, las siguientes búsquedas deberían comportarse de la misma manera:

```text
/productos/buscar/arroz
/productos/buscar/ARROZ
/productos/buscar/ArRoZ
```

### Pista

Utilizar el método `.lower()` para convertir tanto el nombre del producto como la palabra clave a minúsculas antes de realizar la comparación.

Conceptualmente:

```python
nombre.lower()
palabra_clave.lower()
```

La comprobación puede realizarse mediante una condición de pertenencia:

```python
palabra_clave.lower() in nombre.lower()
```

---

## Resumen de endpoints

| Método | Endpoint | Funcionalidad |
|---|---|---|
| `GET` | `/categorias` | Devuelve las categorías disponibles sin duplicados |
| `GET` | `/alertas/stock` | Devuelve productos con stock menor o igual a 3 |
| `GET` | `/productos/buscar/{palabra_clave}` | Busca productos por nombre sin distinguir mayúsculas/minúsculas |

## Criterios de implementación

La solución debe cumplir con los siguientes criterios:

- Los tres endpoints deben implementarse en `main.py`.
- Todos deben utilizar el método HTTP `GET`.
- La información debe obtenerse desde `inventario.json`.
- `/categorias` debe eliminar categorías duplicadas.
- `/alertas/stock` debe devolver únicamente productos con `stock <= 3`.
- `/productos/buscar/{palabra_clave}` debe realizar una búsqueda parcial por nombre.
- La búsqueda de productos debe ser independiente de mayúsculas y minúsculas.
- Las respuestas deben ser compatibles con el funcionamiento habitual de FastAPI.

## Objetivo de aprendizaje

Al finalizar el laboratorio, el aprendiz deberá ser capaz de:

- Crear rutas dinámicas utilizando FastAPI.
- Leer y procesar información almacenada en archivos JSON.
- Filtrar colecciones de datos mediante condiciones.
- Eliminar valores duplicados utilizando estructuras de datos de Python.
- Trabajar con parámetros dinámicos en las rutas.
- Implementar búsquedas de texto sin distinción entre mayúsculas y minúsculas.
- Integrar lógica básica de programación dentro de endpoints de una API.