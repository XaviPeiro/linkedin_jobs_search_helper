from linkedin_jobs_search_helper.jobs.infraestracture.notifications.fs import FileSystemNotificator
from linkedin_jobs_search_helper.settings import get_settings

notifier_unexpected_openai_response = FileSystemNotificator(
    filepath=str(get_settings().openai_unexpected_responses_path)
)
