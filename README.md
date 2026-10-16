# Instrucciones para los aprendices:

## La Tarea de Alerta (Segundo Plano): 
En su archivo database.py, creen primero una corrutina llamada alerta_stock_bajo(codigo, nombre, stock_actual). Esta función debe simular el envío de un correo al administrador (usando await asyncio.sleep(2)) e imprimir en consola de forma llamativa: 
```
"⚠️ ALERTA CRÍTICA: El producto {nombre} ({codigo}) ha bajado a {stock_actual} unidades. Solicitar restock inmediato."
```

## La Lógica de Venta: 
Creen una corrutina principal llamada vender_producto(codigo, cantidad_vendida). Esta función debe realizar el siguiente flujo asíncrono:

* Búsqueda: Buscar el producto en el JSON. Si no existe, lanzar un KeyError ("Producto no encontrado").

* Validación: Verificar el stock. Si la cantidad_vendida es mayor al stock actual, lanzar un ValueError ("Stock insuficiente").

* Actualización: Restar la cantidad vendida del stock y guardar los cambios en el archivo JSON.

* Disparador de Alerta (Lo nuevo): Evaluar si el stock resultante es menor a 3. De ser así, lanzar la corrutina alerta_stock_bajo utilizando asyncio.create_task() para que el administrador sea notificado en segundo plano sin hacer que el cliente espere en la caja.

* Retorno: Devolver un diccionario o string con el resumen de la venta exitosa.

## Prueba de Estrés (En main.py): 
Creen una simulación usando asyncio.gather() donde intenten procesar 4 ventas simultáneas utilizando bloques try/except para atrapar los errores sin que el programa colapse. Su simulación debe forzar obligatoriamente estos tres escenarios:

* Una venta exitosa normal que deje buen stock.

* Una venta que deje el stock en 2 o menos (para comprobar que la alerta en segundo plano se dispara correctamente sin bloquear la respuesta de la venta).

* Una venta fallida que pida más unidades de las que existen (para comprobar que el ValueError es atrapado).