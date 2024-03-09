# stepik_storeapi

Решение задачи ["API магазина"](https://stepik.org/lesson/1186984/step/8?unit=1222202) для курса ["Python-разработчик"](https://stepik.org/course/122813/) на [степике](https://stepik.org)

Буду благодарен за фидбек в Issues или Discussions.

## Задача

> Теперь ваша очередь написать свою API – часть онлайн магазина.
>
> Ваша задача – сделать API, которая позволит клиентам:
>
> - Получить список уникальных товаров – каждый товар в единичном экземпляре, у него есть описание, название и цена.
> - Добавить товар в корзину
> - Удалить товар из корзины
> - Оформить заказ. Чтобы это сделать пользователю достаточно указать свою почту.
>
> Все эндпоинты для клиентов должны работать без аутентификации.
>
> У вас также есть две дополнительные роли – менеджер и админ.
>
> Менеджер может менять товарам цену и описание.
>
> Администратор может всё, что может менеджер, а также добавлять товары на платформу.
>
> Для администраторов и менеджеров обязательно нужно проводить аутентификацию и авторизацию.
>
> Удачи в выполнении!
>
> В качестве ответа на задачу прикладывайте ссылку на GitHub.


[Пример](https://stepik.org/lesson/1186984/step/7?unit=1222202) решения похожей задачи из курса: [gardiys/stepik_blog](https://github.com/gardiys/stepik_blog).

## Замечания по реализации

### Основные условности

Вместо логина (имени пользователя) тут используется email.

В этой реализации корзин несколько, разделение идёт по email, но без аутентификации. По идее нужно хранить корзину в сессии, но пока без неё.

Добавил хранение паролей в виде хеша, но по идее нужно аутентификацию вынести в отдельный модуль и использовать например OAuth токены, вместо передачи логина/пароля в каждый эндпоинт.

### Хранение пользователей

Для простоты тестирования, в этой реализации пользователи хранятся в предопределённом списке в памяти.
Список предопределённых тестовых пользователей:

- Пользователь `vasya@example.com`
- Менеджер `ivan@example.com`, пароль `test`
- Администратор `admin@example.com`, пароль `god`

### Упрощения для Swagger UI

Для того чтобы данные в Swagger UI были в виде отдельных полей, а не в виде json текста в функциях эндпоинтов использована конструкция:

~~~python
credentials: Annotated[LoginModel, Depends()]
~~~

вместо например

~~~python
credentials: Annotated[LoginModel, Body()]
~~~

Это упрощает тестирование в Swagger UI, но в этом случае данные передаются как query параметры, например `/items?name=123&description=123&price=123&email=123&password=123`, что плохо для реального использования.

## Запуск

Создайте виртуальное окружение (если нет):

~~~bash
pip install --user virtualenv
virtualenv .venv
~~~

Активируйте его:

~~~bash
. .venv/bin/activate
~~~

Установите зависимости:

~~~bash
pip install -r requirements.txt
~~~

Для запуска используйте [uvicorn](https://www.uvicorn.org) с параметрами ниже:

~~~bash
uvicorn store.main:app --reload --port 8080
--app-dir src/
~~~

## Документация

Её необходимо собрать с помошью [mkdocs](https://www.mkdocs.org). Для этого нужно установить зависимости:

~~~bash
pip install -r requirements.txt
pip install -r requirements.docs.txt
~~~

После этого либо собрать документацию в каталог `site/`, либо запустить тестовый сервер.

~~~bash
# сборка
mkdocs build
# тестовый сервер
mkdocs serve
~~~

Стандартные **локальные** URL документации:

- Документация mkdocs: http://127.0.0.1:8000/
- Документация Swagger: http://127.0.0.1:8080/docs
