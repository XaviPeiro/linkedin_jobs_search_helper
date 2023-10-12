from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from components import notifier_unexpected_openai_response
from logger import app_logger
from openai_api import OpenAIClient

# Let's assume criteria is a text to search in the descr
system_message = """
    You will be provided with IT job descriptions and you will be asked many questions about it in order to know if I should discard this job offer or not. 
    Answer "yes" if the answer to one of the following questions is yes, otherwise answer "no".
"""
system_message = """
    You will be provided with IT job descriptions and you will be asked many questions about it in order to know if I should discard this job offer or not. 
    Answer exclusively with a "yes" and "no". I do not want you to answer anything else than "yes" or "no", no explanation allowed.
"""
prompts_prelude_for_job_description = 'Assuming this job description: \"{}\". Answer the following yes-no questions, I do not want you to respond anything else than yes or no.'

OAI_prompts_v3_5 = {
    "system_message": system_message,
    "prompts_prelude_for_job_description": prompts_prelude_for_job_description
}


class ICriteria(ABC):

    @abstractmethod
    def apply(self, entities: list):
        ...


@dataclass
class JobDescriptionOAICriteria(ICriteria):
    """
        Actually it is an "anyYes"
    """
    open_ai_client: OpenAIClient
    criteria: list[str]

    @staticmethod
    def any_yes_in_response(answer: str):
        if "yes" in answer.lower():
            return True
        elif "no" in answer.lower():
            return False
        else:
            notifier_unexpected_openai_response.notify(f"{datetime.now()} - {answer}")
            return None

    def apply(self, entities: list) -> list[bool, None]:
        res: list = []

        # To keep it cheap I use 3.5-turbo. Besides that, I want to get only True/False as response, but the only way
        # I've found to do that is specifying "this is a yes-no question" (pregunta directa total); exchanging
        # yes/no by True/False doesn't work. The "Yes/No" answer comes with a final dot, so it has to be trimmed
        # and hyphens if many.
        for job_descr in entities:
            prelude = OAI_prompts_v3_5.get("prompts_prelude_for_job_description")
            self.open_ai_client.start_chat()
            self.open_ai_client.add_message(message=prelude.format(job_descr))

            criteria = "\n".join(self.criteria)
            answer = self.open_ai_client.chat_request(message=criteria)
            bool_answer = self.any_yes_in_response(answer)
            res.append(bool_answer)

            app_logger.info(f"Question: {criteria}")
            app_logger.info(f"ANSWER: {answer}")

            self.open_ai_client.clear_chat()

        return res


