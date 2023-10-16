from dataclasses import dataclass
from datetime import datetime

from components import notifier_unexpected_openai_response
from domain.criteria.criteria import ICriteria, OAI_prompts_v3_5
from logger import app_logger
from openai_api import OpenAIClient


@dataclass
class JobDescriptionOAICriteria(ICriteria):
    """
        Actually it is an "anyYes"
    """
    open_ai_client: OpenAIClient
    criteria: list[str]

    # TODO: create a transformer (ToBool(gpt_res)||AnyYes(gpt_res)). This make no sense.
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


# @dataclass
# class JobDescriptionRelevanceRate(ICriteria):
#     open_ai_client: OpenAIClient
#     criteria: list[str]
#
#     def apply(self, entities: list):
#         ...
#
