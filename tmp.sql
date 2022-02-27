UPDATE new_ara.core_board t SET t.ko_name = '운영진공지', t.ko_description = '운영진공지' WHERE t.id = 8;
UPDATE new_ara.core_board t SET t.ko_name = '중고거래', t.ko_description = '중고거래' WHERE t.id = 4;
UPDATE new_ara.core_board t SET t.slug = 'facility-feedback', t.ko_name = '교내업체 피드백', t.en_name = 'Facility Feedback', t.ko_description = '교내업체 피드백', t.en_description = 'Facility Feedback' WHERE t.id = 5;

INSERT INTO new_ara.core_board (created_at, updated_at, deleted_at, slug, ko_name, en_name, ko_description,
                                en_description, is_readonly, access_mask, is_hidden, is_anonymous)
VALUES ('2022-02-24 21:41:37.000000', '2022-02-24 21:41:39.000000', '0001-01-01 00:00:00.000000', 'facility-notice',
        '교내 입주업체 공지', 'Facility Notice', '교내 입주업체 공지', 'Facility Notice', 0, 6, 0, 0);


INSERT INTO new_ara.core_board (created_at, updated_at, deleted_at, slug, ko_name, en_name, ko_description,
                                en_description, is_readonly, access_mask, is_hidden, is_anonymous)
VALUES ('2022-02-24 21:41:37.000000', '2022-02-24 21:41:39.000000', '0001-01-01 00:00:00.000000', 'club', '동아리', 'Club',
        '동아리', 'Club', 0, 2, 0, 0);

INSERT INTO new_ara.core_board (created_at, updated_at, deleted_at, slug, ko_name, en_name, ko_description,
                                en_description, is_readonly, access_mask, is_hidden, is_anonymous)
VALUES ('2022-02-24 21:41:37.000000', '2022-02-24 21:41:39.000000', '0001-01-01 00:00:00.000000', 'real-estate', '부동산',
        'Real Estate', '부동산', 'Real Estate', 0, 2, 0, 0);

INSERT INTO new_ara.core_board (created_at, updated_at, deleted_at, slug, ko_name, en_name, ko_description,
                                en_description, is_readonly, access_mask, is_hidden, is_anonymous)
VALUES ('2022-02-24 21:41:37.000000', '2022-02-24 21:41:39.000000', '0001-01-01 00:00:00.000000', 'with-school',
        '학교와의 게시판', 'With School', '학교와의 게시판', 'With School', 0, 2, 0, 0);

INSERT INTO new_ara.core_board (created_at, updated_at, deleted_at, slug, ko_name, en_name, ko_description,
                                en_description, is_readonly, access_mask, is_hidden, is_anonymous)
VALUES ('2022-02-24 21:41:37.000000', '2022-02-24 21:41:39.000000', '0001-01-01 00:00:00.000000', 'with-newara',
        '뉴아라팀과의 게시판', 'With Newara', '뉴아라팀과의 게시판', 'With Newara', 0, 2, 0, 0);

create table new_ara.core_board_group
(
    id      int auto_increment
        primary key,
    slug    varchar(30) not null,
    ko_name varchar(30) not null,
    en_name varchar(30) not null
);

INSERT INTO new_ara.core_board_group (id, slug, ko_name, en_name) VALUES (1, 'all', '모아보기', 'All');
INSERT INTO new_ara.core_board_group (id, slug, ko_name, en_name) VALUES (2, 'notice', '공지', 'Notice');
INSERT INTO new_ara.core_board_group (id, slug, ko_name, en_name) VALUES (3, 'chat', '잡담', 'Chat');
INSERT INTO new_ara.core_board_group (id, slug, ko_name, en_name) VALUES (4, 'students', '학생 단체 및 동아리', 'Students');
INSERT INTO new_ara.core_board_group (id, slug, ko_name, en_name) VALUES (5, 'money', '돈', 'Money');
INSERT INTO new_ara.core_board_group (id, slug, ko_name, en_name) VALUES (6, 'communication', '소통', 'Communication');


-- after migration
UPDATE new_ara.core_board t SET t.group_id = 4 WHERE t.id = 3;
UPDATE new_ara.core_board t SET t.group_id = 4 WHERE t.id = 12;
UPDATE new_ara.core_board t SET t.group_id = 2 WHERE t.id = 6;
UPDATE new_ara.core_board t SET t.group_id = 2 WHERE t.id = 7;
UPDATE new_ara.core_board t SET t.group_id = 5 WHERE t.id = 5;
UPDATE new_ara.core_board t SET t.group_id = 5 WHERE t.id = 14;
UPDATE new_ara.core_board t SET t.group_id = 5 WHERE t.id = 13;
UPDATE new_ara.core_board t SET t.group_id = 3 WHERE t.id = 11
UPDATE new_ara.core_board t SET t.group_id = 4 WHERE t.id = 4;
UPDATE new_ara.core_board t SET t.group_id = 3 WHERE t.id = 2;
UPDATE new_ara.core_board t SET t.group_id = 2 WHERE t.id = 9;
