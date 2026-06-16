"""add wishlist fields and faq

Revision ID: 003
Revises: 002
Create Date: 2026-05-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expand inquiry_source enum
    op.execute("ALTER TYPE inquiry_source ADD VALUE IF NOT EXISTS 'referral';")
    op.execute("ALTER TYPE inquiry_source ADD VALUE IF NOT EXISTS 'website';")

    # Room additions
    op.add_column("rooms", sa.Column("display_room_number", sa.String(20)))
    op.add_column("rooms", sa.Column("property_code", sa.String(10), nullable=False, server_default="DT01"))
    bed_type_enum = sa.Enum("lower_bunk", "upper_bunk", "loft_type", name="bed_type")
    bed_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("rooms", sa.Column("bed_type", bed_type_enum))

    # Resident additions
    op.add_column("residents", sa.Column("address", sa.Text))
    op.add_column("residents", sa.Column("school", sa.String(255)))
    op.add_column("residents", sa.Column("course", sa.String(255)))
    op.add_column("residents", sa.Column("review_center", sa.String(255)))
    op.add_column("residents", sa.Column("exam_date", sa.Date))
    op.add_column("residents", sa.Column("is_first_time_dormer", sa.Boolean, server_default="true"))

    # Inquiry additions
    op.add_column("inquiries", sa.Column("property_code", sa.String(10), server_default="DT01"))
    op.add_column("inquiries", sa.Column("prospect_name", sa.String(255)))
    op.add_column("inquiries", sa.Column("prospect_phone", sa.String(20)))
    op.add_column("inquiries", sa.Column("prospect_email", sa.String(255)))
    op.add_column("inquiries", sa.Column("school", sa.String(255)))
    op.add_column("inquiries", sa.Column("course", sa.String(255)))
    op.add_column("inquiries", sa.Column("review_center", sa.String(255)))
    op.add_column("inquiries", sa.Column("exam_date", sa.Date))
    op.add_column("inquiries", sa.Column("first_time_dormer", sa.Boolean, server_default="true"))
    op.add_column("inquiries", sa.Column("previous_dorm", sa.String(255)))
    op.add_column("inquiries", sa.Column("desired_move_in_date", sa.Date))
    op.add_column("inquiries", sa.Column("length_of_stay", sa.String(50)))
    op.add_column("inquiries", sa.Column("inquiry_form_data", sa.JSON))

    # Announcement additions
    op.add_column("announcements", sa.Column("target_property", sa.String(10)))
    op.add_column("announcements", sa.Column("target_room_numbers", sa.JSON))
    op.add_column("announcements", sa.Column("target_bed_types", sa.JSON))

    # FAQ table
    op.create_table(
        "faqs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), server_default="general"),
        sa.Column("order_index", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("faqs")

    op.drop_column("announcements", "target_property")
    op.drop_column("announcements", "target_room_numbers")
    op.drop_column("announcements", "target_bed_types")

    op.drop_column("inquiries", "property_code")
    op.drop_column("inquiries", "prospect_name")
    op.drop_column("inquiries", "prospect_phone")
    op.drop_column("inquiries", "prospect_email")
    op.drop_column("inquiries", "school")
    op.drop_column("inquiries", "course")
    op.drop_column("inquiries", "review_center")
    op.drop_column("inquiries", "exam_date")
    op.drop_column("inquiries", "first_time_dormer")
    op.drop_column("inquiries", "previous_dorm")
    op.drop_column("inquiries", "desired_move_in_date")
    op.drop_column("inquiries", "length_of_stay")
    op.drop_column("inquiries", "inquiry_form_data")

    op.drop_column("residents", "address")
    op.drop_column("residents", "school")
    op.drop_column("residents", "course")
    op.drop_column("residents", "review_center")
    op.drop_column("residents", "exam_date")
    op.drop_column("residents", "is_first_time_dormer")

    op.drop_column("rooms", "display_room_number")
    op.drop_column("rooms", "property_code")
    op.drop_column("rooms", "bed_type")
    sa.Enum(name="bed_type").drop(op.get_bind(), checkfirst=True)
