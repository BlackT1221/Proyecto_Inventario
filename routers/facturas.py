from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from core.database import obtener_bd
from models.factura import Factura as FacturaModel
from models.orden import Orden as OrdenModel
from models.orden_repuesto import OrdenRepuesto as OrdenRepuestoModel
from schemas.ordenes import FacturaDetalladaResponse

router = APIRouter(prefix="/facturas", tags=["Facturación"])

@router.get("/{orden_id}", response_model=FacturaDetalladaResponse)
async def obtener_factura_por_orden(
    orden_id: int,
    db: AsyncSession = Depends(obtener_bd)
):
    # Carga ansiosa multinivel: Factura -> Orden -> Mecánico y Repuestos -> Repuesto
    sentencia = (
        select(FacturaModel)
        .options(
            joinedload(FacturaModel.orden).joinedload(OrdenModel.mecanico),
            joinedload(FacturaModel.orden)
            .selectinload(OrdenModel.repuestos_usados)
            .joinedload(OrdenRepuestoModel.repuesto),
        )
        .where(FacturaModel.orden_id == orden_id)
    )
    resultado = await db.execute(sentencia)
    factura = resultado.scalar_one_or_none()

    if not factura:
        raise HTTPException(
            status_code=404,
            detail=f"No existe una factura emitida para la orden #{orden_id}."
        )

    return factura