from typing import List
from sqlalchemy import String, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Speaker(Base):
    __tablename__ = "speakers"

    gll_file: Mapped[str] = mapped_column(String, primary_key=True)
    speaker_name: Mapped[str] = mapped_column(String, nullable=False)
    skip: Mapped[bool] = mapped_column(Boolean, default=False)
    config_files: Mapped[List["ConfigFile"]] = relationship(
        "ConfigFile", back_populates="speaker", cascade="all, delete-orphan"
    )
