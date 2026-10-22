"""Localized presentation text for native dashboard panels."""

MESSAGES = {'hy': {'SMART DIAGNOSTICS  •  AI ANALYSIS  •  BETTER DRIVING': 'ԽԵԼԱՑԻ ԱԽՏՈՐՈՇՈՒՄ  •  AI ՎԵՐԼՈՒԾՈՒԹՅՈՒՆ  •  ԱՊԱՀՈՎ '
                                                                'ՎԱՐՈՒՄ',
        '+ Add widget': '+ Ավելացնել վիջեթ',
        'No samples': 'Տվյալներ չկան',
        'Telemetry channel': 'Հեռաչափության ալիք',
        'Coolant temperature': 'Հովացուցիչ հեղուկի ջերմաստիճան',
        'MAP pressure': 'MAP ճնշում',
        'O2 sensor': 'O2 սենսոր',
        'Select a vehicle': 'Ընտրեք մեքենան',
        'Select vehicle': 'Ընտրել մեքենան',
        'Choose your model to begin a diagnostic session': 'Ախտորոշումը սկսելու համար ընտրեք մեքենայի մոդելը',
        'No acquisition running': 'Տվյալների հավաքագրումը չի գործարկվել',
        'Open live channels': 'Բացել տվյալների ալիքները',
        'No recommended tests yet': 'Առաջարկվող թեստեր դեռ չկան',
        'tests completed': 'թեստ ավարտված է',
        'INCOMPLETE results remain open': 'ԱՆԱՎԱՐՏ արդյունքները մնում են բաց',
        'Reported codes are evidence, not a confirmed component failure.': 'Գրանցված կոդերը տվյալներ են և դեռ չեն '
                                                                           'հաստատում բաղադրիչի խափանումը։',
        'Add symptoms / DTC': 'Ավելացնել ախտանշաններ / DTC',
        'No description supplied': 'Նկարագրություն չկա',
        'Source:': 'Աղբյուր՝',
        'No DTCs recorded in the current session': 'Ընթացիկ սեսիայում DTC կոդեր չկան',
        'AI hypotheses': 'AI վարկածներ',
        'Evidence-based hypotheses • Scores are not failure probabilities': 'Տվյալների վրա հիմնված վարկածներ • '
                                                                            'Գնահատականները խափանման հավանականություն '
                                                                            'չեն',
        'evidence score': 'տվյալների գնահատական',
        'Hypothesis': 'Վարկած',
        'unconfirmed': 'չհաստատված',
        'Recommended tests': 'Առաջարկվող թեստեր',
        'Add evidence and analyze the session to generate hypotheses': 'Վարկածներ ստանալու համար ավելացրեք տվյալներ և '
                                                                       'գործարկեք վերլուծությունը',
        'Missing evidence and questions will appear here': 'Բացակայող տվյալներն ու հարցերը կհայտնվեն այստեղ',
        'Export the current diagnostic record or reopen a backend session.': 'Արտահանեք ընթացիկ ախտորոշումը կամ բացեք '
                                                                             'պահված սեսիան։',
        'results': 'արդյունք',
        'Record an observed repair and its evidence. Ingestion adds reference material; it does not train the model or confirm a diagnosis.': 'Գրանցեք '
                                                                                                                                              'կատարված '
                                                                                                                                              'վերանորոգումն '
                                                                                                                                              'ու '
                                                                                                                                              'դրա '
                                                                                                                                              'տվյալները։ '
                                                                                                                                              'Նյութի '
                                                                                                                                              'ներմուծումը '
                                                                                                                                              'չի '
                                                                                                                                              'ուսուցանում '
                                                                                                                                              'մոդելը '
                                                                                                                                              'և '
                                                                                                                                              'չի '
                                                                                                                                              'հաստատում '
                                                                                                                                              'ախտորոշումը։',
        'Vehicle, DTCs, measurements, repair, and verified outcome…': 'Մեքենա, DTC կոդեր, չափումներ, վերանորոգում և '
                                                                      'ստուգված արդյունք…',
        'Drafts stay on this device until you choose to ingest them.': 'Սևագրերը մնում են այս սարքում մինչև '
                                                                       'ներմուծելը։',
        'Draft saved on this device': 'Սևագիրը պահպանվեց այս սարքում',
        'Add a title and observed repair details first.': 'Նախ ավելացրեք վերնագիրն ու վերանորոգման մանրամասները։',
        'Reference processed:': 'Նյութը մշակված է՝',
        'chunks. No model training performed.': 'հատված։ Մոդելի ուսուցում չի կատարվել։',
        'Open a diagnostic session before exporting a report.': 'Հաշվետվությունն արտահանելուց առաջ բացեք ախտորոշիչ '
                                                                'սեսիան։',
        'Export diagnostic report': 'Արտահանել ախտորոշման հաշվետվությունը',
        'Diagnostic report exported': 'Ախտորոշման հաշվետվությունն արտահանվեց',
        'Diagnostic report': 'Ախտորոշման հաշվետվություն',
        'Hypotheses require test confirmation.': 'Վարկածները պահանջում են թեստով հաստատում։',
        'Select a recommended test to view prerequisites and safety notes': 'Նախապայմաններն ու անվտանգության նշումները '
                                                                            'տեսնելու համար ընտրեք առաջարկվող թեստը',
        'risk=': 'ռիսկ=',
        'LOW': 'ՑԱԾՐ',
        'MEDIUM': 'ՄԻՋԻՆ',
        'HIGH': 'ԲԱՐՁՐ',
        'CREATED': 'ՍՏԵՂԾՎԱԾ',
        'COLLECTING': 'ՏՎՅԱԼՆԵՐԻ ՀԱՎԱՔԱԳՐՈՒՄ',
        'ANALYZING': 'ՎԵՐԼՈՒԾՈՒԹՅՈՒՆ',
        'READY': 'ՊԱՏՐԱՍՏ',
        'WAITING_FOR_TEST': 'ՍՊԱՍՈՒՄ Է ԹԵՍՏԻՆ',
        'COMPLETED': 'ԱՎԱՐՏՎԱԾ',
        'CONFIRMED': 'ՀԱՍՏԱՏՎԱԾ',
        'REJECTED': 'ՄԵՐԺՎԱԾ',
        'REPORTED': 'ՀԱՂՈՐԴՎԱԾ',
        'MEASURED': 'ՉԱՓՎԱԾ',
        'CALCULATED': 'ՀԱՇՎԱՐԿՎԱԾ',
        'INFERRED': 'ԵՆԹԱԴՐՎԱԾ',
        'Petrol': 'Բենզին',
        'Diesel': 'Դիզել',
        'Select a vehicle first.': 'Նախ ընտրեք մեքենան։',
        'Reconnect the backend before editing the active session vehicle.': 'Ընթացիկ սեսիայի մեքենան խմբագրելուց առաջ '
                                                                            'վերականգնեք սերվերի կապը։',
        'Live-data refresh failed:': 'Տվյալների թարմացումը ձախողվեց՝',
        'No active session.': 'Ակտիվ սեսիա չկա։',
        'Connected': 'Միացված է',
        'Disconnected': 'Անջատված է',
        'Simulator': 'Սիմուլյատոր',
        'No data': 'Տվյալներ չկան'},
 'ru': {'SMART DIAGNOSTICS  •  AI ANALYSIS  •  BETTER DRIVING': 'УМНАЯ ДИАГНОСТИКА  •  ИИ-АНАЛИЗ  •  БЕЗОПАСНОЕ '
                                                                'ВОЖДЕНИЕ',
        '+ Add widget': '+ Добавить виджет',
        'No samples': 'Нет данных',
        'Telemetry channel': 'Канал телеметрии',
        'Coolant temperature': 'Температура охлаждающей жидкости',
        'MAP pressure': 'Давление MAP',
        'O2 sensor': 'Датчик O2',
        'Select a vehicle': 'Выберите автомобиль',
        'Select vehicle': 'Выбрать автомобиль',
        'Choose your model to begin a diagnostic session': 'Выберите модель для начала диагностики',
        'No acquisition running': 'Сбор данных не запущен',
        'Open live channels': 'Открыть каналы данных',
        'No recommended tests yet': 'Рекомендованных тестов пока нет',
        'tests completed': 'тестов завершено',
        'INCOMPLETE results remain open': 'Незавершённые результаты остаются открытыми',
        'Reported codes are evidence, not a confirmed component failure.': 'Записанные коды — данные, а не '
                                                                           'подтверждение неисправности детали.',
        'Add symptoms / DTC': 'Добавить симптомы / DTC',
        'No description supplied': 'Описание отсутствует',
        'Source:': 'Источник:',
        'No DTCs recorded in the current session': 'В текущем сеансе нет кодов DTC',
        'AI hypotheses': 'Гипотезы ИИ',
        'Evidence-based hypotheses • Scores are not failure probabilities': 'Гипотезы на основе данных • Оценки не '
                                                                            'являются вероятностью отказа',
        'evidence score': 'оценка данных',
        'Hypothesis': 'Гипотеза',
        'unconfirmed': 'не подтверждено',
        'Recommended tests': 'Рекомендованные тесты',
        'Add evidence and analyze the session to generate hypotheses': 'Добавьте данные и выполните анализ для '
                                                                       'получения гипотез',
        'Missing evidence and questions will appear here': 'Здесь появятся недостающие данные и вопросы',
        'Export the current diagnostic record or reopen a backend session.': 'Экспортируйте текущую диагностику или '
                                                                             'откройте сохранённый сеанс.',
        'results': 'результатов',
        'Record an observed repair and its evidence. Ingestion adds reference material; it does not train the model or confirm a diagnosis.': 'Запишите '
                                                                                                                                              'выполненный '
                                                                                                                                              'ремонт '
                                                                                                                                              'и '
                                                                                                                                              'его '
                                                                                                                                              'данные. '
                                                                                                                                              'Добавление '
                                                                                                                                              'материала '
                                                                                                                                              'не '
                                                                                                                                              'обучает '
                                                                                                                                              'модель '
                                                                                                                                              'и '
                                                                                                                                              'не '
                                                                                                                                              'подтверждает '
                                                                                                                                              'диагноз.',
        'Vehicle, DTCs, measurements, repair, and verified outcome…': 'Автомобиль, коды DTC, измерения, ремонт и '
                                                                      'проверенный результат…',
        'Drafts stay on this device until you choose to ingest them.': 'Черновики остаются на устройстве до добавления '
                                                                       'в базу.',
        'Draft saved on this device': 'Черновик сохранён на устройстве',
        'Add a title and observed repair details first.': 'Сначала добавьте название и сведения о ремонте.',
        'Reference processed:': 'Материал обработан:',
        'chunks. No model training performed.': 'фрагментов. Обучение модели не проводилось.',
        'Open a diagnostic session before exporting a report.': 'Перед экспортом отчёта откройте диагностический '
                                                                'сеанс.',
        'Export diagnostic report': 'Экспорт диагностического отчёта',
        'Diagnostic report exported': 'Диагностический отчёт экспортирован',
        'Diagnostic report': 'Диагностический отчёт',
        'Hypotheses require test confirmation.': 'Гипотезы требуют подтверждения тестами.',
        'Select a recommended test to view prerequisites and safety notes': 'Выберите рекомендованный тест для '
                                                                            'просмотра условий и мер безопасности',
        'risk=': 'риск=',
        'LOW': 'НИЗКИЙ',
        'MEDIUM': 'СРЕДНИЙ',
        'HIGH': 'ВЫСОКИЙ',
        'CREATED': 'СОЗДАН',
        'COLLECTING': 'СБОР ДАННЫХ',
        'ANALYZING': 'АНАЛИЗ',
        'READY': 'ГОТОВО',
        'WAITING_FOR_TEST': 'ОЖИДАНИЕ ТЕСТА',
        'COMPLETED': 'ЗАВЕРШЕНО',
        'CONFIRMED': 'ПОДТВЕРЖДЕНО',
        'REJECTED': 'ОТКЛОНЕНО',
        'REPORTED': 'СООБЩЕНО',
        'MEASURED': 'ИЗМЕРЕНО',
        'CALCULATED': 'РАССЧИТАНО',
        'INFERRED': 'ПРЕДПОЛОЖЕНО',
        'Petrol': 'Бензин',
        'Diesel': 'Дизель',
        'Select a vehicle first.': 'Сначала выберите автомобиль.',
        'Reconnect the backend before editing the active session vehicle.': 'Перед изменением автомобиля активного '
                                                                            'сеанса восстановите связь с сервером.',
        'Live-data refresh failed:': 'Ошибка обновления данных:',
        'No active session.': 'Нет активного сеанса.',
        'Connected': 'Подключено',
        'Disconnected': 'Отключено',
        'Simulator': 'Симулятор',
        'No data': 'Нет данных'}}

MESSAGES["hy"].update({"STOPPED": "ԿԱՆԳՆԵՑՎԱԾ", "No acquisition samples": "Հավաքագրված տվյալներ չկան", "BLE TX characteristic UUID": "BLE ուղարկման բնութագրիչի UUID", "BLE RX characteristic UUID": "BLE ընդունման բնութագրիչի UUID"})
MESSAGES["ru"].update({"STOPPED": "ОСТАНОВЛЕНО", "No acquisition samples": "Нет собранных данных", "BLE TX characteristic UUID": "UUID характеристики передачи BLE", "BLE RX characteristic UUID": "UUID характеристики приёма BLE"})

MESSAGES['hy'].update({'CLOSED': 'ՓԱԿՎԱԾ Է',
 'DATABASE': 'Տվյալների բազա',
 'DATA_COLLECTION': 'ՏՎՅԱԼՆԵՐԻ ՀԱՎԱՔԱԳՐՈՒՄ',
 'ECU_REPORTED': 'ECU-ի հաղորդած',
 'HISTORICAL_CASE': 'Նախորդ դեպք',
 'HYPOTHESIS_VALIDATION': 'ՎԱՐԿԱԾՆԵՐԻ ՍՏՈՒԳՈՒՄ',
 'INITIAL_ANALYSIS': 'ՍԿԶԲՆԱԿԱՆ ՎԵՐԼՈՒԾՈՒԹՅՈՒՆ',
 'LLM_INFERENCE': 'Լեզվային մոդելի եզրակացություն',
 'ML_MODEL': 'Մեքենայական ուսուցման մոդել',
 'OEM_DOCUMENT': 'Արտադրողի փաստաթուղթ',
 'POST_REPAIR_VERIFICATION': 'ՎԵՐԱՆՈՐՈԳՈՒՄԻՑ ՀԵՏՈ ՍՏՈՒԳՈՒՄ',
 'QUESTIONS_PENDING': 'ՍՊԱՍՎՈՒՄ ԵՆ ՃՇՏՈՒՄՆԵՐ',
 'REPAIR': 'ՎԵՐԱՆՈՐՈԳՈՒՄ',
 'ROOT_CAUSE_FOUND': 'ՊԱՏՃԱՌԸ ԳՏՆՎԱԾ Է',
 'RULE': 'Կանոնային վերլուծություն',
 'SYMPTOMS_COLLECTED': 'ԱԽՏԱՆՇԱՆՆԵՐԸ ՀԱՎԱՔՎԱԾ ԵՆ',
 'TECHNICIAN_OBSERVED': 'Տեխնիկի դիտարկում',
 'TESTING': 'ԹԵՍՏԱՎՈՐՈՒՄ',
 'USER_REPORTED': 'Օգտատիրոջ հաղորդած',
 'VEHICLE_IDENTIFIED': 'ՄԵՔԵՆԱՆ ՆՈՒՅՆԱԿԱՆԱՑՎԱԾ Է',
 'VEHICLE_MEASURED': 'Մեքենայի չափում'})

MESSAGES['ru'].update({'CLOSED': 'ЗАКРЫТО',
 'DATABASE': 'База данных',
 'DATA_COLLECTION': 'СБОР ДАННЫХ',
 'ECU_REPORTED': 'Сообщено ЭБУ',
 'HISTORICAL_CASE': 'Предыдущий случай',
 'HYPOTHESIS_VALIDATION': 'ПРОВЕРКА ГИПОТЕЗ',
 'INITIAL_ANALYSIS': 'ПЕРВИЧНЫЙ АНАЛИЗ',
 'LLM_INFERENCE': 'Вывод языковой модели',
 'ML_MODEL': 'Модель машинного обучения',
 'OEM_DOCUMENT': 'Документ производителя',
 'POST_REPAIR_VERIFICATION': 'ПРОВЕРКА ПОСЛЕ РЕМОНТА',
 'QUESTIONS_PENDING': 'ОЖИДАЮТСЯ УТОЧНЕНИЯ',
 'REPAIR': 'РЕМОНТ',
 'ROOT_CAUSE_FOUND': 'ПРИЧИНА НАЙДЕНА',
 'RULE': 'Анализ по правилам',
 'SYMPTOMS_COLLECTED': 'СИМПТОМЫ СОБРАНЫ',
 'TECHNICIAN_OBSERVED': 'Наблюдение механика',
 'TESTING': 'ТЕСТИРОВАНИЕ',
 'USER_REPORTED': 'Сообщено пользователем',
 'VEHICLE_IDENTIFIED': 'АВТОМОБИЛЬ ИДЕНТИФИЦИРОВАН',
 'VEHICLE_MEASURED': 'Измерено автомобилем'})

MESSAGES["hy"].update({"VCI devices:": "VCI սարքեր՝", "Simulator acquisition started": "Սիմուլյատորի տվյալների հավաքումը սկսվել է", "Acquisition stopped": "Տվյալների հավաքումը կանգնեցված է", "Stopping background requests before closing...": "Փակելուց առաջ ֆոնային հարցումները դադարեցվում են…"})
MESSAGES["ru"].update({"VCI devices:": "Устройства VCI:", "Simulator acquisition started": "Сбор данных симулятора запущен", "Acquisition stopped": "Сбор данных остановлен", "Stopping background requests before closing...": "Остановка фоновых запросов перед закрытием…"})

MESSAGES["hy"].update({"DISCONNECTED": "ԱՆՋԱՏՎԱԾ", "CONNECTED": "ՄԻԱՑՎԱԾ", "CONNECTING": "ՄԻԱՑՈՒՄ", "SCANNING": "ՈՐՈՆՈՒՄ"})
MESSAGES["ru"].update({"DISCONNECTED": "ОТКЛЮЧЕНО", "CONNECTED": "ПОДКЛЮЧЕНО", "CONNECTING": "ПОДКЛЮЧЕНИЕ", "SCANNING": "ПОИСК"})


MESSAGES["hy"].update({
    "Backend recovered": "Սերվերի կապը վերականգնվել է",
    "Acquisition not started": "Տվյալների հավաքումը չի սկսվել",
    "Acquisition unavailable": "Տվյալների հավաքումը հասանելի չէ",
    "Session not found": "Սեսիան չի գտնվել",
})
MESSAGES["ru"].update({
    "Backend recovered": "Соединение с сервером восстановлено",
    "Acquisition not started": "Сбор данных не запущен",
    "Acquisition unavailable": "Сбор данных недоступен",
    "Session not found": "Сессия не найдена",
})
