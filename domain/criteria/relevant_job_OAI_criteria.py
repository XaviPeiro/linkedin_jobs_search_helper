from dataclasses import dataclass
from datetime import datetime

from components import notifier_unexpected_openai_response
from domain.criteria.criteria import ICriteria, OAI_prompts_v3_5
from logger import app_logger
from openai_api import OpenAIClient

system_message = """
You will be provided with IT job descriptions and you will be asked many questions about it in order to know if I should discard this job offer or not.

My profile:
- I am only authorized to work in the European Union.
- I have 7 years of experience as web developer.
- 6 years with Python.
- I'm strong at: Docker, Django,  Git, Docker-compose, REST API, Web Development, Linux.
- I'm regular at: PostgreSQL, ShellScript, MySQL, FastAPI.
- I'm so weak at: JS, AWS, Kubernetes, Java, MongoDB, ElasticSearch, Micro Services.
- My Spanish and Catalan level is native, and English full-proficiency.

Assume I have no knowledge of those technologies or fields I have not aforementioned.
"""

question = "How much my profile fits to this job from 1 to 100? Answer exclusively the numeric value, nothing else."


# For this one I should use GPT4. so 3.5 work pretty bad when in comes to that.
@dataclass
class JobDescriptionOAICriteriaRelevance(ICriteria):
    open_ai_client: OpenAIClient
    criteria: list[str]

    def apply(self, entities: list) -> list[bool, None]:
        res: list = []

        for job_descr in entities:
            prelude = OAI_prompts_v3_5.get("prompts_prelude_for_job_description")
            self.open_ai_client.start_chat()
            self.open_ai_client.add_message(message=prelude.format(job_descr))

            criteria = "\n".join(self.criteria)
            answer = self.open_ai_client.chat_request(message=criteria)
            res.append(answer)

            app_logger.info(f"Question: {criteria}")
            app_logger.info(f"ANSWER: {answer}")

            self.open_ai_client.clear_chat()

        return res
