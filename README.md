# linguine_bot
Основнная идея - создать "обучающего" бота, который присылает видео и задание на лексику из него, при этом позволяя в любой момент залезть в словарь. 
Соответственно, компоненты реализации следующие:
1. Источник видео с транскриптами, чтобы по транскриптам генерить упражнения. 
2. Алгоритм генерации упражнений.
3. Проверка упражнений.
4. Словарный источник.
5. Сервис для хранения состояний.

Предлагаемые решения:
1. Видео дергается с платформы TEDTalks (https://www.ted.com/talks), т.к. там подавляющее число видео имеют транскрипты. 
Реализовано два режима получения видео - по ссылке на страничку TEDTalks от пользователя и рандомным выбором из заранее собранных ссылок.
Ссылки собирались селениумом: на вход подается страничка, где видео отфильтрованы  по языку (английский) и по длине (не более 6 минут, чтобы не утомлять). Селениум вытаскивает ссылки всех видео на странице, затем переходит на следующую. По-хорошему надо бы запускать его регулярно и дописывать новые ссылки, но я пока остановилась на достигнутом. 
Далее ссылка на страничку парсится с помощью BeautifulSoup, чтобы получить доступ непосредственно к ссылке на видео файл. 
Телеграмбот его сам скачивает в процессе обработки отправляемого сообщения. 
Транскрипты собираются также через BeautifulSoup по ссылке на страницу.
2. Реализован один тип упражнений - нужно заполнить пропущенное слово вариантом на выбор. 
Для этого из транскрипта извлекаются ключевые слова (библиотечка yet another keyword extractor), из них удаляются имена собственные, затем берутся топ 10 самых нераспространенных (чтобы не было заданий на простые словечки типа job). Далее ищем предложения с этими словами и заменяем на пропуски, одно предложение - одно пропущенное слово. Всего нужно 5 предложений, но я взяла 10 ключевых слов на случай, если сразу несколько из них встретятся в одном предложении. 
Далее нужно как-то сгенерировать варианты ответа. Поначалу я хотела честно использовать Word2Vec-модель из библиотеки gensim, которая расчитывает N самых близких слов основываясь на векторном представлении, но я так и не смогла развернуть модель на сервере, поэтому нашла сайт ('http://bionlp-www.utu.fi/wv_demo/'), который предоставляет веб-интерфейс для обращения к модели 'English GoogleNews Negative300'. Я запускаю селениум и просто вбиваю нужные мне слова в форму на сайте, потом забираю результат. На случай, если слова не будет в модели, дополнительно прикручен скрапинг с сайта, который ищет созвучные слова ('https://www.rhymezone.com/') - там обязательно что-нибудь найдется (пример: для bassmobile предлагается bannable и subsumable, лучше чем ничего :). 
3. Проверка упражнений по точному совпадению, для ответа сделаны кнопки. В конце подсчитывается количество правильных ответов.  
4. Используется Merriam-Webster's Collegiate Dictionary по API. Пока реализован поиск только по точному вхождению, но в теории он умеет подцеплять и деривативы по совпадающему корню слова. Оттуда же дергается аудиофайлик с произношением слова (чтобы узнать его в видео может оказаться полезным).
5. Для хранения состояний используется SQLite. Хранятся две цепочки состояний: для навигации по словарю и для работы с видео. Раздельные цепочки нужны для того, чтобы можно было лазить в словарик в процессе выполнения упражнений.
