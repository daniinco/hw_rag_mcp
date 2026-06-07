# быстрый гайд на запуск:

```
git clone https://github.com/daniinco/hw_rag_mcp.git
cd hw_rag_mcp 
добавить povarenok.csv в файл - скачать тут https://github.com/ashaba1in/hse-nlp/blob/2025/homeworks/hw5_rag/povarenok.csv
сделать окружение, у меня так:
/opt/homebrew/bin/python3.12 -m venv .venv

source .venv/bin/activate
pip install -r requirements.txt

дальше уже запуски
python ingest.py
python search_demo.py

ollama pull qwen2.5:7b # у меня уже такой скачан, можно другой
ollama serve

python agent_demo.py

python eval_runner.py
```



# Выбрать mcp -
Выбрал qdrant, всё запускаю локально

# Корпус документов.
Взял файлик povarenok.csv из курса по nlp, русскоязычный
Это 40000 рецептов спаршенных с кулинарного сайта
По факту будем использовать для демонстрации только первые 500

В нём 3 поля: name,ingredients,text

# индексация
файлик povarenok.csv надо положить в ту же папку где и все остальные сданные файлики лежат

Запуск индексации

`.venv/bin/python ingest.py`

В самом файле заданы параметры индексации и сколько строк брать

```
Выведет:
Загружено рецептов: 500
Всего фрагментов: 520
  загружено 256/520
  загружено 512/520
  загружено 520/520
Индексация завершена.
Точек в коллекции: 520
```

Каждый фрагмент сохраняется с метаданными:
```
points.append({
                "id": uid, айдишник
                "text": chunk, текст
                "metadata": {
                    "document_id": str(csv_row), номер строчки в цсв
                    "chunk_id": str(ci), номер чанка в строчке
                    "source": f"povarenok.csv:{csv_row}",
                    "title": name, заголовок
```

# подключить mcp и демонстрация top-k поиска

Конфигурация в mcp_config.json

инструмент поиска - qdrant-find
Это название выведет при запуске скрипта с демонстрацией mcp:

`.venv/bin/python search_demo.py 2>/dev/null`

Результат:
Инструменты: ['qdrant-find', 'qdrant-store']

```
Query: Рецепт борща
Top-k: 3
1. document_id=150, chunk_id=0
   source=povarenok.csv:150
   text=Бастурма из баранины Ингредиенты: ['Баранина', 'Соль', 'Специи', 'Перец чили', 'Лист лавровый'] Смешиваем все игридиенты...
2. document_id=145, chunk_id=1
   source=povarenok.csv:145
   text=забывала этот рецепт, которым я смогу удивить....
3. document_id=493, chunk_id=0
   source=povarenok.csv:493
   text=Овощной суп с чёрным рисом Ингредиенты: ['Рис', 'Баклажан', 'Перец болгарский', 'Помидоры черри', 'Лук репчатый', 'Морко...

Query: Как приготовить тесто для пиццы
Top-k: 3
1. document_id=145, chunk_id=1
   source=povarenok.csv:145
   text=забывала этот рецепт, которым я смогу удивить....
2. document_id=74, chunk_id=1
   source=povarenok.csv:74
   text=приготовленная таким способом, не превращается в сухую корку, остается влажной. Остывшие куличи вынуть из форм, покрыть ...
3. document_id=75, chunk_id=0
   source=povarenok.csv:75
   text=Салат с морской капустой Ингредиенты: ['Перец болгарский', 'Тыква', 'Капуста морская', 'Зелень', 'Хлебцы'] Перец нарезат...

Query: Десерт из шоколада
Top-k: 3
1. document_id=457, chunk_id=0
   source=povarenok.csv:457
   text=Шоколадная паста от Джейми Оливера Ингредиенты: ['Фундук', 'Сахар', 'Шоколад темный', 'Сливки', 'Масло сливочное'] Набор...
2. document_id=178, chunk_id=0
   source=povarenok.csv:178
   text=Кекс с шоколадом на сметане Ингредиенты: ['Мука пшеничная', 'Сметана', 'Разрыхлитель теста', 'Яйцо куриное', 'Сахар', 'М...
3. document_id=290, chunk_id=0
   source=povarenok.csv:290
   text=Шоколад в шоколаде Ингредиенты: ['Шоколад молочный', 'Масло растительное', 'Цедра апельсина', 'Сок апельсиновый', 'Шокол...
```


# Подключение mcp к агенту:
используем LangGraph

# Демонстрация агента

```
ollama pull qwen2.5:7b # у меня уже такой скачан, можно другой
ollama serve  # если не запущен

.venv/bin/python agent_demo.py 2>/dev/null
```

Проверка на 20 запросах
```
.venv/bin/python eval_runner.py 2>/dev/null
```

результат в eval_queries.csv, там есть поле с началом ответа модели и есть поле с вердиктом о правильности и моим комментарием:
text_preview,in_top3,manual_judgement,comment


Вообще поиск отработал скорее плохо, но пару раз нашел че надо
Вероятно дело в русскоязычности документа и слабых локальных модельках



