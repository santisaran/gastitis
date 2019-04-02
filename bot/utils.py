from django.contrib.auth.models import User

from bot.models import TelegramUser, TelegramGroup
from expenses.models import Expense


def user_and_group(func):
    """
    Add user and group to handler params.
    """
    def wrapper(update, context):
        user_data = update.message.from_user
        chat_id = user_data.id
        first_name = getattr(user_data, 'first_name', chat_id)
        last_name = getattr(user_data, 'last_name') or '-'
        telegram_username = getattr(user_data, 'username', '')
        username = telegram_username or first_name
        user, _ = User.objects.get_or_create(telegram__chat_id=user_data.id, defaults={
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
        })

        TelegramUser.objects.update_or_create(
            user=user, chat_id=chat_id, defaults={
                'username': telegram_username
            })
        group_data = update.message.chat
        group_id = group_data.id
        group_name = group_data.title or username + '__private'

        group, _ = TelegramGroup.objects.get_or_create(chat_id=group_id, defaults={
            'name': group_name,
        })
        group.users.add(user)


        func(update, context, user, group)

    return wrapper


def new_expense(params, user, group):
    """
    Check if params are valid and create a new expense.

    Returns a text to send to the user.
    """
    if not params:
        return 'Necesito que me digas cuanto pagaste y una descripción del gasto.'

    amount_received, *description = params

    try:
        amount = amount_received.replace(',', '.')
        amount = float(amount)

    except ValueError:
        return 'El primer valor que me pasas después del comando tiene que ser el valor de lo '\
               'que pagaste, "{}" no es un número válido.'.format(amount_received)

    if not description:
        return 'Necesito que agregues una descripción del gasto.'

    description = ' '.join(description)
    expense = Expense(user=user, group=group, description=description, amount=amount)
    expense.save()

    return 'Se guardo tu gasto {}'.format(expense)
