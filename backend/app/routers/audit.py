"""
Audit endpoints used by the frontend
Provides:
- GET /api/audit/logs
- GET /api/audit/blockchain
- GET /api/audit/export

Requires admin authentication (auditor or above)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from datetime import datetime
from typing import Optional
import csv
import io
import structlog

from app.database import get_db
from app.middleware.auth import get_current_admin, require_role
from app.models.admin import AdminRole
from app.models.audit import AuditLog, BlockchainTransaction
from app.models.voter import AuthAttempt, Voter

logger = structlog.get_logger()

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/logs")
async def get_audit_logs(
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    voterId: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin = Depends(require_role(AdminRole.AUDITOR, AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN))
):
    """Return authentication attempt logs with filters and pagination (frontend expects 1-indexed pages)"""
    try:
        # Use raw SQL to avoid enum conversion issues
        from sqlalchemy import text

        # Build the base query
        sql_query = """
            SELECT
                a.id,
                v.voter_id,
                a.auth_method,
                a.outcome,
                a.attempted_at,
                a.ip_address,
                a.failure_reason,
                a.similarity_score
            FROM auth_attempts a
            LEFT JOIN voters v ON a.voter_id = v.id
            WHERE 1=1
        """
        params = {}

        # Date range filters
        if startDate:
            try:
                start_dt = datetime.fromisoformat(startDate)
                sql_query += " AND a.attempted_at >= :start_date"
                params['start_date'] = start_dt
            except Exception:
                pass

        if endDate:
            try:
                end_dt = datetime.fromisoformat(endDate)
                sql_query += " AND a.attempted_at <= :end_date"
                params['end_date'] = end_dt
            except Exception:
                pass

        # Filter by voter_id
        if voterId:
            sql_query += " AND v.voter_id = :voter_id"
            params['voter_id'] = voterId

        # Filter by outcome
        if outcome:
            sql_query += " AND a.outcome = :outcome"
            params['outcome'] = outcome

        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM ({sql_query}) as subquery"
        total_result = db.execute(text(count_query), params).fetchone()
        total = total_result[0] if total_result else 0

        # Add ordering and pagination
        sql_query += " ORDER BY a.attempted_at DESC"
        offset = (page - 1) * limit
        sql_query += f" OFFSET {offset} LIMIT {limit}"

        # Execute query
        result = db.execute(text(sql_query), params)
        rows = result.fetchall()

        # Format response
        results = [
            {
                "id": str(row[0]),
                "voter_id": row[1],
                "method": row[2],
                "outcome": row[3],
                "timestamp": row[4].isoformat() if row[4] else None,
                "ip_address": str(row[5]) if row[5] else None,
                "failure_reason": row[6],
                "similarity_score": float(row[7]) if row[7] else None
            }
            for row in rows
        ]

        return {"total": total, "page": page, "limit": limit, "logs": results}

    except Exception as e:
        logger.error("get_audit_logs_failed", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve authentication logs: {str(e)}")


@router.get("/blockchain")
async def get_blockchain_transactions(
    voterId: Optional[str] = Query(None),
    txHash: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin = Depends(require_role(AdminRole.AUDITOR, AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN))
):
    """Return blockchain transaction logs (frontend expects 1-indexed pages)"""
    try:
        query = db.query(BlockchainTransaction)

        if txHash:
            query = query.filter(BlockchainTransaction.tx_hash == txHash)

        # voterId filter may not directly map to tx; leave as future enhancement

        total = query.count()

        # Convert 1-indexed page to 0-indexed offset
        offset = (page - 1) * limit
        txs = query.order_by(BlockchainTransaction.recorded_at.desc()).offset(offset).limit(limit).all()

        results = [
            {
                "id": str(t.id),
                "election_id": str(t.election_id) if t.election_id else None,
                "tx_type": t.tx_type,
                "tx_hash": t.tx_hash,
                "block_number": t.block_number,
                "from_address": t.from_address,
                "to_address": t.to_address,
                "gas_used": t.gas_used,
                "status": t.status,
                "timestamp": t.recorded_at.isoformat() if t.recorded_at else None,
                "voter_id": t.raw_event.get("voter_id") if t.raw_event else None,
                "recorded_at": t.recorded_at.isoformat() if t.recorded_at else None
            }
            for t in txs
        ]

        return {"total": total, "page": page, "limit": limit, "transactions": results}

    except Exception as e:
        logger.error("get_blockchain_transactions_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve blockchain transactions")


@router.get("/export")
async def export_audit_logs(
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    voterId: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(require_role(AdminRole.AUDITOR, AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN))
):
    """Export audit logs as CSV"""
    try:
        query = db.query(AuditLog)

        if startDate:
            try:
                start_dt = datetime.fromisoformat(startDate)
                query = query.filter(AuditLog.occurred_at >= start_dt)
            except Exception:
                pass
        if endDate:
            try:
                end_dt = datetime.fromisoformat(endDate)
                query = query.filter(AuditLog.occurred_at <= end_dt)
            except Exception:
                pass
        if voterId:
            try:
                import uuid as _uuid
                query = query.filter(or_(AuditLog.target_id == _uuid.UUID(voterId), AuditLog.details["voter_id"].astext == voterId))
            except Exception:
                query = query.filter(AuditLog.details["voter_id"].astext == voterId)
        if outcome:
            query = query.filter(AuditLog.action == outcome)

        logs = query.order_by(AuditLog.occurred_at.desc()).all()

        # Build CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "admin_id", "action", "target_table", "target_id", "details", "ip_address", "occurred_at"])
        for l in logs:
            writer.writerow([
                str(l.id),
                str(l.admin_id) if l.admin_id else "",
                l.action,
                l.target_table or "",
                str(l.target_id) if l.target_id else "",
                str(l.details) if l.details else "",
                str(l.ip_address) if l.ip_address else "",
                l.occurred_at.isoformat() if l.occurred_at else ""
            ])

        response = Response(content=output.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=audit_logs.csv"
        return response

    except Exception as e:
        logger.error("export_audit_logs_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to export audit logs")
