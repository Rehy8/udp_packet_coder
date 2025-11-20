"""server.py ."""

# import itertools
import socket

import hamming_module as hm

UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', UDP_PORT))

# Буфер для сбора 7 чередующихся пакетов (каждый пакет - это столбец блока)
received_interleaved_packets = []
total_packets_expected = 7

print(f'Сервер слушает порт {UDP_PORT}...')

i = 0
while True:
    data, addr = sock.recvfrom(1024)

    if data == b'stop':
        print('Клиент завершил коммуникацию.')
        break

    text = data.decode('utf-8')

    # Преобразованив список битов [0, 1, 0, 1, 1, 0, 0]
    packet_bits = [int(x) for x in text]
    received_interleaved_packets.append(packet_bits)

    i += 1
    print(
        f'Получен пакет №{i} ({len(packet_bits)} бит). '
        f'Длина буфера: {len(received_interleaved_packets)}'
    )

    # Как только собраны все 7 пакетов
    if i % total_packets_expected == 0:
        # ----------------------------------------------------
        # 1. Симуляция потери двух пакетов (стирания)
        # ----------------------------------------------------
        interleaved_data_with_loss, erasure_indices = hm.introduce_packet_loss(
            received_interleaved_packets
        )

        # ----------------------------------------------------
        # 2. Дечередование и восстановление стираний
        # ----------------------------------------------------

        # Получаем количество закодированных блоков (из длины первого пакета)
        # Ищем первый попавшийся пакет, который НЕ равен None
        valid_packet = next(
            pkt for pkt in interleaved_data_with_loss if pkt is not None
        )
        num_blocks = len(valid_packet)

        # Дечередование: блокируем данные обратно по 7 битов на блок.
        # Заметьте: если пакет потерян (None),
        #  его нужно учесть в блоке как стирание (None)
        encoded_blocks_with_erasures = [[] for _ in range(num_blocks)]

        for block_index in range(num_blocks):
            # Собираем закодированный блок из 7 пакетов
            for packet_index in range(total_packets_expected):  # 0 до 6
                packet = interleaved_data_with_loss[packet_index]
                if packet is None:
                    # Потерянный пакет -> стирание (None) в блоке
                    encoded_blocks_with_erasures[block_index].append(None)
                else:
                    # Извлекаем бит для этого блока из этого пакета
                    encoded_blocks_with_erasures[block_index].append(
                        packet[block_index]
                    )

        # Декодирование каждого блока
        decoded_sequence = []
        for block in encoded_blocks_with_erasures:
            # erasure_indices для decode_with_erasures
            #  - это позиции в 7-битном блоке
            # (индексы 0-6), которые соответствуют потерянным пакетам.

            decoded_block = hm.decode_with_erasures(block, erasure_indices)
            decoded_sequence.extend(decoded_block)

        # ----------------------------------------------------
        # 3. Вывод результата
        # ----------------------------------------------------

        print('\n--- Восстановление и декодирование ---')
        print(f'Количество исходных блоков (по 4 бита): {num_blocks}')
        print(
            'Восстановленная последовательность данных '
            f'({len(decoded_sequence)} бит):\n{decoded_sequence}'
        )
        print('--- Конец последовательности ---\n')

        # Сброс буфера для следующей последовательности
        received_interleaved_packets = []
        i = 0

sock.close()
