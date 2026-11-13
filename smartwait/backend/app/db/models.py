"""
SmartWait database models (SQLAlchemy 2.0 style).

Tables:
  users, students, staff, services, counters, queue_tokens, queue_events,
  visit_plans, visit_items, staff_assignments, predictions, feedback, notifications
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------- Enumerations ----------

class Role(str, enum.Enum):
    student = "student"
    staff = "staff"
    admin = "admin"


class CounterStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    closed = "closed"


class TokenStatus(str, enum.Enum):
    waiting = "waiting"
    called = "called"
    serving = "serving"
    completed = "completed"
    skipped = "skipped"
    cancelled = "cancelled"


class EventType(str, enum.Enum):
    joined = "joined"
    called = "called"
    recalled = "recalled"
    skipped = "skipped"
    served = "served"
    completed = "completed"
    cancelled = "cancelled"
    counter_paused = "counter_paused"
    counter_resumed = "counter_resumed"


class PlanStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class ItemStatus(str, enum.Enum):
    pending = "pending"
    queued = "queued"
    in_service = "in_service"
    done = "done"
    skipped = "skipped"


class NotificationChannel(str, enum.Enum):
    in_app = "in_app"
    push = "push"


# ---------- Identity ----------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    student: Mapped["Student | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    staff: Mapped["Staff | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    roll_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))
    # Authorised priority category (e.g. "general", "senior_citizen", "pwd"); verified by admin.
    priority_category: Mapped[str] = mapped_column(String(40), default="general", nullable=False)
    # Attendance history used by the no-show model (updated by the queue engine).
    turns_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    turns_missed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped[User] = relationship(back_populates="student")
    tokens: Mapped[list["QueueToken"]] = relationship(back_populates="student")
    plans: Mapped[list["VisitPlan"]] = relationship(back_populates="student")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="student")


class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    designation: Mapped[str | None] = mapped_column(String(100))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped[User] = relationship(back_populates="staff")
    assignments: Mapped[list["StaffAssignment"]] = relationship(back_populates="staff")


# ---------- Services & counters ----------

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Typical time to serve one student, in minutes. Used as the prior before ML data exists.
    avg_duration_min: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    counters: Mapped[list["Counter"]] = relationship(back_populates="service")
    tokens: Mapped[list["QueueToken"]] = relationship(back_populates="service")

    __table_args__ = (CheckConstraint("avg_duration_min > 0", name="ck_service_duration_positive"),)


class ServiceDependency(Base):
    """Directed edge: `service_id` must be completed before `prerequisite_id`.
    Example: Fee Payment -> Bonafide Certificate. Used by the visit optimizer's DAG."""
    __tablename__ = "service_dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    prerequisite_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("service_id", "prerequisite_id", name="uq_dependency_pair"),
        CheckConstraint("service_id <> prerequisite_id", name="ck_no_self_dependency"),
    )


class Counter(Base):
    __tablename__ = "counters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g. "FEE-1"
    location: Mapped[str | None] = mapped_column(String(120))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[CounterStatus] = mapped_column(
        Enum(CounterStatus, name="counter_status"), default=CounterStatus.active, nullable=False
    )

    service: Mapped[Service] = relationship(back_populates="counters")
    tokens: Mapped[list["QueueToken"]] = relationship(back_populates="counter")
    assignments: Mapped[list["StaffAssignment"]] = relationship(back_populates="counter")


class StaffAssignment(Base):
    __tablename__ = "staff_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    counter_id: Mapped[int] = mapped_column(ForeignKey("counters.id", ondelete="CASCADE"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime)

    staff: Mapped[Staff] = relationship(back_populates="assignments")
    counter: Mapped[Counter] = relationship(back_populates="assignments")

    __table_args__ = (
        CheckConstraint("ends_at IS NULL OR ends_at > starts_at", name="ck_assignment_time_order"),
    )


# ---------- Queue ----------

class QueueToken(Base):
    __tablename__ = "queue_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g. "FEE-042"
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="RESTRICT"), nullable=False)
    counter_id: Mapped[int | None] = mapped_column(ForeignKey("counters.id", ondelete="SET NULL"))
    plan_item_id: Mapped[int | None] = mapped_column(ForeignKey("visit_items.id", ondelete="SET NULL"))
    status: Mapped[TokenStatus] = mapped_column(
        Enum(TokenStatus, name="token_status"), default=TokenStatus.waiting, nullable=False
    )
    priority_rank: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    called_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    student: Mapped[Student] = relationship(back_populates="tokens")
    service: Mapped[Service] = relationship(back_populates="tokens")
    counter: Mapped[Counter | None] = relationship(back_populates="tokens")
    plan_item: Mapped["VisitItem | None"] = relationship(back_populates="token")
    events: Mapped[list["QueueEvent"]] = relationship(back_populates="token", cascade="all, delete-orphan")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="token")

    __table_args__ = (
        CheckConstraint(
            "completed_at IS NULL OR called_at IS NULL OR completed_at >= called_at",
            name="ck_token_time_order",
        ),
    )


class QueueEvent(Base):
    """Append-only history of every queue state change. Source of ML training data and analytics."""
    __tablename__ = "queue_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_id: Mapped[int] = mapped_column(ForeignKey("queue_tokens.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType, name="event_type"), nullable=False)
    # Snapshot of the queue at the moment of the event (used as ML features).
    queue_length_at_event: Mapped[int] = mapped_column(Integer, nullable=False)
    active_counters_at_event: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, index=True)

    token: Mapped[QueueToken] = relationship(back_populates="events")


# ---------- Multi-service visit optimizer ----------

class VisitPlan(Base):
    __tablename__ = "visit_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[PlanStatus] = mapped_column(Enum(PlanStatus, name="plan_status"), default=PlanStatus.draft, nullable=False)
    recommended_arrival: Mapped[datetime | None] = mapped_column(DateTime)
    estimated_total_min: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    student: Mapped[Student] = relationship(back_populates="plans")
    items: Mapped[list["VisitItem"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="VisitItem.sequence_no"
    )


class VisitItem(Base):
    __tablename__ = "visit_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("visit_plans.id", ondelete="CASCADE"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="RESTRICT"), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus, name="item_status"), default=ItemStatus.pending, nullable=False)

    plan: Mapped[VisitPlan] = relationship(back_populates="items")
    service: Mapped[Service] = relationship()
    token: Mapped[QueueToken | None] = relationship(back_populates="plan_item", uselist=False)

    __table_args__ = (
        UniqueConstraint("plan_id", "service_id", name="uq_plan_service"),
        UniqueConstraint("plan_id", "sequence_no", name="uq_plan_sequence"),
        CheckConstraint("sequence_no > 0", name="ck_sequence_positive"),
    )


# ---------- ML, feedback, notifications ----------

class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_id: Mapped[int] = mapped_column(ForeignKey("queue_tokens.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(60), nullable=False)  # e.g. "random_forest_v1"
    kind: Mapped[str] = mapped_column(String(30), nullable=False)        # "wait_time" | "no_show"
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    range_low: Mapped[float | None] = mapped_column(Float)
    range_high: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    token: Mapped[QueueToken] = relationship(back_populates="predictions")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    token_id: Mapped[int | None] = mapped_column(ForeignKey("queue_tokens.id", ondelete="SET NULL"))
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    student: Mapped[Student] = relationship(back_populates="feedback")

    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="ck_rating_range"),)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel"), default=NotificationChannel.in_app, nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
