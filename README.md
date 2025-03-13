Программное средство для анализа и прослушивания музыкальных произведений

 Гаевский Ростислав Сергеевич, гр. 353504  


 Функциональная модель программного обеспечения  

Разрабатываемое программное средство представляет собой настольное приложение, реализованное с использованием фреймворка PyQt. Оно позволяет пользователю:  

- Воспроизводить музыкальные файлы.  
- Получать информацию о треках.  
- Управлять библиотекой композиций.  
- Проводить базовый аудиоанализ (спектрограмма, частотный анализ, визуализация формы сигнала).  

Программное средство предусматривает два уровня доступа: гость и авторизованный пользователь.  

 Роли и их функционал  

 Роль "Гость" 
- Прослушивание доступных по умолчанию треков.  
- Просмотр информации о треках.  
- Возможность входа в систему.  

 Роль "Авторизованный пользователь"
- Загрузка и управление собственной музыкальной библиотекой.  
- Сохранение и редактирование плейлистов.  
- Прослушивание и анализ музыкальных файлов.  
- Получение расширенной информации о треках.  
- Визуализация аудиосигнала.  
- Управление профилем.  


 Функциональные требования  
 1. Функция регистрации и входа  

- Регистрация нового пользователя с вводом логина и пароля.  
- Проверка надежности пароля.  
- Возможность восстановления пароля через email.  
- Хэширование пароля при его сохранении.  

 2. Функция управления музыкальной библиотекой  

- Загрузка треков в популярных форматах (mp3, wav, flac).  
- Создание, редактирование и удаление плейлистов.  
- Поиск треков по:  
  - Названию,  
  - Исполнителю,  
  - Альбому,  
  - Жанру.  
- Сортировка треков по:  
  - Дате загрузки,  
  - Алфавиту,  
  - Длительности.  

3. Функция воспроизведения аудио  

- Управление воспроизведением:  
  - Воспроизведение, пауза, перемотка.  
- Поддержка очереди воспроизведения.  
- Регулировка громкости и режима повтора.  
- Отображение текущего времени и длительности трека.  

 4. Функция анализа музыкальных произведений  

- Отображение спектрограммы и волновой формы сигнала.  
- Расчёт частотных характеристик:  
  - Основная частота,  
  - Интенсивность.    
  - Вывод текста произведение.

 5. Функция управления профилем  

- Смена пароля.  
- Изменение отображаемого имени.  
- Удаление аккаунта (по запросу пользователя).  


