from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import User, UserRole, Ticket, TicketStatus

async def auto_allocate_ticket(ticket: Ticket, db: AsyncSession) -> User | None:
    """
    Engine Logic:
    1. Scan for all active field staff workers.
    2. Count how many 'assigned' or 'open' tickets each worker currently has.
    3. Filter out overloaded workers (e.g., maximum 5 active tickets).
    4. Select the eligible worker with the lowest workload to balance the field force.
    """
    # Query to count active tickets per field worker
    workload_query = (
        select(
            User.id,
            func.count(Ticket.id).label("active_tickets")
        )
        .where(User.role == UserRole.field_staff)
        .outerjoin(Ticket, Ticket.assigned_to == User.id)
        # Filter for tickets that are not resolved yet
        .where((Ticket.status != TicketStatus.resolved) | (Ticket.id == None))
        .group_by(User.id)
        .order_by("active_tickets")
    )
    
    result = await db.execute(workload_query)
    worker_loads = result.all()
    
    if not worker_loads:
        return None  # No workers registered in system yet
        
    # Find the first worker who is under our threshold limit (e.g., 5 tasks max)
    target_worker_id = None
    for worker_id, active_tickets in worker_loads:
        if active_tickets < 5:
            target_worker_id = worker_id
            break
            
    if target_worker_id:
        # Fetch the complete worker object
        worker_result = await db.execute(select(User).where(User.id == target_worker_id))
        assigned_worker = worker_result.scalar_one()
        
        # Update the ticket state
        ticket.assigned_to = assigned_worker.id
        ticket.status = TicketStatus.assigned
        return assigned_worker
        
    return None  # All workers are currently overloaded; ticket stays 'open' in the queue