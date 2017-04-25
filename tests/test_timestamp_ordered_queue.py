import mock

from kyber.logs import TimestampOrderedQueue, parse_logentry


def test_timestamp_ordered_queue_uses_count_to_tiebreak():
    toq = TimestampOrderedQueue()
    toq.put('pod', '1970-01-01 entry one')      # priority = epoch(1970-01-01) = 0   [1]
    toq.put('pod', '1970-01-02 entry three')    # priority = epoch(1970-01-02) = > 0 [3]
    toq.put('pod', '1970-01-01 entry two')      # priority = epoch(1970-01-01) = 0   [2]
    priority_1, index_1, string_1 = toq.get_raw()
    priority_2, index_2, string_2 = toq.get_raw()
    priority_3, index_3, string_3 = toq.get_raw()

    assert string_1 == 'pod: entry one'
    assert string_2 == 'pod: entry two'
    assert string_3 == 'pod: entry three'

    assert priority_1 == priority_2
    assert index_2 > index_1


def test_timestamp_ordered_queue_empty():
    toq = TimestampOrderedQueue()
    assert toq.empty is True
    toq.put(0, 'test')
    assert toq.empty is False
    toq.get()
    assert toq.empty is True


def test_parse_logentry():
    timestamp = '1970-01-01T00:00:00Z'
    log_string = '[mock system] mock log entry'
    log_entry = '{} {}'.format(timestamp, log_string)
    ts, string = parse_logentry(log_entry)
    assert string == log_string
    assert ts == 0.0


def test_timestamp_ordered_queue_calls_parse_logentry():
    toq = TimestampOrderedQueue()
    with mock.patch('kyber.logs.parse_logentry') as mock_parse_logentry:
        mock_parse_logentry.return_value = [0, 'test']
        toq.put('mockpod', 'hello')
    assert mock_parse_logentry.called is True
    assert toq.get() == 'mockpod: test'


def test_timestamp_ordered_queue_with_two_timestamps():
    timestamp1 = '1970-01-01T00:00:00Z'
    timestamp2 = '1970-01-01T00:00:01Z'
    toq = TimestampOrderedQueue()
    toq.put('mockpod', '{} mock younger'.format(timestamp2))
    toq.put('mockpod', '{} mock older'.format(timestamp1))
    assert toq.get() == 'mockpod: mock older'


def test_timestamp_ordered_queue_with_keep_timestamp():
    timestamp = '1970-01-01T00:00:00Z'
    toq = TimestampOrderedQueue(keep_timestamp=True)
    toq.put('mockpod', '{} mock'.format(timestamp))
    assert toq.get() == 'mockpod: {} mock'.format(timestamp)


def test_timestamp_ordered_queue_verbose_calls_click_echo_on_timestamp_parse_error():
    toq = TimestampOrderedQueue(verbose=True)
    with mock.patch('kyber.logs.click.echo') as mock_echo:
        toq.put('mockpod', 'meh mock')
        assert mock_echo.called
        assert toq.get() == 'mockpod: meh mock'
