"""테스트 부트스트랩.

app(=engine)이 import되기 전에 DATABASE_URL을 실행마다 새로운 임시 파일로
덮어, 테스트 파일들이 운영용 warm_haven.db나 서로의 데이터를 공유하지 않게 한다.
unittest discover는 테스트 모듈을 import하기 전에 이 패키지 __init__을 먼저
실행하므로 여기서 환경 변수를 설정하면 settings/engine 생성보다 앞선다.
"""

import atexit
import os
import tempfile

_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="warm_haven_test_")
os.close(_fd)

# SQLAlchemy SQLite URL은 슬래시를 쓴다(Windows 백슬래시 회피).
os.environ["DATABASE_URL"] = "sqlite:///" + _db_path.replace("\\", "/")
# 테스트는 항상 dev 토큰 경로로 단독 검증한다.
os.environ.setdefault("USE_FIREBASE_AUTH", "false")


@atexit.register
def _cleanup_test_db() -> None:
    try:
        os.remove(_db_path)
    except OSError:
        pass
