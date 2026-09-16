# 펫딜 엔진 (1호 카테고리: 반려동물 소모품)

수집(네이버 쇼핑 API) → 장당·kg당·100g당 단위가 환산 → 90일 최저가 판정 → 텔레그램 발송 → 사이트(index.html) 생성

## 구조
```
config.yaml            키워드·규칙·API 키(환경변수)
run.py                 실행 진입점 (cron 4회/일)
petdeal/
  collector.py         네이버 쇼핑 검색 API 수집 / DemoCollector(샘플)
  normalizer.py        상품명 → 중량·개수·단백질g → 단위가
  judge.py             90일 최저가 -15% / 단위가 하위 20% / 미끼·중복 차단
  affiliate.py         쿠팡 딥링크 API(승인 후) / 네이버 쇼핑커넥트 수동 CSV
  notify.py            텔레그램 / 콘솔 / 카카오(딜러사 계약 후 구현)
  publish.py           deals.json + site/index.html 생성
  db.py                SQLite (products / prices / alerts)
site/template.html     사이트 템플릿 (__DATA__ 치환)
data/                  sqlite, deals.json, channel.json, groupbuy.json, affiliate_links.csv
tests/                 make_sample.py(데모 데이터), test_normalizer.py
```

## 설치·실행
```
pip install requests pyyaml
python tests/make_sample.py        # 데모 데이터 + 30일 이력 생성
python run.py --demo               # API 키 없이 전체 흐름 검증 → site/index.html
```

## 실운영 전환 체크리스트
1. 네이버 개발자센터 → 애플리케이션 등록 → 검색 API(쇼핑) → `NAVER_CLIENT_ID/SECRET` 환경변수
2. @BotFather 로 봇 생성 → `TELEGRAM_BOT_TOKEN`. 채널 개설 후 봇을 관리자로 추가 → `TELEGRAM_CHAT_ID=@채널ID`
3. `data/channel.json` 에 채널명·텔레그램·카카오 링크 입력
4. 쿠팡파트너스 가입 → 수동 링크 → 누적 15만 원 후 API 키 → `COUPANG_ACCESS_KEY/SECRET_KEY`
5. 네이버 쇼핑커넥트 가입 → 링크 수동 발급 → `data/affiliate_links.csv` (product_id,link)
6. cron: `0 6,12,18,0 * * * cd /srv/petdeal && python run.py >> logs/run.log`
7. `site/index.html` 을 정적 호스팅(Cloudflare Pages/GitHub Pages)에 배포 — 실행마다 자동 갱신
8. 공동구매 개시 전 통신판매업 신고 → `data/groupbuy.json` 갱신

## 운영 흐름
- 자동: 수집 → 판정 → 후보 최대 8건 텔레그램 발송 → 사이트 갱신
- 수동(하루 10분): 발송 결과 확인, 오판 상품 `rules` 조정, 브랜드 라벨 확인 시 `PROTEIN_RATIO` 교정
- 주 1회: deals.json 상위 10건으로 카카오 다이제스트 작성(딜러사 API 연동 전까지 수동 발송)

## 카테고리·단위가
| 카테고리 | 단위가 | 규칙B(단위가 랭킹) 적용 |
|---|---|---|
| pad 배변패드 | 원/장 (소·중·대형 태그) | O |
| litter 고양이 모래 | 원/kg 또는 원/L | O |
| wet 습식·캔·츄르 | 원/100g | O |
| treat 간식 | 원/100g | O |
| dog_dry / cat_dry 사료 | 원/kg (참고용) | X — 같은 제품 90일 최저가 하락만 알림 |
| supplement 영양제 | 원/정 · 원/100g | X |

## 판정 규칙 (config.rules)
| 키 | 기본 | 의미 |
|---|---|---|
| history_days | 90 | 최저가 비교 기간 |
| drop_threshold | 0.15 | 최저가 대비 하락률 |
| unit_price_percentile | 0.20 | 카테고리 내 단위가 하위 비율 |
| dedupe_days | 7 | 재알림 금지 |
| max_alerts_per_run | 8 | 회당 최대 발송 |
| min_price_krw | 5000 | 샘플·소분 상품 제외 |
| unit_rank_categories | pad,litter,wet,treat | 단위가 단독 근거 허용 카테고리 |

## 한계·주의
- 네이버 API는 리뷰수·유통기한 미제공 → 향후 상품 페이지 스크래핑으로 보강
- 사료는 등급(프리미엄/일반) 차이가 커서 kg당 단가 순위는 참고용. 딜 판정은 동일 SKU 이력만
- 사료 광고 표현: 건강 효능·수의사 추천 등 과장 표현 금지(사료관리법 개정, 2028 시행 예정). 채널 메시지는 가격·용량 사실만 기재
- 네이버 쇼핑커넥트는 자동화 링크 제재 → 수동 발급 유지
- 카카오 친구톡은 비즈니스 채널 심사 + 딜러사 계약 필요
