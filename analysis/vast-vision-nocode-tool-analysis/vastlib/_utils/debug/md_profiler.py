import cProfile
import pstats
import io
from datetime import datetime


def get_profile_data(profiler: cProfile.Profile, rank: int = 25) -> str:
    """関数ごとの処理時間の記録

    Args:
        profiler (cProfile.Profile): _description_
        rank (int, optional): _description_. Defaults to 25.

    Returns:
        str: _description_
    """
    buf = io.StringIO()
    sortby = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=buf)

    # NOTE: ソート処理
    ps.strip_dirs()
    ps.sort_stats(sortby)
    ps.print_stats(rank)
    # ps.strip_dirs().sort_stats(sortby).print_stats(rank)

    data = buf.getvalue()
    data = 'ncalls' + data.split('ncalls')[-1]
    data = '\n'.join([','.join(line.rstrip().split(None, 5)) for line in data.split('\n')])
    return data


def record_data(data: str) -> None:
    _now = datetime.now()
    filename = _now.strftime('%Y%m%d_%H%M%S')

    with open('./tact/' + filename + '.csv', 'w+') as f:
        # f=open(result.rsplit('.')[0]+'.csv','w')
        f.write(data)
        f.close()


if __name__ == '__main__':
    pr = cProfile.Profile()
    pr.enable()
    # ... do something ...
    pr.disable()
    data = get_profile_data(pr)
    record_data(data)
