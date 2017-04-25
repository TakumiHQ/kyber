import mock

from kyber.logs import TimestampOrderedQueue, parse_logentry


def test_timestamp_ordered_queue_uses_count_to_tiebreak():
    pq = TimestampOrderedQueue()
    pq.put('pod', '1970-01-01 entry one')      # priority = epoch(1970-01-01) = 0   [1]
    pq.put('pod', '1970-01-02 entry three')    # priority = epoch(1970-01-02) = > 0 [3]
    pq.put('pod', '1970-01-01 entry two')      # priority = epoch(1970-01-01) = 0   [2]
    priority_1, index_1, string_1 = pq.get_raw()
    priority_2, index_2, string_2 = pq.get_raw()
    priority_3, index_3, string_3 = pq.get_raw()

    assert string_1 == 'pod: entry one'
    assert string_2 == 'pod: entry two'
    assert string_3 == 'pod: entry three'

    assert priority_1 == priority_2
    assert index_2 > index_1


def test_timestamp_ordered_queue_empty():
    pq = TimestampOrderedQueue()
    assert pq.empty is True
    pq.put(0, 'test')
    assert pq.empty is False
    pq.get()
    assert pq.empty is True


def test_parse_logentry():
    timestamp = '1970-01-01T00:00:00Z'
    log_string = '[mock system] mock log entry'
    log_entry = '{} {}'.format(timestamp, log_string)
    ts, string = parse_logentry(log_entry)
    assert string == log_string
    assert ts == 0.0


def test_timestamp_ordered_queue_calls_parse_logentry():
    ol = TimestampOrderedQueue()
    with mock.patch('kyber.logs.parse_logentry') as mock_parse_logentry:
        mock_parse_logentry.return_value = [0, 'test']
        ol.put('mockpod', 'hello')
    assert mock_parse_logentry.called is True
    assert ol.get() == 'mockpod: test'


def test_timestamp_ordered_queue_with_two_timestamps():
    timestamp1 = '1970-01-01T00:00:00Z'
    timestamp2 = '1970-01-01T00:00:01Z'
    ol = TimestampOrderedQueue()
    ol.put('mockpod', '{} mock younger'.format(timestamp2))
    ol.put('mockpod', '{} mock older'.format(timestamp1))
    assert ol.get() == 'mockpod: mock older'


def test_timestamp_ordered_queue_with_keep_timestamp():
    timestamp = '1970-01-01T00:00:00Z'
    ol = TimestampOrderedQueue(keep_timestamp=True)
    ol.put('mockpod', '{} mock'.format(timestamp))
    assert ol.get() == 'mockpod: {} mock'.format(timestamp)


def test_timestamp_ordered_queue_verbose_calls_click_echo_on_timestamp_parse_error():
    ol = TimestampOrderedQueue(verbose=True)
    with mock.patch('kyber.logs.click.echo') as mock_echo:
        ol.put('mockpod', 'meh mock')
        assert mock_echo.called
        assert ol.get() == 'mockpod: meh mock'
