from infraestracture.notifications.fs import FileSystemNotificator

notifier_unexpected_openai_response = FileSystemNotificator(filepath="logs/openai_unexpected_responses.txt")
