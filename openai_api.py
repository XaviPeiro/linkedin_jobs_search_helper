from dataclasses import dataclass, field
from typing import Self

import openai


class RateLimitException(Exception):
    ...


@dataclass
class OpenAIClient:
    secret: str
    _system: dict[str, str] = field(init=False, default_factory=lambda: {"system": ""})
    _chat_context: list[dict] = field(init=False, default_factory=list)

    def __post_init__(self):
        openai.api_key = self.secret

    @classmethod
    def init_with_role(cls, secret: str, message: str) -> Self:
        instance: Self = cls(secret=secret)
        instance._system = {"role": "system", "content": f"{message}"}

        return instance

    def _request(self, messages: list[dict]):
        # TODO: I really have to investigate more about the openai API, so using "create" all the time sounds
        #  counterintuitive. Let's check best practices and other methods like "acreate" and "get".
        #  (the response does not include any ID to the created chat.)

        try:
            response = openai.ChatCompletion.create(
                # model="gpt-3.5-turbo",
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=1,
                max_tokens=50,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
        except openai.error.RateLimitError as rate_limit_e:
            raise RateLimitException from rate_limit_e
        except openai.error.ServiceUnavailableError as sue:
            # TODO: maybe wait or retry policy, by the moment only making this usecase obvious.
            raise sue
        except Exception as e:
            raise e

        return response

    @property
    def system(self):
        return self._system.get("content")

    @system.setter
    def system(self, message: str):
        self._system["content"] = message


    """
        Clean brand new request.
    """
    def request(self, message: str):
        messages = [self._system]
        messages.extend({"role": "user", "content": f"{message}"})
        return self._request(messages=messages)

    # TODO: Better to use a context manager for the whole chat thing.
    def start_chat(self):
        self._chat_context = [self._system]

    """
        Works in a chat, ie keeps the context, the previous both sides messages.
    """
    def chat_request(self, message: str):
        self.add_message(message=message)
        res = self._request(messages=self._chat_context)
        answer = res["choices"][0]["message"]["content"]
        self._chat_context.append({"role": "assistant", "content": f"{answer}"})

        return answer

    def add_message(self, message: str):
        self._chat_context.append({"role": "user", "content": f"{message}"})

    def clear_chat(self):
        self._chat_context = []


def main():
    secret = ""
    system_message = "You're helping me to find a remote IT job. I live in Poland, Europe."
    txt_tmlpate = "Assuming this job description: \"{}\". It is mandatory to live in the USA to apply this job? Please, respond exclusively True or False."
    openai_client = OpenAIClient.init_with_role(secret=secret, message=system_message)
    res = openai_client.request(message=txt_tmlpate)


if __name__ == "__main__":
    main()
