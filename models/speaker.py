from typing import List, Optional

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Speaker(Base):
    __tablename__ = "speakers"

    gll_file: Mapped[str] = mapped_column(String, primary_key=True)
    speaker_name: Mapped[str] = mapped_column(String, nullable=False)
    skip: Mapped[bool] = mapped_column(Boolean, default=False)

    # Optional physical properties
    sensitivity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    impedance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in kg
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in mm
    width: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in mm
    depth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in mm

    config_files: Mapped[List[str]] = relationship(
        "ConfigFile", back_populates="speaker", cascade="all, delete-orphan"
    )
