from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.speaker import Base


class ConfigFile(Base):
    """Model for config files associated with speakers"""

    __tablename__ = "config_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    config_file: Mapped[str] = mapped_column(String)
    gll_file: Mapped[str] = mapped_column(ForeignKey("speakers.gll_file"))
    speaker: Mapped[str] = relationship("Speaker", back_populates="config_files")

    def __repr__(self):
        return f"<ConfigFile(file_path='{self.config_file}')>"
