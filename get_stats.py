from datetime import datetime, timedelta
from amocrm.v2 import tokens, Lead

from config import CLIENT_ID, CLIENT_SECRET, SUBDOMAIN, REDIRECT_URL, CODE


async def calculate_manager_stats():
    """
    Рассчитывает статистику по сделкам для менеджеров.

    :return: Словарь со статистикой сделок по менеджерам.
    """

    tokens.default_token_manager(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        subdomain=SUBDOMAIN,
        redirect_url=REDIRECT_URL,
        storage=tokens.FileTokensStorage(),
    )

    # tokens.default_token_manager.init(code=CODE, skip_error=False)

    leads = Lead.objects.all()
    manager_stats = {}

    # Определяем момент ровно сутки назад от настоящего времени
    now = datetime.now()
    one_day_ago = now - timedelta(days=1)

    # Определяем начало текущей недели (понедельник)
    current_week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    print(current_week_start)

    # Определяем начало текущего месяца (первое число)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    print(current_month_start)

    for lead in leads:
        for contact_data in lead.contacts:
            manager_name = contact_data.responsible_user.name
            if manager_name not in manager_stats:
                manager_stats[manager_name] = {
                    "total_deals": 0,           # Общие данные
                    "total_completed_deals": 0,
                    "total_deals_sum": 0,
                    "total_completed_deals_sum": 0,

                    "recent_deals": 0,          # Последние сутки
                    "recent_completed_deals": 0,
                    "recent_deals_sum": 0,
                    "recent_completed_deals_sum": 0,

                    "week_deals": 0,            # Текущая неделя
                    "week_completed_deals": 0,
                    "week_deals_sum": 0,
                    "week_completed_deals_sum": 0,

                    "month_deals": 0,           # Текущий месяц
                    "month_completed_deals": 0,
                    "month_deals_sum": 0,
                    "month_completed_deals_sum": 0,
                }

            # Увеличиваем общее количество сделок
            manager_stats[manager_name]["total_deals"] += 1

            # Проверяем, завершена ли сделка
            if lead.closed_at is not None:
                manager_stats[manager_name]["total_completed_deals"] += 1
                manager_stats[manager_name]["total_completed_deals_sum"] += lead.price
                if lead.closed_at >= one_day_ago:
                    manager_stats[manager_name]["recent_completed_deals"] += 1
                    manager_stats[manager_name]["recent_completed_deals_sum"] += lead.price
                if lead.closed_at >= current_week_start:
                    manager_stats[manager_name]["week_completed_deals"] += 1
                    manager_stats[manager_name]["week_completed_deals_sum"] += lead.price
                if lead.closed_at >= current_month_start:
                    manager_stats[manager_name]["month_completed_deals"] += 1
                    manager_stats[manager_name]["month_completed_deals_sum"] += lead.price

            # Увеличиваем общую сумму сделок
            manager_stats[manager_name]["total_deals_sum"] += lead.price

            # Сделки за последние сутки
            if lead.created_at >= one_day_ago:
                manager_stats[manager_name]["recent_deals"] += 1
                manager_stats[manager_name]["recent_deals_sum"] += lead.price

            # Сделки за текущую неделю
            if lead.created_at >= current_week_start:
                manager_stats[manager_name]["week_deals"] += 1
                manager_stats[manager_name]["week_deals_sum"] += lead.price

            # Сделки за текущий месяц
            if lead.created_at >= current_month_start:
                manager_stats[manager_name]["month_deals"] += 1
                manager_stats[manager_name]["month_deals_sum"] += lead.price

    return manager_stats



