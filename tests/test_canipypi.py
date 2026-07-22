from canipypi import check_name, ultranormalize


def test_name_checks():
    assert ultranormalize('Bloom_Filter') == 'b100mf11ter'

    projects = ['Friendly_Bard', 'BloomFilter']

    result = check_name('-bad', projects)
    assert not result.available and result.reason == 'invalid'

    result = check_name('asyncio', projects)
    assert not result.available and result.reason == 'stdlib'

    result = check_name('friendly.bard', projects)
    assert not result.available and result.reason == 'existing' and result.conflict == 'Friendly_Bard'

    result = check_name('bloom-filter', projects)
    assert not result.available and result.reason == 'similar' and result.conflict == 'BloomFilter'

    result = check_name('fresh-name', projects)
    assert result.available and result.reason is None and result.conflict is None
