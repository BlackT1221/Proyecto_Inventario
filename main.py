from fastapi import FastAPI, Depends
from routers.ordenes import router as router_ordenes
from dependencias import simular_base_datos

app = FastAPI(
    title="API Recepción Taller Mecánico",
    description="Sistema de triaje y facturación",
    version="1.0"
)

app.include_router(router_ordenes)

@app.get("/prueba-yield")
async def probar_yield(conexion: str = Depends(simular_base_datos)):
    print("2. [RUTA] Ejecutando la ruta. Estado:", conexion)
    return {"mensaje": "Revisar consola."}