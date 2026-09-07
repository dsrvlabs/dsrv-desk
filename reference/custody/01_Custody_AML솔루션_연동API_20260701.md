# Custody <> AML 솔루션 연동 API (커스터디팀 AS-IS 자료 · 원문 보존)

- 출처: Notion `Custody > … > Custody <> AML 솔루션 연동 API` (https://app.notion.com/p/dsrv/Custody-AML-API-38f7fc3011a980c88891ed451319ea12)
- 페이지 최종 수정: 2026-07-01 · 레그테크플래닛 원문(API 인터페이스 정리) 기준일: 2026-06-03
- 수령: 2026-09-07 (Notion MCP fetch). 첨부 2건은 미수령 — ① API_인터페이스_정리_20260603.txt ② 코드모음.xlsx(국가 코드 제외 코드값)
- 성격: **사내 커스터디팀의 현행(AS-IS) 연동 사양**. 법령 근거가 아니라 사실 자료. 교환·중개 기획의 전제로 쓰기 전에 커스터디팀에 **현행 여부 재확인** 필요(2개월 경과).
- 아래는 Notion 본문을 표 구조 그대로 옮긴 것. 코드값·필드명은 원문 표기 유지. 서비스 키 값은 원문에도 플레이스홀더.

---

## 운영 형태
커스터디 AML 시스템은 **운영망(폐쇄망) 내부 서버**에서 구동되며, 레그테크플래닛으로부터 관련 프로그램(API, Backend, Frontend)의 **도커 이미지를 전달받아 적용·업데이트**하는 방식으로 운영. 도메인은 당사 제공.
아래는 레그테크플래닛 연동 · **Custody Admin 기준** · 전체 API 호출 시점 및 처리 흐름.

## 전체 흐름 요약
- ① 상품: 상품 생성 → `putProduct`
- ② 고객: 법인 고객 생성 → `putCustomer` → `getKycresultUnapproved` → AML 심사 → `/callback` 수신
- ③ 수정: 재이행 `kycReasonCode = 02` → `getKycresultUnapproved` / 주요정보변경 `kycReasonCode = 03` → `putCustomer`
- ④ 지갑: 지갑 생성 → `putAccount`
- ⑤ 거래: 자산 구분 CUSTOMER 승인 → `putSendReceipt` → `putTransaction` → `putAccount`(잔고 갱신)
- ⑥ 사고: 사고 등록(Admin) → `checkAccountTrouble`

## 공통 규약
별도 타입 표기가 없는 필드는 모두 문자열(string).

공통 Request
```json
{ "ServiceKey": "{AML_SERVICE_KEY}", "Parameter": { "canUpdate": "1" }, "Data": { } }
```
공통 Response
```json
{ "ResultCode": 0, "ResultMessage": "", "Data": { } }
```

---

## ① 상품 등록: putProduct — POST `/flow/putProduct`
신규 상품(Product) 생성 시 AML 솔루션에 취급 상품 정보 등록. **TOKEN 타입 상품 제외.** 호출 시점: 신규 상품 생성 시(자동).

| 필드 | 필수 | 설명 | 고정값/형식 |
|---|---|---|---|
| productId | 필수 | 상품 코드 | P0001 형식 |
| productName | 필수 | 상품명 | |
| openDate | 필수 | 등록일 | yyyymmdd |

## ② 고객 등록 & KYC

### putCustomer — POST `/flow/putCustomer`
신규 **법인** 고객 생성 시 고객 프로파일과 관련인(대표이사·대리인·실소유자) 정보를 등록. 호출 시점: 신규 법인 고객 생성 시(자동) / 고객 정보 수정 + `kycReasonCode = '03'`.

법인 기본정보

| 필드 | 필수 | 설명 | 고정값/형식 |
|---|---|---|---|
| kycReasonCd | | KYC 사유 코드 | 01 신규 / 02 재이행 / 03 주요정보변경 / 09 기타(기재) |
| customerNo | 필수 | 고객 식별번호 | L-XXXXXX-XXXX |
| customerCategorizeCd | 필수 | 고객 구분 | 01 개인고객 / 02 법인고객 |
| customerStatusCd | 필수 | 고객 상태 코드 | 01 신규 / 02 활성 / 03 휴면 / 04 거래중지 / 05 거래해지 / 06 거래거절 |
| refApiPath | 필수 | KYC 결과 수신 콜백 URL | Custody Admin API path |
| channelCd | | 채널 코드 | 01 대면 / 02 비대면 / 99 기타 |
| customerName / customerEnName | 필수 | 법인명(한글/영문) | |
| realNumber | 필수 | 사업자등록번호 | |
| realNumberCd | 필수 | 실명번호 구분 | 01 주민등록번호(개인) / 02 주민등록번호(기타단체) / 03 사업자등록번호 / 04 여권번호 / 05 법인등록번호 / 06 외국인등록번호 / 07 국내거소신고번호 / 08 투자등록번호 / 09 고유번호·납세번호 / 11 BIC코드(SWIFT) / 12 해당국가법인번호 / 14 CI번호 / 99 기타 |
| corporateRegNo | 필수 | 법인등록번호 | |
| establishDate | 필수 | 설립일 | |
| nationalityCd / residenceCountryCd | 필수 | 국적 / 거주국 코드 | |
| industry | | 업종 | |
| KSICCd | 필수 | 한국표준산업분류코드(11차) | |
| largePropertyYN | | 고액자산가 여부 | Y/N |
| headPostNo / headAddress(필수) / headAddressAdd(필수) / headEmail / headFax / headPhoneNo | | 본점 주소·연락처 | |
| branchPostNo / branchAddress / branchAddressAdd | | 지점 주소 | |
| homepage | | 홈페이지/이메일 | |
| businessScaleCd | 필수 | 기업 규모 | 01 대기업 / 02 중소기업 |
| listedYn | 필수 | 상장 여부 | Y/N |
| listedTypeCd / listedTypeEtc | | 상장 유형 | 01 유가증권 / 02 코스닥 / 03 NYSE / 04 NASDAQ / 05 LSE / 06 HKEX / 99 기타 |
| businessPurposeCd | 필수 | 거래 목적 | 01 급여·생활비 / 02 저축·투자 / 03 보험료 / 04 공과금 / 05 카드대금 / 06 대출상환 / 07 사업상거래 / 08 보장 / 09 상속 / **10 가상자산 운용 / 11 가상자산 위탁 및 보관** / 99 기타(기재) |
| businessPurposeEtc | | 거래 목적 기타 | |
| fundsSourceCd | 필수 | 자금 출처(배열) | 01 근로소득 / 02 연금 / 03 차용·대출 / 04 거래대금 / 05 매매대금 / 06 임대대금 / 07 사업소득 / 08 금융소득 / 09 투자자산 처분(가상자산·증권 등) / 10 부동산 임대·양도 / 99 기타(기재) |
| fundsSourceEtc | | 자금 출처 기타 | |
| corporationTypeCd | 필수 | 법인 유형 | 01 영리법인 / 02 금융기관 / 03 공공기관 / 04 국제간정부기구 / 05 비영리법인 / 06 대부업자 / 07 환전상 / 08 카지노사업자 / 09 가상자산사업자 / 10 시계·귀금속판매상 / 99 기타 |
| corporationTypeEtc | | 법인 유형 기타 | |
| annualRevenue | | 연간 매출 | |
| expectedTransactionAmountCd | | 예상 연간 거래 금액 | 01 1천만원 이하 / 02 5천만원 이하 / 03 1억원 이하 / 04 1억원 초과 |
| expectedTransactionCountCd | | 예상 연간 거래 빈도 | 01 5회 미만 / 02 5~10회 미만 / 03 10~50회 미만 / 04 50회 이상 |
| mainProduct / employeeCount | | 주요 상품·서비스 / 임직원 수 | |
| relatedPersonList | | 관련인 목록(REP/DEL/OWN) | 배열 |

관련인 공통 필드(REP 대표이사 · DEL 대리인 · OWN 실소유자)

| 필드 | 필수 | 설명 | 고정값/형식 |
|---|---|---|---|
| relatedCategorizeCd | 필수 | 관련인 구분 | 01 고객 / 02 대표자 / 03 실소유자 / 04 대리인 / 05 기타 |
| relationCd | 필수 | 관계 코드 | 51 대표이사 / 72 임직원 / 99 기타(기재) |
| customerName / customerEnName | 필수 | 성명 한글/영문 (DEL은 영문만 필수) | |
| nationalityCd / residenceCountryCd | 필수 | 국적 / 거주국 | |
| realNumberCd | 필수(OWN은 택1) | 실명번호 구분 | 위 코드표와 동일 |
| realNumber | REP·DEL 필수 | **실명번호(복호화 상태로 전송)** · OWN은 비움 또는 birthday | |
| birthday | | 생년월일(OWN, realNumber 대체) | |
| homePostNo / homeAddress / homeAddressAdd | | 주소 | |
| genderCd | | 성별 | 01 남 / 02 여 |
| cellPhoneNo(cellphoneNo) | | 휴대폰 | |
| companyName / deptName / companyNum | | (DEL) 직장명·부서·직장전화 | |
| ownershipRatio / ownerVerificationLevelCd | | (OWN) 지분율 / 확인 수준 | |
| ownerVerificationDocCd | | (OWN) 확인 서류 | 01 주주명부 / 02 주식변동사항명세서 / 03 금감원 전자공시 / 04 사업보고서 / 05 신용정보사 보고서 / 06 사원명부 / 07 이사회명부 / 08 정관 / 09 법인등기부등본 / 10 출자자명부 / 11 없음(거래불가) / 12 기타 |
| jobCd | 필수 | 직업 코드 | 01 급여소득자 / 02 개인사업자 / 03 연금소득자 / 04 주부 / 05 학생 / 06 무직 / 91 파악할 수 없음 |
| exceptionCheck / exceptionCheckList | | 예외 여부·목록 | REP·DEL: N · [] / OWN: Y · ['Valid','RA'] |

응답 예시: `{ "ResultCode": 0, "Data": { "kycResult": "CDD", "kycResultCd": "01" } }`

### getKycresultUnapproved — POST `/flow/getKycresultUnapproved` (putCustomer 성공 직후 연속 호출)
해당 고객의 KYC 심사 요청. putCustomer 전체 필드 + `productId`(심사 신청 상품 코드, P0001 형식). 응답 `kycResult: CDD / kycResultCd: 01` 형식.

### /callback — POST `/callback` (Custody Admin 구현)
AML 솔루션이 심사 완료 후 Custody Admin으로 비동기 콜백. `putCustomer`의 `refApiPath`에 이 경로 필수.
- 성공: `kycResult = 01, 02` → 고객 상태 **ACTIVE**
- 실패: `kycResult = 03` → 고객 상태 **REJECTED**

## ③ 지갑 등록: putAccount — POST `/flow/putAccount`
지갑을 AML 솔루션에 계좌로 등록하거나, 자산 구분 승인 시 잔고 갱신. 호출 시점 2가지: 1) 지갑 신규 등록 시(자동 — contract.controller.ts) 2) 자산 구분 CUSTOMER / DUST_TEST 승인 시 — putTransaction과 함께.

| 필드 | 필수 | 설명 | 고정값/형식 |
|---|---|---|---|
| accountNo | 필수 | 고객 지갑 주소 | |
| tag | | 태그 | none |
| network | | 체인 | ETH, BTC 등 |
| currency | 필수 | 자산 심볼 | |
| accountBalance | 필수 | 현재 잔고(토큰 수량) | |
| accountBalanceKrw | | 현재 잔고(원화) | |
| accountPreBalance | | 전일 잔고 | |
| accountRoleCd | 필수 | 계좌 역할 | 01 관련계좌 / 02 송·수취계좌 |
| accountRole | | 계좌 역할명 | 송수취계좌 |
| accountStateCd | 필수 | 계좌 상태 | 01 활성 / 02 휴면 / 03 해지 / 04 거래정지 |
| accountState | | 계좌 상태명 | 활성 |
| orgCode / orgName | | 기관 코드·명 | LS0038 / 주식회사 디에스알브이랩스 |
| branchOfficeCd / branchOffice / branchOfficePostNo | | 지점 | LS00046 |
| openDate | 필수 | 지갑 생성일 | yyyymmdd |
| closedDate | | 해지일 | null |
| registrationUserId | 필수 | 지갑 생성자 ID | |
| productId | 필수 | 상품 코드 | |

## ④ 입출금 거래 보고: putSendReceipt → putTransaction → putAccount
특정 트랜잭션을 고객 자산으로 반영할 때 **3개 API를 반드시 순서대로** 호출.

### putSendReceipt — POST `/flow/putSendReceipt`
거래 상대방(counterparty) 신원 정보 전송. 트래블룰로 수집된 IVMS101 정보가 있으면 함께 전송.

| 필드 | 필수 | 설명 | 형식 |
|---|---|---|---|
| transactionAccountNo | 필수 | 상대방 지갑 주소(입금 from / 출금 to) | |
| network / tag | | 체인 / 태그 | ETH, BTC / none |
| currency | 필수 | 자산 심볼 | |
| customerCategorizeCd | 필수 | 고객구분 | 01 개인 / 02 법인 |
| customerName | 필수 | 상대방 이름(IVMS101 성명 또는 **화이트리스트 레이블**) | |
| customerEnName / realNumberCd / realNumber / nationalityCd / nationality / residenceCountryCd / residenceCountry / residenceYN | | 상대방 신원 | |
| homePostNo / homeAddress / homeAddressAdd / birthday / genderCd / homePhoneNo / cellPhoneNo | | 상대방 연락·주소 | |

### putTransaction — POST `/flow/putTransaction`
입출금 거래 내역 보고.

| 필드 | 필수 | 설명 | 고정값/형식 |
|---|---|---|---|
| seq | 필수 | 거래 고유번호 | yyyymmdd-0000000001 |
| date / time | 필수 | 거래 일자 / 시각 | yyyy-MM-dd / HHmmss |
| customerNo | 필수 | 고객 식별번호 | |
| accountNo | 필수 | 고객 지갑 주소 | |
| transactionTypeCd | 필수 | 거래 유형 | **01 입금 / 02 출금** |
| channelCd / channel | 필수/ | 채널 | 99 / 기타 |
| meanCd / mean | | 거래 수단 | 13 / 가상자산 |
| methodName | 필수 | 거래 방법명 | **가상자산 입고 / 가상자산 출고** |
| moneyTypeCd / moneyType | 필수/ | 자산 유형 | DIG / 가상자산 |
| moneyTypeEtc | 필수 | 자산 심볼 | ETH, BTC 등 |
| krwAmount | 필수 | **원화 환산 금액** | |
| usdAmount | | 달러 환산 금액 | |
| orgCode | | 기관 코드 | LS0038 |
| tokenAmount | 필수 | 토큰 수량 | |
| tag / network(필수) / vout | | | none / / '' |
| txHash | 필수 | 트랜잭션 해시 | |
| usdKrwRate | | USD/KRW 환율 | '' |
| transactionAccountNo | 필수 | 상대방 주소(출금 to / 입금 from) | |
| currency | 필수 | 자산 심볼 | |

### putAccount (거래 이후 잔고 갱신)
거래 이후 고객 지갑 현재 잔고 동기화. 파라미터는 ③과 동일.

## ⑤ 사고 처리: checkAccountTrouble — POST `/flow/checkAccountTrouble`
Admin에서 사고(Accident) 등록 처리 시, **압류·동결** 등 사고 처리된 지갑 정보 보고.

| 필드 | 필수 | 설명 |
|---|---|---|
| customerNo | 필수 | 고객 식별번호 |
| accountNo | 필수 | 지갑 주소 |
| startDate | 필수 | 거래 제한 시작일 |
| endDate | | 거래 제한 종료일 |
| customerName | | 고객명 |
| network / currency | 필수 | 체인 / 자산 심볼 |
| tag | | none |

ResultCode 0 → 사고 계좌 AML 보고 완료, 해당 지갑 거래 제한 적용.
