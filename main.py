import asyncio
import random
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact
from telethon.errors import UserPrivacyRestrictedError, FloodWaitError

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')
GROUP_USERNAME = os.getenv('GROUP_USERNAME') 

phone_numbers = ['+998940667509', '+998992424373','+998946138786','+998888114171'] 

client = TelegramClient('session_leadgen', API_ID, API_HASH)

async def main():
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE)
        await client.sign_in(PHONE, input('Введите код из Telegram: '))

    print("=== Система успешно запущена ===")
    
    try:
        group = await client.get_entity(GROUP_USERNAME)
    except Exception as e:
        print(f"Группа не найдена: {e}")
        return

    for number in phone_numbers:
        print(f"\n[{number}] Проверка...")
        try:
            contact = InputPhoneContact(
                client_id=random.randrange(-2**63, 2**63),
                phone=number,
                first_name='Check',
                last_name=''
            )
            result = await client(ImportContactsRequest([contact]))
            
            if result.users:
                user = result.users[0]
                print(f"✓ Номер есть в Telegram! ID: {user.id}, Имя: {user.first_name}")
                
                print(f"Попытка добавления в группу: {GROUP_USERNAME}...")
                
                from telethon.tl.types import Channel, Chat
                from telethon.tl.functions.messages import AddChatUserRequest
                
                try:
                    if isinstance(group, Channel):
                        invite_result = await client(InviteToChannelRequest(group, [user]))
                        
                        is_missing = False
                        if hasattr(invite_result, 'missing_invitees'):
                            for missing in invite_result.missing_invitees:
                                if missing.user_id == user.id:
                                    is_missing = True
                                    break
                        
                        if is_missing:
                            print(f"⚠ {number} не добавлен (Missing). Причина: Настройки конфиденциальности пользователя (только для контактов) или ограничение Telegram.")
                        else:
                            print(f"++ {number} успешно добавлен в группу!")
                            
                    elif isinstance(group, Chat):
                        await client(AddChatUserRequest(group.id, user.id, fwd_limit=100))
                        print(f"++ {number} успешно добавлен в группу!")
                    else:
                        print(f"Неизвестный тип группы: {type(group)}")
                        
                except Exception as invite_err:
                    print(f"Ошибка при добавлении: {invite_err}")
                
                try:
                    await client(DeleteContactsRequest([user]))
                except Exception:
                    pass
            else:
                print(f"✗ На этом номере Telegram не зарегистрирован.")
            
        except UserPrivacyRestrictedError:
            print(f"⚠ Пользователь запретил добавление в группы в настройках.")
        except FloodWaitError as e:
            print(f"🛑 Telegram ввел ограничение (FloodWait)! Нужно подождать {e.seconds} секунд.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            
        await asyncio.sleep(5)

with client:
    client.loop.run_until_complete(main())