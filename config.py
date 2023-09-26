train = "ktx"

srt_user_id = "1234567890"          # SRT 회원번호
srt_user_pw = "abc1234"             # SRT 비밀번호
ktx_user_id = "1234567890"          # KTX 회원번호
ktx_user_pw = "abc1234"             # KTX 비밀번호
dpt_stn = "울산(통도사)"                 # 출발역
arr_stn = "서울"               # 도착역
dpt_date = "20230927"           # 출발일
dpt_time = "14"                 # 출발 검색 시간 "08, 10, 12, ..."

from_idx = 2                    # 검색했을 때 예약할 열차 순번 시작 (1부터 시작)
to_idx = 6                      # 검색했을 때 예약할 열차 순번 끝 (1부터 시작)

adult_cnt = 1                   # 성인 숫자
child_cnt = 0                   # 어린이 숫자
old_cnt = 0                     # 노인 숫자

business = False                 # 특실 예약 여부
economy = True                  # 일반실 예약 여부
reserve = True                  # 예약 대기 여부

phoneNoMid = ''
phoneNoEnd = ''

# 예약 성공 여부 텔레그램 수신 시 아래 정보 필요
telegram_token = "" #"123456789:SDBn-Kn2fdze1eEAL7fefawa1yLo0pjRAUc"
telegram_id = "" #"123548689"