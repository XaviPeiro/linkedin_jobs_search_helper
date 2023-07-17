from dataclasses import dataclass, field
from typing import Self

import openai


class RateLimitException(Exception):
    ...


@dataclass
class OpenAIClient:
    secret: str
    _system: dict[str, str] = field(init=False, default_factory=lambda: {"system": ""})

    def __post_init__(self):
        openai.api_key = self.secret

    @classmethod
    def init_with_role(cls, secret: str, message: str) -> Self:
        instance: Self = cls(secret=secret)
        instance._system = {"role": "system", "content": f"{message}"}

        return instance

    def request(self, message: str):
        # TODO: I really have to investigate more about the openai API, so using "create" all the time sounds
        #  counterintuitive. Let's check best practices and other methods like "acreate" and "get".
        #  (the response does not include any ID to the created chat.)

        try:
            # system_message = "You're helping me to find a remote IT job. I live in Poland, Europe."
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    self._system,
                    {
                        "role": "user",
                        "content": f"f{message}"
                    },

                ],
                temperature=1,
                max_tokens=64,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
        except openai.error.RateLimitError as rate_limit_e:
            raise RateLimitException from rate_limit_e
        except openai.error.ServiceUnavailableError as sue:
            # TODO: maybe wait or retry policy, by the moment only making this usecase obvius.
            raise sue

        return response


def main():
    secret = ""
    system_message = "You're helping me to find a remote IT job. I live in Poland, Europe."
    txt_tmlpate= "Assuming this job description: \"{}\". It is mandatory to live in the USA to apply this job? Please, respond exclusively True or False."
    openai_client = OpenAIClient.init_with_role(secret=secret, message=system_message)
    res = openai_client.request(message=txt_tmlpate)
    print("HELLLLLLLLLLLLLLLLLLLLLLL")
    print(res)


if __name__ == "__main__":
    main()
