# COOS 커뮤니티 데일리 다이제스트

`https://coos.kr/community` 첫 페이지에서 당일 게시글(날짜 셀이 `hh:mm`)만 추출해 Gmail SMTP로 텍스트 메일을 발송합니다. GitHub Actions가 매일 11:59 KST(02:59 UTC)에 자동 실행됩니다.

## 환경변수
로컬 `.env` 또는 GitHub Secrets에 다음을 설정하세요.

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=masonchoi1013@gmail.com
SMTP_PASS=<Gmail 앱 비밀번호>
MAIL_FROM=masonchoi1013@gmail.com
MAIL_TO=mason.choi@evonik.com
USE_PLAYWRIGHT=false
```

Playwright가 필요할 때만 `USE_PLAYWRIGHT=true`로 설정하면 렌더링 후 파싱합니다.

## 로컬 실행
```bash
pip install -r requirements.txt
python scripts/send_coos_digest.py           # requests 기반
# 필요시
python scripts/send_coos_digest.py --use-playwright
```

## GitHub Actions
`.github/workflows/coos-digest.yml`가 매일 02:59 UTC에 실행됩니다. 위 환경변수를 Secrets로 등록하면 자동으로 메일을 발송합니다.
