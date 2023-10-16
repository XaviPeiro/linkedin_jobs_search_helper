from infraestracture.notifications.fs import FileSystemNotificator

notifier_unexpected_openai_response = FileSystemNotificator(filepath="logs/openai_unexpected_responses.txt")
notifier_ordered_jobs_by_relevance = FileSystemNotificator(filepath="data/ordered_by_relevance_jobs.txt")
