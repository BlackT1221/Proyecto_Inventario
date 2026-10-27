from fastapi import FastAPI, HTTPException
from schemas import OrdenCreate, OrdenPatch, OrdenUpdate
from database import leer_base_datos, guardar_base_datos

app = FastAPI(
    title="API Recepción Taller Mecánico",
    description="Sistema de triaje y facturación",
    version="1.0"
)

@app.post("/ordenes", status_code=201)
async def crear_orden(orden: OrdenCreate):
    datos = await leer_base_datos()
    
    # Regla de Negocio: Validar que la placa no esté ya en el taller
    for item in datos:
        if item["placa"] == orden.placa and item["estado"] != "Entregada":
            raise HTTPException(
                status_code=400, 
                detail=f"La moto con placa {orden.placa} ya se encuentra en el taller ({item['estado']})."
            )
            
    nueva_orden = orden.model_dump()
    nueva_orden["estado"] = "En diagnóstico"
    nueva_orden["costo_reparacion"] = 0.0
    
    datos.append(nueva_orden)
    await guardar_base_datos(datos)
    
    return {"mensaje": "Orden creada exitosamente", "orden": nueva_orden}

@app.get("/ordenes")
async def obtener_ordenes():
    datos = await leer_base_datos()
    return {"total_ordenes": len(datos), "ordenes": datos}

@app.put("/ordenes/{placa}")
async def actualizar_orden(placa: str, orden_update: OrdenUpdate):
        
    datos = await leer_base_datos()
    
    for i, item in enumerate(datos):
        if item["placa"] == placa:
            
            datos[i]["estado"] = orden_update.nuevo_estado
            datos[i]["costo_reparacion"] = orden_update.costo_reparacion
            
            await guardar_base_datos(datos)
            return {"mensaje": "Orden actualizada correctamente", "orden": datos[i]}
            
    raise HTTPException(status_code=404, detail="Orden no encontrada")

@app.delete("/ordenes/{placa}", status_code=204)
async def eliminar_orden(placa: str):
    datos = await leer_base_datos()

    # for orden in datos:
    #     if orden["placa"] != placa:
    #         datos_filtrados.append(orden)

    datos_filtrados = [orden for orden in datos if orden["placa"] != placa]

    if len(datos) == len(datos_filtrados):
        raise HTTPException(status_code=404, detail="La orden no existe.")

    await guardar_base_datos(datos_filtrados)

    return None

@app.patch("/ordenes/{placa}")
async def actualizacion_parcial(placa: str, orden_patch: OrdenPatch):
    datos = await leer_base_datos()

    for i, orden in enumerate(datos):
        if orden["placa"] == placa:
            datos_a_actualizar = orden_patch.model_dump(exclude_unset=True)

            # Actualizamos solo con los datos que llegaron
            datos[i].update(datos_a_actualizar)

            await guardar_base_datos(datos)
            return {"mesaje": "La orden ha sido actualizada con los siguientes datos", "orden": datos[i]}

    raise HTTPException(status_code=404, detail="La orden no existe.")