import mock

from kyber.logs import PriorityQueue, OrderedLog, parse_logentry


def test_priority_queue_uses_count_to_tiebreak():
    pq = PriorityQueue()
    pq.push(0, 'test')
    pq.push(0, 'later test')
    assert pq.pop() == (0, 0, 'test')
    assert pq.pop() == (0, 1, 'later test')


def test_priority_queue_returns_lowest_priority():
    pq = PriorityQueue()
    pq.push(1, 'test')
    pq.push(0, 'later test')
    assert pq.pop() == (0, 1, 'later test')
    assert pq.pop() == (1, 0, 'test')


def test_priority_queue_empty():
    pq = PriorityQueue()
    assert pq.empty is True
    pq.push(0, 'test')
    assert pq.empty is False
    pq.pop()
    assert pq.empty is True


def test_parse_logentry():
    timestamp = '1970-01-01T00:00:00Z'
    log_string = '[mock system] mock log entry'
    log_entry = '{} {}'.format(timestamp, log_string)
    ts, string = parse_logentry(log_entry)
    assert string == log_string
    assert ts == 0.0


def test_ordered_log_stream_calls_parse_logentry():
    ol = OrderedLog()
    with mock.patch('kyber.logs.parse_logentry') as mock_parse_logentry:
        mock_parse_logentry.return_value = [0, 'test']
        ol.push('mockpod', 'hello')
    assert mock_parse_logentry.called is True
    assert ol.pop() == 'mockpod: test'


def test_ordered_log_stream_with_two_timestamps():
    timestamp1 = '1970-01-01T00:00:00Z'
    timestamp2 = '1970-01-01T00:00:01Z'
    ol = OrderedLog()
    ol.push('mockpod', '{} mock younger'.format(timestamp2))
    ol.push('mockpod', '{} mock older'.format(timestamp1))
    assert ol.pop() == 'mockpod: mock older'


def test_ordered_log_stream_with_keep_timestamp():
    timestamp = '1970-01-01T00:00:00Z'
    ol = OrderedLog(keep_timestamp=True)
    ol.push('mockpod', '{} mock'.format(timestamp))
    assert ol.pop() == 'mockpod: {} mock'.format(timestamp)


def test_ordered_log_stream_verbose_calls_click_echo_on_timestamp_parse_error():
    ol = OrderedLog(verbose=True)
    with mock.patch('kyber.logs.click.echo') as mock_echo:
        ol.push('mockpod', 'meh mock')
        assert mock_echo.called
        assert ol.pop() == 'mockpod: meh mock'