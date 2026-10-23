from fastapi import FastAPI, HTTPException, Request #importo mi framework
from database import leer_base_datos, obtener_producto, guardar_base_datos
from schemas import ProductoCreate

# Inicializar la aplicación
apiRest = FastAPI(
    title="API inventarios SENA",
    description="Mi primera API asíncrona",
    version="1.0.0"
)

# Nuestro primer endpoint
@apiRest.get("/") # Decorador -> Función que recibe como parámetro otra función
async def ruta_principal():
    return {"mensaje": "¡Bienvenido a mi primera API Rest!"}

@apiRest.get("/estado")
async def estado_servidor():
    return {"status": "En línea", "servicios": "Operativos sin ningun invonveniente"}

@apiRest.get("/productos")
async def listar_productos():
    datos = await leer_base_datos()
    return {"cantidad": len(datos), "productos": datos}

@apiRest.get("/productos/{codigo_producto}")
async def buscar_un_producto(codigo_producto: str):
    try:
        # Para llamar a la función de obtener producto
        producto = await obtener_producto(codigo_producto)
        return producto
    except KeyError:
        raise HTTPException(status_code=404, detail="El producto soliciato no existe en la BD.")

@apiRest.post("/productos", status_code=201)
async def registrar_nuevo_producto(producto: ProductoCreate):
    datos = await leer_base_datos()

    # 1. Validar que el producto no exista
    for dato in datos:
        if dato["codigo"] == producto.codigo:
            raise HTTPException(status_code=400, detail="El código de producto ya existe.")

    # 2. Convertir la clase a un diccionario
    nuevo_producto = producto.model_dump()

    # 3. Guardar
    datos.append(nuevo_producto)
    await guardar_base_datos(datos)

    return {"mensaje": "Producto registrado correctamente", "producto": nuevo_producto}

# Put, actulizar inventario
@apiRest.put("/productos/{codigo_producto}")
async def actulizar_producto(codigo_producto: str, producto_actualizado: ProductoCreate):
    datos = await leer_base_datos()
    for posicion, dato in enumerate(datos):
        if dato["codigo"] == codigo_producto:
            # Reemplazamos los datos manteniendo el codigo
            datos[posicion] = producto_actualizado.model_dump()
            datos[posicion]["codigo"] = codigo_producto

            await guardar_base_datos(datos)
            return {"mensaje": "Producto actualizado", "producto": datos[posicion]}
        
    raise HTTPException(status_code=404, detail="Producto no encontrado")