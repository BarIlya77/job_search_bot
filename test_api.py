#!/usr/bin/env python3
"""Тест API HH.ru"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.services.hh_client import HHAPIClient


async def test_api():
    async with HHAPIClient() as client:
        vacancies = await client.search_vacancies("python junior", per_page=2)
        print(f"Найдено вакансий: {len(vacancies)}")

        if vacancies:
            vac = vacancies[0]
            print(f"\nПервая вакансия:")
            print(f"ID: {vac.get('id')}")
            print(f"Название: {vac.get('name')}")
            print(f"Salary: {vac.get('salary')} (тип: {type(vac.get('salary'))})")
            print(f"Employer: {vac.get('employer')} (тип: {type(vac.get('employer'))})")
            print(f"Area: {vac.get('area')}")
            print(f"Experience: {vac.get('experience')}")
            print(f"Schedule: {vac.get('schedule')}")


if __name__ == "__main__":
    asyncio.run(test_api())