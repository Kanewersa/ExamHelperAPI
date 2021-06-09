import base64
import io
import json

from PIL import Image

import pytesseract
from channel import Channel
from database import Statement


class ExamChannel(Channel):
    def __init__(self, identifier):
        super().__init__(identifier)

    async def add_question(self, data):
        data = data.split('/', 1)
        encoded_image = data[1]
        image_string = encoded_image.split('base64,')[-1].strip()
        image_string = io.BytesIO(base64.b64decode(image_string))
        image = Image.open(image_string).convert("RGBA")

        # Add white background in case image is transparent
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, image)

        image_content = pytesseract.image_to_string(bg, lang="pol").replace('\n', ' ').replace('\r', '')

        questions = Statement() \
            .insert("questions (content, image, exam_id)", str(image_content), str(encoded_image), str(self.identifier)) \
            .returning() \
            .execute()

        question = questions[0]

        q = {
            "id": question[0],
            "content": question[1],
            "base64": question[2],
            "exam_id": question[3],
        }

        await super().process_message(None, "added_question:" + json.dumps(q))

    def add_answer(self, user):
        self.process_message(user, "added_answer")

    async def process_message(self, user, message):
        if message.startswith("get_answers"):
            msg = message.split('/')
            answers = Statement().get_all("answers").where("question_id = " + str(msg[1])).execute()
            await user.send("answers:" + json.dumps(answers))
        elif message.startswith("add_question"):
            await self.add_question(message)
        elif message.startswith("vote"):
            msg = message.split('/')
            if msg[2] == "-1":
                Statement().update("answers", "downvotes = downvotes + 1").where("id = " + msg[1]).execute()
            elif msg[2] == "1":
                Statement().update("answers", "upvotes = upvotes + 1").where("id = " + msg[1]).execute()
            else:
                return
            answer = Statement().get_all("answers").where("id = " + msg[1]).execute()
        elif message.startswith("get_questions"):
            questions = Statement().get_all("questions").where("exam_id = " + str(self.identifier)).execute()
            questions_dict = {}

            for question in questions:
                q = {
                    "id": question[0],
                    "content": question[1],
                    "base64": question[2],
                    "exam_id": question[3],
                }

                questions_dict[question[0]] = q

            q_json = json.dumps(questions_dict)
            await user.send("questions:" + q_json)
        else:
            print("Unknown command: " + message + ". Sent by: " + user.identifier)
