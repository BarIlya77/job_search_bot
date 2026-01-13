from sqlalchemy import Column, BigInteger, String, Text, Boolean, JSON, DateTime, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    telegram_id = Column(BigInteger, primary_key=True)
    first_name = Column(String(100), nullable=False)
    username = Column(String(100))
    # search_filters = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    # Связь с вакансиями
    vacancies = relationship("UserVacancy", back_populates="user")

    def __repr__(self):
        return f"<User {self.telegram_id}: {self.first_name}>"


class UserFilter(Base):
    __tablename__ = 'user_filters'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False)
    filter_name = Column(String(50), nullable=False)  # 'profession', 'salary', 'experience'
    filter_value = Column(JSON)  # Храним значения как JSON
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (Index('idx_user_filter', 'telegram_id', 'filter_name'),)

    def __repr__(self):
        return f"<UserFilter {self.telegram_id}:{self.filter_name}={self.filter_value}>"


class Vacancy(Base):
    __tablename__ = 'vacancies'

    hh_id = Column(String(50), primary_key=True)  # ID с HH.ru
    title = Column(String(500), nullable=False)
    employer_name = Column(String(500))
    salary_from = Column(Integer)
    salary_to = Column(Integer)
    salary_currency = Column(String(10))
    area = Column(String(100))
    experience = Column(String(50))
    schedule = Column(String(50))
    url = Column(String(500), unique=True, nullable=False)
    raw_data = Column(JSON)  # Все данные от API
    published_at = Column(DateTime)  # Когда опубликована на HH
    fetched_at = Column(DateTime, default=func.now())  # Когда мы получили

    # Связь с пользователями
    users = relationship("UserVacancy", back_populates="vacancy")

    def __repr__(self):
        return f"<Vacancy {self.hh_id}: {self.title[:30]}...>"


class UserVacancy(Base):
    """Связь пользователь-вакансия (многие-ко-многим)"""
    __tablename__ = 'user_vacancies'

    user_id = Column(BigInteger, ForeignKey('users.telegram_id'), primary_key=True)
    vacancy_id = Column(String(50), ForeignKey('vacancies.hh_id'), primary_key=True)
    notified = Column(Boolean, default=False)  # Отправлено уведомление?
    cover_sent = Column(Boolean, default=False)  # Отправлено сопроводительное?
    interested = Column(Boolean, default=True)  # Пользователь заинтересован?
    created_at = Column(DateTime, default=func.now())

    # Связи
    user = relationship("User", back_populates="vacancies")
    vacancy = relationship("Vacancy", back_populates="users")

    def __repr__(self):
        return f"<UserVacancy user:{self.user_id} vacancy:{self.vacancy_id}>"
