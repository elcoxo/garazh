import uuid

from aiogram import F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputRichMessage, Message
from aiogram.utils.markdown import hbold
from aiogram_i18n.lazy import LazyProxy as _
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot import telegram_router
from bot.keyboards import get_user_context, main_keyboard
from db.redis import redis_client
from models import User
from services.calendar import list_calendars
from settings import get_settings

cfg = get_settings()


@telegram_router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(f"Your ID: {message.from_user.id}")


@telegram_router.message(CommandStart())
async def cmd_start(message: Message, db_user: User, session: AsyncSession) -> None:
    ctx = get_user_context(db_user)
    await message.answer(f"Hello, {hbold(db_user.tg_full_name)}!", reply_markup=main_keyboard(ctx))


@telegram_router.message(F.text == _('btn-connect-calendar'))
@telegram_router.message(Command('connect'))
async def cmd_connect(message: Message, db_user: User) -> None:
    token = str(uuid.uuid4())
    await redis_client.setex(f'connect_token:{token}', 600, str(db_user.id))
    url = f'{cfg.app_base_url}/auth/google?token={token}'
    sent = await message.answer_rich(
        rich_message=InputRichMessage(
            markdown='# Авторизация\n\nАвторизуйтесь, чтобы подключить календарь.',
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Google Calendar', url=url)],
        ]),
    )
    await redis_client.setex(f'auth_msg:{db_user.id}', 700, str(sent.message_id))


@telegram_router.message(F.text == _('btn-support'))
async def btn_support(message: Message) -> None:
    await message.answer('По всем вопросам: @temets')


@telegram_router.message(Command('calendars'))
async def cmd_calendars(message: Message, db_user: User, session: AsyncSession) -> None:
    credential = db_user.oauth_credential
    if credential is None:
        await message.answer('Сначала подключи календарь: /connect')
        return

    calendars = await list_calendars(session, credential)
    if not calendars:
        await message.answer('Календари не найдены')
        return

    lines = '\n'.join(f'• {cal.name}' for cal in calendars)
    await message.answer(f'📅 Твои календари:\n\n{lines}')


@telegram_router.message(F.text == 'test')
async def cmd_test(message: Message) -> None:
    await message.answer_rich(
        rich_message=InputRichMessage(
            html=(
                "<h1>Heading 1 (самый большой)</h1>"
                "<h2>Heading 2</h2>"
                "<h3>Heading 3</h3>"
                "<h4>Heading 4</h4>"
                "<h5>Heading 5</h5>"
                "<h6>Heading 6 (самый маленький)</h6>"
                "<p>Обычный параграф для сравнения</p>"
            )
        ),
    )


@telegram_router.message(F.text == 'test2')
async def cmd_test2(message: Message) -> None:
    await message.answer_rich(
        rich_message=InputRichMessage(
            markdown="""**bold text** __bold text__ *italic text* _italic text_ ~~strikethrough text~~ `inline fixed-width code` ==marked text== ||spoiler||

[inline URL](https://t.me/) [inline e-mail](mailto:user@example.com) [inline phone number](tel:+123456789) [inline mention of a user](tg://user?id=123456789) ![👍](tg://emoji?id=5368324170671202286) ![22:45 tomorrow](tg://time?unix=1647531900&format=wDT) $x^2 + y^2$ \\#hashtag $USD +12345678901, card: 4242 4242 4242 4242, https://t.me t.me a@t.me /command @username all the text above was on the same line

# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6

Paragraph text

```python
  print('pre-formatted fixed-width code block written in the Python programming language')
```

---

- unordered list item
* unordered list item
+ unordered list item

1. ordered list item
2. ordered list item

- [ ] task list item
- [x] completed task list item

>Block quotation started
>
>Block quotation continued on the next line
>Block quotation continued on the same line
>
>The last line of the block quotation

![](https://telegram.org/example/photo.jpg)
![](https://telegram.org/example/video.mp4)
![](https://telegram.org/example/audio.mp3)
![](https://telegram.org/example/audio.ogg)
![](https://telegram.org/example/animation.gif)

![](https://telegram.org/example/photo.jpg "Photo caption")
![](https://telegram.org/example/video.mp4 "Video caption")
![](https://telegram.org/example/audio.mp3 "Audio caption")
![](https://telegram.org/example/audio.ogg "Voice note caption")
![](https://telegram.org/example/animation.gif "Animation caption")

| Header 1 | Header 2 |
|:---------|:--------:|
| left     | center   |

Text with a reference[^id1] and another one[^id2].

[^id1]: Definition of the first footnote.
[^id2]: Definition of the second footnote.

$$E = mc^2$$

```math
E = mc^2
```

## Example Nested Syntax Report for _Q1_
Intro with <u>underlined text</u>, ==marked text==, and $x^2 + y^2$.
**Bold _italic <u>underlined italic bold</u> italic_ bold**
<u>In inline tags, nested **markdown** is parsed</u>
>Quote with **bold text, ~~strikethrough, and <tg-spoiler>spoiler</tg-spoiler>~~**, plus [a link](https://t.me/).

- List item with `code`, <sup>superscript</sup>, <sub>subscript</sub>, and a footnote[^note]
- Another item with **bold <tg-spoiler><code>spoiler code</code></tg-spoiler>**
- Another item with ~~strikethrough and <ins>inserted text</ins>~~

| Metric | Value |
|:-------|------:|
| Speed  | **42** <sup>ms</sup> |
| Status | <tg-spoiler>ready</tg-spoiler> |

[^note]: Footnote with _italic text_ and <u>HTML underline</u>.

---

# Details blocks can contain Markdown content:

<details open><summary>Summary with **bold text**</summary>

### Details heading
- List item with _italic text_
- List item with <tg-spoiler>spoiler</tg-spoiler>

</details>

# Collages and slideshows can contain Markdown media blocks:

<tg-collage>

![](https://telegram.org/example/photo.jpg)
![](https://telegram.org/example/video.mp4)

</tg-collage>

<tg-slideshow>

![](https://telegram.org/example/photo.jpg)
![](https://telegram.org/example/video.mp4)

</tg-slideshow>"""
        ),
    )

#
"""
# Календарь
Почта: `почта юзера`

- [ ] название календаря 1
- [x] название выбранный/aктивного календаря 2
- [ ] название календаря 3
"""


@telegram_router.message(F.text == "echo")
async def echo(message: types.Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except Exception as e:
        logger.error(f"Can't send message - {e}")
        await message.answer("Nice try!")


@telegram_router.message(F.text == 'ping')
async def hello(message: types.Message) -> None:
    try:
        await message.answer('pong')
    except Exception as e:
        logger.error(f"Can't send message - {e}")
        await message.answer("Nice try!")
