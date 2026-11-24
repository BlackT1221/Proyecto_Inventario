from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.database import obtener_bd
from models.factura import Factura as FacturaModel
from models.orden import Orden as OrdenModel
from models.mecanico import Mecanico as MecanicoModel
from models.repuesto import Repuesto as RepuestoModel
from models.orden_repuesto import OrdenRepuesto as OrdenRepuestoModel
from typing import Optional, List
from schemas.ordenes import OrdenCreate, OrdenPatch, OrdenResponse, AgregarRepuestoOrden, RepuestoEnOrdenResponse
from dependencias import verificar_api_key, parametros_paginacion
from sqlalchemy.orm import joinedload, selectinload

router = APIRouter(prefix="/ordenes", tags=["Gestionar ordenes"])

@router.get("/", response_model=List[OrdenResponse])
async def obtener_ordenes(
    estado: Optional[str] = None,
    paginacion: dict = Depends(parametros_paginacion), 
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(OrdenModel).options(joinedload(OrdenModel.mecanico))
    resultado = await db.execute(sentencia)
    ordenes = resultado.scalars().all() # Traer los objetos (No "lenguaje" sql)

    return ordenes

@router.get("/{orden_id}", response_model=OrdenResponse)
async def obtener_orden_por_id(
    orden_id: int,
    db: AsyncSession = Depends(obtener_bd)
):
    # SELECT * FROM ordenes WHERE id = orden_id
    sentencia = select(OrdenModel).options(joinedload(OrdenModel.mecanico)).where(OrdenModel.id == orden_id)
    resultado = await db.execute(sentencia)

    orden = resultado.scalar_one_or_none()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    return orden

@router.post("/", status_code=201)
async def crear_orden(
    orden: OrdenCreate,
    api_key: str = Depends(verificar_api_key), 
    db: AsyncSession = Depends(obtener_bd)
):

    consulta_mec = select(MecanicoModel).where(MecanicoModel.id == orden.mecanico_id)
    res_mec = await db.execute(consulta_mec)
    mecanico_db = res_mec.scalar_one_or_none()

    if not mecanico_db or not mecanico_db.activo:
        raise HTTPException(
            status_code=400,
            datail=f"El mecanico con el ID {orden.mecanico_id} no existe o está inactivo."
        )
    
    nueva_orden = OrdenModel(**orden.model_dump())

    db.add(nueva_orden)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error al guardar la base de datos")

    await db.refresh(nueva_orden)

    return {"mensaje": "Orden creada", "orden": nueva_orden}

@router.delete("/{placa}", status_code=204)
async def eliminar_orden(
    placa: str,
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(OrdenModel).where(OrdenModel.placa == placa)
    resultado = await db.execute(sentencia)
    orden = resultado.scalar_one_or_none()

    if not orden:
        raise HTTPException(status_code=404, detail="La orden no existe")

    await db.delete(orden)
    await db.commit()
    return None

@router.patch("/{placa}")
async def actualizacion_parcial(
    placa: str, 
    orden_patch: OrdenPatch,
    db: AsyncSession = Depends(obtener_bd)
):
    # SELECT * FROM ordenes WHERE placa == placa
    sentencia = select(OrdenModel).where(OrdenModel.placa == placa)
    resultado = await db.execute(sentencia)
    orden = resultado.scalar_one_or_none()

    if not orden:
        raise HTTPException(status_code=404, detail="La orden no existe")

    datos_a_actualizar = orden_patch.model_dump(exclude_unset=True)

    if "nuevo_estado" in datos_a_actualizar:
        datos_a_actualizar["estado"] = datos_a_actualizar.pop("nuevo_estado")

    for campo, valor in datos_a_actualizar.items():
        setattr(orden, campo, valor)

    try:
        await db.commit()
        await db.refresh(orden)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error aplicando la actualización parcial.")

    return {"mensaje": "La orden ha sido actualizada con éxito", "orden": orden}

@router.post("/{orden_id}/repuestos", status_code=201, response_model=RepuestoEnOrdenResponse)
async def agregar_repuesto_a_orden(
    orden_id: int,
    datos: AgregarRepuestoOrden,
    db: AsyncSession = Depends(obtener_bd)
):
    res_orden = await db.execute(select(OrdenModel).where(OrdenModel.id == orden_id))
    orden_db = res_orden.scalar_one_or_none()
    if not orden_db:
        raise HTTPException(status_code=404, detail="La orden de servicio no existe.")

    # CANDADO 3: Inmutabilidad de órdenes cerradas/facturadas
    if orden_db.estado.lower() == "reparada":
        raise HTTPException(
            status_code=400,
            detail="No se pueden agregar repuestos a una orden ya cerrada/facturada."
        )

    res_rep = await db.execute(select(RepuestoModel).where(RepuestoModel.id == datos.repuesto_id))
    repuesto_db = res_rep.scalar_one_or_none()
    if not repuesto_db:
        raise HTTPException(status_code=404, detail="El repuesto no existe en inventario.")

    if repuesto_db.stock_actual < datos.cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Disponible: {repuesto_db.stock_actual}, solicitado: {datos.cantidad}"
        )

    repuesto_db.stock_actual -= datos.cantidad
    orden_db.costo_reparacion += repuesto_db.precio_venta * datos.cantidad

    detalle = OrdenRepuestoModel(
        orden_id=orden_db.id,
        repuesto_id=repuesto_db.id,
        cantidad=datos.cantidad,
        precio_unitario_historico=repuesto_db.precio_venta
    )
    db.add(detalle)

    try:
        await db.commit()
        await db.refresh(detalle)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error procesando el movimiento de inventario.")

    return detalle


@router.patch("/{orden_id}", response_model=OrdenResponse)
async def actualizar_orden_parcial(
    orden_id: int,
    orden_patch: OrdenPatch,
    db: AsyncSession = Depends(obtener_bd)
):
    # Cargamos la orden junto con su mecánico y sus repuestos usados
    sentencia = (
        select(OrdenModel)
        .options(
            joinedload(OrdenModel.mecanico),
            selectinload(OrdenModel.repuestos_usados)
        )
        .where(OrdenModel.id == orden_id)
    )
    resultado = await db.execute(sentencia)
    orden_db = resultado.scalar_one_or_none()

    if not orden_db:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")

    # CANDADO 1: Idempotencia / Bloqueo si ya está cerrada
    if orden_db.estado.lower() == "reparada":
        raise HTTPException(
            status_code=400,
            detail="La orden ya se encuentra marcada como Reparada y posee una factura emitida."
        )

    datos_actualizar = orden_patch.model_dump(exclude_unset=True)
    mano_obra_enviada = datos_actualizar.pop("mano_obra", 0.0) or 0.0

    if "falla_reportada" in datos_actualizar:
        orden_db.falla_reportada = datos_actualizar["falla_reportada"]

    nuevo_estado = datos_actualizar.get("nuevo_estado")
    if nuevo_estado:
        nuevo_estado_norm = nuevo_estado.strip().capitalize()

        if nuevo_estado_norm == "Reparada":
            # Verificar en BD que no exista factura previa
            res_fact = await db.execute(
                select(FacturaModel).where(FacturaModel.orden_id == orden_db.id)
            )
            if res_fact.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Esta orden ya tiene una factura registrada.")

            # Cálculo de repuestos desde la tabla intermedia
            subtotal_repuestos = sum(
                item.cantidad * item.precio_unitario_historico
                for item in orden_db.repuestos_usados
            )

            # Sumamos la mano de obra al costo acumulado de la orden
            orden_db.costo_reparacion = subtotal_repuestos + mano_obra_enviada

            # CANDADO 2: No facturar órdenes en $0
            if orden_db.costo_reparacion <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="No se puede marcar como Reparada una orden con costo total en $0."
                )

            # CANDADO 4: Cálculo tributario (IVA 19%)
            total_neto = orden_db.costo_reparacion
            iva_calculado = round(total_neto * 0.19, 2)
            total_con_iva = round(total_neto + iva_calculado, 2)

            nueva_factura = FacturaModel(
                orden_id=orden_db.id,
                subtotal_repuestos=round(subtotal_repuestos, 2),
                costo_mano_obra=round(mano_obra_enviada, 2),
                iva=iva_calculado,
                total_pagar=total_con_iva
            )
            db.add(nueva_factura)

        orden_db.estado = nuevo_estado_norm

    try:
        # Commit atómico: actualiza la orden y crea la factura en una sola transacción
        await db.commit()
        await db.refresh(orden_db)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar la orden y generar la factura.")

    return orden_db