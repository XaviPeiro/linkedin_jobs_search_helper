from abc import ABC, abstractmethod

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

