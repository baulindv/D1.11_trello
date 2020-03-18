import sys
import requests
from collections import Counter

# Данные авторизации в API Trello  
auth_params = {
    'key': "",
    'token': "", }

board_id = ''

# Адрес, на котором расположен API Trello, # Именно туда мы будем отправлять HTTP запросы.  
base_url = "https://api.trello.com/1/{}"

global_column_data = None


# Получает данные всех колонок на доске
def get_column_data():
    global global_column_data
    if global_column_data is None:
        global_column_data = requests.get(base_url.format('boards') + '/' + board_id + '/lists', params=auth_params).json()
    return global_column_data


# Создать колонку
def create_list(name):
    # Определить longID идентификатор доски
    board_data = requests.get(base_url.format('boards') + '/' + board_id, params=auth_params).json()
    board_longID = board_data['id']

    a = requests.post(base_url.format('lists'), data={'name': name, 'idBoard': board_longID, **auth_params})
    if a.status_code == 200:
        print(f'Колонка с названием "{name}" создана.')
    else:
        print(f'Ошибка: {a.status_code, a.text}')


def read():
    # Получим данные всех колонок на доске:
    column_data = get_column_data()
    # Теперь выведем название каждой колонки и всех заданий, которые к ней относятся:
    for column in column_data:
        print(column['name'], end=' ')
        # Получим данные всех задач в колонке и перечислим все названия
        task_data = requests.get(base_url.format('lists') + '/' + column['id'] + '/cards', params=auth_params).json()
        # Количество заданий в колонке
        print(f'({len(task_data)})')

        if not task_data:
            print('\t' + 'Нет задач!')
            continue
        for task in task_data:
            print('\t' + task['name'])


# Ищет дубликаты задач по всех колонках
def find_dubl():
    column_data = get_column_data()
    # Словарь id - имя колонки
    columns_dict = {}
    # Список всех задач и колонок, в которых они находятся
    tasks_list_all = []
    # Итоговый список дублирующихся задач и колонок, в которых они находятся
    tasks_dubl = []
    # Список для подсчёта вхождений каждой задачи
    tasks_count = []
    # Номер дубликата
    dubl_num = 1
    for column in column_data:
        columns_dict[column['id']] = column['name']
        task_data = requests.get(base_url.format('lists') + '/' + column['id'] + '/cards', params=auth_params).json()

        for task in task_data:
            tasks_list_all.append([dubl_num, task['id'], task['name'], columns_dict[task['idList']]])
            tasks_count.append(task['name'])
            dubl_num += 1

    tasks_count = Counter(tasks_count)
    tasks_count = dict(tasks_count)
    for key, val in tasks_count.items():
        if val > 1:
            for i in tasks_list_all:
                if key == i[2]:
                    tasks_dubl.append(i)

    return tasks_dubl


def create(name, column_name):
    # Получим данные всех колонок на доске
    column_data = get_column_data()

    # Переберём данные обо всех колонках, пока не найдём ту колонку, которая нам нужна
    for column in column_data:
        if column['name'] == column_name:
            # Создадим задачу с именем _name_ в найденной колонке
            requests.post(base_url.format('cards'), data={'name': name, 'idList': column['id'], **auth_params})
            print(f'Создана задача "{name}" в колонке "{column_name}".')
            break


def move(name, column_name):
    # Получим данные всех колонок на доске
    column_data = get_column_data()
    # Среди всех колонок нужно найти задачу(и) по имени и получить её id
    task_ids = []
    for column in column_data:
        column_tasks = requests.get(base_url.format('lists') + '/' + column['id'] + '/cards', params=auth_params).json()
        for task in column_tasks:
            if task['name'] == name:
                task_ids.append(task['id'])

    if len(task_ids) == 0:
        print('Данной задачи не существует!')
        return

    # Есть ли дубликаты?
    if len(task_ids) > 1:
        dubl_exists = find_dubl()
        # Идентификаторы дубликатов для ограничения выбора
        valid_dubl_ids = []
        for dubl in dubl_exists:
            valid_dubl_ids.append(dubl[0])

        print('Найдены дублирующиеся имена задач. Необходимо выбрать одну для перемещения.')
        print('-' * 75)
        print('{: <20} {: <20} {: <20}'.format('Идентификатор', 'Задача', 'Местонахождение'))

        for dubl in dubl_exists:
            if name == dubl[2]:
                print('{: <20} {: <20} {: <20}'.format(dubl[0], dubl[2], dubl[3]))

        print('-' * 75)
        while True:
            dubl_id = input('Введите идентификатор: ')
            try:
                dubl_id = int(dubl_id)
            except ValueError:
                print('Необходимо ввести число!')
            else:
                if dubl_id not in valid_dubl_ids:
                    print('Неверный идентификатор!')
                else:
                    for i in dubl_exists:
                        if dubl_id == i[0]:
                            task_id = i[1]
                    break
    else:
        task_id = task_ids[0]

    # Теперь, когда у нас есть id задачи, которую мы хотим переместить
    # Переберём данные обо всех колонках, пока не найдём ту, в которую мы будем перемещать задачу
    for column in column_data:
        if column['name'] == column_name:
            # И выполним запрос к API для перемещения задачи в нужную колонку
            requests.put(base_url.format('cards') + '/' + task_id + '/idList',
                         data={'value': column['id'], **auth_params})
            print('Задача перемещена')
            break


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        read()
    elif sys.argv[1] == 'create':
        create(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'move':
        move(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'create_list':
        create_list(sys.argv[2])
