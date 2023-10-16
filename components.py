from infraestracture.notifications.fs import FileSystemNotificator
from datetime import date


notifier_unexpected_openai_response = FileSystemNotificator(filepath=f"data/{date.today()}-openai_discard_jobs.txt")
notifier_ordered_jobs_by_relevance = FileSystemNotificator(filepath=f"data/{date.today()}-ordered_by_relevance_jobs.txt")
