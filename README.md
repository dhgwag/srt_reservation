# Python program for booking SRT ticket.


매진된 SRT 표의 예매를 도와주는 파이썬 프로그램입니다.  
원하는 표가 나올 때 까지 새로고침하여 예약을 시도합니다.


## 다운
```cmd
git clone https://github.com/dhgwag/srt_reservation.git
```
  
## 필요
- 파이썬 3.7, 3.9에서 테스트 했습니다.

```py
pip install -r requirements.txt
```


## Configuration
**Config.py를 항목에 맞춰 변경**  
```text
user_id = "1234567890"          # SRT 회원번호
user_pw = "abc1234"             # SRT 비밀번호
dpt_stn = "동탄"                 # 출발역
arr_stn = "동대구"               # 도착역
dpt_date = "20221023"           # 출발일
dpt_time = "08"                 # 출발 검색 시간 "08, 10, 12, ..."

from_idx = 2                    # 검색했을 때 예약할 열차 순번 시작 (1부터 시작)
to_idx = 3                      # 검색했을 때 예약할 열차 순번 끝 (1부터 시작)
# 예를 들어, from_idx가 1, to_idx가 1이면 검색 시 제일 윗 열차만 예약 시도

adult_cnt = 1                   # 성인 숫자
child_cnt = 0                   # 어린이 숫자
old_cnt = 0                     # 노인 숫자

business = True                 # 특실 예약 여부
economy = True                  # 일반실 예약 여부
reserve = True                  # 예약 대기 여부

phoneNoMid = '1234'             # 휴대폰 가운데 네자리
phoneNoEnd = '5678'             # 휴대폰 뒷 네자리

# 예약 성공 여부 텔레그램 수신 시 아래 정보 필요, 비워두면 텔레그램 무시
telegram_token = "" #"123456789:SDBn-Kn2fdze1eEAL7fefawa1yLo0pjRAUc"
telegram_id = "" #"123548689"
```


**Telegram으로 예약 완료시 알림 받기**
token과 id는 아래 링크 참조하여 생성

https://gabrielkim.tistory.com/entry/Telegram-Bot-Token-%EB%B0%8F-Chat-Id-%EC%96%BB%EA%B8%B0

## 간단 사용법

```cmd
python quickstart.py
```


**실행 결과**

![](./img/img1.png)

## 기타  
명절 승차권 예약에는 사용이 불가합니다.  