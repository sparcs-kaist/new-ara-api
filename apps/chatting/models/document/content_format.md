# 메시지 타입별 형식

모든 메시지는 `ChatMessage` 하나로 저장한다.
여러 사람이 상태를 바꾸는 타입(투표, 정산, 배달 주문)은 전용 테이블이 메시지를 1:1 로 가리키고,
메시지 조회 시 `attachment` 필드로 함께 내려간다.

`message_content` 는 사람이 읽는 텍스트다. (채팅방 목록 미리보기, 구버전 클라이언트용)

| 타입 | message_content | attachment | 만드는 곳 |
|---|---|---|---|
| TEXT | 본문 | - | `POST chat/message` |
| IMAGE / FILE | 파일 링크 | - | `POST chat/message` |
| EMOTICON | 이모티콘 | - | `POST chat/message` |
| VOTE | `[투표] 제목` | 투표 (`ChatVote`) | `POST chat/vote` |
| PAYMENT_REQUEST | `[정산 요청] 총 N원` | 정산 (`ChatPaymentRequest`) | `POST chat/payment`, 배달방은 `POST delivery/<id>/payment-request` |
| DELIVERY_ORDER | `[주문] 메뉴 · N원` (메뉴 없으면 `[주문] N원`) | 주문 (`DeliveryOrder`) | `POST delivery/<id>/orders` |
| DELIVERY_ARRIVAL | `배달이 도착했어요! 🛵` | - | `POST delivery/<id>/arrive` |
| SYSTEM | 안내 문구 (예: `익명2님이 참여했어요.`) | - | 서버만 (작성자 없음, 알림 없음) |

- VOTE, PAYMENT_REQUEST, DELIVERY_* 는 일반 메시지 API 로 만들거나 지울 수 없다.
- 메시지 수정은 TEXT 만 가능하다.
- DELIVERY_* 는 함께 배달 방(room_type=DELIVERY)에서만 쓸 수 있다.
- 계좌번호는 `message_content` 에 넣지 않는다 (미리보기, 푸시에 노출되지 않도록).

## 작성자 표시

메시지의 `sender` 에 채팅방 이름 표시 방식이 적용된 이름이 들어간다.

```json
{"display_name": "익명1", "anon_number": 1, "role": "PARTICIPANT", "is_mine": false}
```

- 익명 방: 방장은 `방장`, 나머지는 `익명N`. 번호는 처음 들어올 때 정해지고, 나갔다 다시 들어와도 유지된다.
- 익명 방에서는 `created_by` 가 `null` 이다. 내 메시지인지는 `sender.is_mine` 으로 판단한다.

## 투표 (VOTE)

```json
{
  "id": 1, "message_id": 10, "chat_room": 3, "title": "점심 뭐 먹지?",
  "max_choices": 2,
  "options": [
    {"id": 1, "text": "카이마루", "vote_count": 1, "voters": [{"display_name": "익명1", "...": "..."}]}
  ],
  "voter_count": 1,
  "my_option_ids": [1]
}
```

- `max_choices`: 1 이면 단일 선택, N 이면 최대 N 개, `null` 이면 제한 없음.
- 투표: `PUT chat/vote/<id>/ballot {"option_ids": [...]}` 로 내 선택 전체를 바꾼다. 빈 리스트면 취소.
- 지금은 누가 투표했는지와 결과가 항상 실시간으로 보인다.
  나중에 익명 투표, 결과 숨기기, 마감을 추가할 때는 `ChatVote` 에 필드를 추가하고 `can_see_voters` / `can_see_counts` 만 고치면 된다.

## 정산 요청 (PAYMENT_REQUEST)

```json
{
  "id": 1, "bank_name": "카카오뱅크", "account_number": "3333-01-1234567",
  "targets": [{"user": {"display_name": "익명1", "...": "..."}, "amount": 7000, "paid_at": null}],
  "total_amount": 7000, "is_settled": false
}
```

- 대상자마다 금액이 다를 수 있다.
- 대상자가 `PATCH chat/payment/<id>/paid {"paid": true}` 로 송금 완료를 누른다.

## 배달 주문 (DELIVERY_ORDER)

```json
{"id": 1, "message_id": 12, "party": 2, "orderer": {"display_name": "익명1", "...": "..."},
 "menu_name": "떡볶이", "price": 8000, "is_canceled": false}
```

- `menu_name` 은 선택이다 (배민 함께주문을 쓰면 가격만 입력).

## 실시간 반영 (소켓)

REST 로 상태가 바뀌면 서버가 `chat_<room_id>` 그룹으로 `room_update` 를 보낸다.

```json
{"type": "room_update", "payload": {"resource": "messages" | "vote" | "payment" | "delivery",
                                    "change": "created" | "updated", "room_id": 3, "data": {"id": 1}}}
```

- data 에는 id 만 들어간다. 받은 쪽에서 REST 로 다시 조회한다.
- 위 전용 API 로 만든 메시지는 서버가 알리므로, 클라이언트가 따로 `message_new` 를 보내지 않는다.
- 방 멤버(차단 관계 제외)만 `join` 할 수 있다. 아니면 `{"type": "error", "code": "forbidden"}` 을 받는다.
