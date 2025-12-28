BEGIN TRANSACTION;
CREATE TABLE answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  question_id TEXT,
  final_text TEXT,
  created_at TEXT
);
INSERT INTO "answers" VALUES(1,'17e871a9-91f0-4ba9-a73b-aab1e4b14683','1','This is my test answer','2025-11-23 07:42:26');
INSERT INTO "answers" VALUES(2,'d6d7f3f8-6197-4e25-87d7-3beb42688dc6','1','This is my test answer','2025-11-23 08:54:15');
INSERT INTO "answers" VALUES(3,'d6d7f3f8-6197-4e25-87d7-3beb42688dc6','1','This is my test answer','2025-11-23 14:32:35');
INSERT INTO "answers" VALUES(4,'d6d7f3f8-6197-4e25-87d7-3beb42688dc6','1','This is my test answer','2025-11-23 14:50:35');
INSERT INTO "answers" VALUES(5,'e9d87252-51cf-4e87-992e-271a5b70a0b5','1','This is my test answer','2025-11-23 16:55:01');
INSERT INTO "answers" VALUES(6,'09df86c2-1337-4847-99c4-2c4fe4e7371d','1','Hello','2025-11-23 17:09:08');
INSERT INTO "answers" VALUES(7,'8a4072d6-d456-4f7d-a91d-7c780ca9921b','1','This is my test answer','2025-11-23 17:14:34');
INSERT INTO "answers" VALUES(8,'485078c2-8feb-4434-8c84-8cbd739b42f1','1','This is my test answer','2025-11-23 17:35:51');
INSERT INTO "answers" VALUES(9,'6d01458d-ece3-4979-af01-c4996098f170','1','hi i am sowjanya','2025-11-23 18:12:01');
INSERT INTO "answers" VALUES(10,'35d36378-f8a7-410d-8ff2-a7d61787d480','1','hi i am sowjanya from ms ramaiah university ','2025-11-23 18:18:45');
INSERT INTO "answers" VALUES(11,'5c841dbb-98ff-41bb-bda3-13cd6b15d453','1','hi i am sowjanya from ms ramaiah university system from cse aiml ','2025-11-24 04:24:13');
INSERT INTO "answers" VALUES(12,'e3ae30ee-b7bd-4ae1-ad4f-cf3d5e536e02','1','hi i am sowjanya from ms ramaiah university system from cse aiml ','2025-11-24 04:47:56');
INSERT INTO "answers" VALUES(13,'25258800-404b-4325-a0fd-57f7fbed8d8d','1','i ams sowjanya ravindra from ms ramaiah university of applied sciences at cse aiml ','2025-11-24 05:19:44');
INSERT INTO "answers" VALUES(14,'20c8697c-5f05-417d-936b-8d656f6632d5','1','i ams sowjanya ravindra from ms ramaiah university of applied sciences at cse aiml ','2025-11-24 05:20:06');
INSERT INTO "answers" VALUES(15,'f0b6e220-8bba-4c2c-bc2f-1111ee01ea80','1','hi i am sowjanya from ms ramaiah university of applied sciencse','2025-11-24 06:10:04');
INSERT INTO "answers" VALUES(16,'c40ad83e-9817-402c-a0ae-4722b175b038','1','hi i am sowjanya from ms ramaiah university of applied sciencse','2025-11-24 06:10:30');
INSERT INTO "answers" VALUES(17,'0f4cf96a-5951-460d-968c-b54907fddda0','1','AI technology enables machines to simulate human intelligence by learning from data, recognizing patterns, and making decisions to perform tasks like understanding language, solving problems, and making predictions. It is used in many applications, from virtual assistants and recommendation systems to self-driving cars and medical diagnostics, and is based on fields like machine learning and deep learning. ','2025-11-24 06:11:37');
INSERT INTO "answers" VALUES(18,'ffb93e90-b081-4cf0-a3bf-99f71a64c26e','1','hi i am sowjanya how are u','2025-11-24 06:12:10');
INSERT INTO "answers" VALUES(19,'6c725875-9261-485c-adb1-66de18665011','1','hi i am sowjanya ravindra from ms ramiah university','2025-11-24 06:13:15');
CREATE TABLE assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT UNIQUE,
  candidate_id INTEGER,
  test_id INTEGER,
  created_at TEXT
);
INSERT INTO "assignments" VALUES(1,'fe5cf222-b59a-41ca-b30a-f7b7e32b3de2',1,1,'2025-11-21 02:46:02');
CREATE TABLE feature_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  question_id TEXT,
  mean_ht REAL,
  mean_dd REAL,
  cpm REAL,
  paste_flag INTEGER,
  created_at TEXT
);
CREATE TABLE keystroke_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  question_id TEXT,
  events_json TEXT,
  created_at TEXT
);
CREATE TABLE questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  text TEXT
);
INSERT INTO "questions" VALUES(1,'Sample question text for enrollment');
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT UNIQUE,
  assignment_id INTEGER,
  candidate_id INTEGER,
  test_id INTEGER,
  started_at TEXT,
  finished_at TEXT,
  status TEXT
);
INSERT INTO "sessions" VALUES(1,'de74803d-5a4f-468e-9c31-9dd588cf4045',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(2,'c1a303d7-da70-4bce-acf6-6b2e848eade7',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(3,'d6a4e8f1-4dd2-4146-8f25-b4ba1d4ff509',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(4,'f94994bf-89ce-4d4d-8576-6dd34f2ec76c',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(5,'e49d6d04-1426-4c56-8173-0cbf3de77355',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(6,'21f59614-539d-4e44-9e3b-df7db1b5a857',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(7,'cef33323-e5d6-4eea-b08c-ad7c9e61fb94',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(8,'64e88794-46db-4edb-94a9-f844a543d321',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(9,'3ddc46bc-8ce5-4028-9343-b7b2f6d9ef04',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(10,'2fbdf0a9-eadc-4b73-8373-b1f8f8128b09',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(11,'65390989-cd39-4173-95d4-047a36577eb2',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(12,'93dbd670-a864-4b7f-b4a6-47e0224d7438',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(13,'c9cc043e-07b7-4f37-b6b1-f3311195aeb6',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(14,'17e871a9-91f0-4ba9-a73b-aab1e4b14683',NULL,1,1,'2025-11-23 07:27:49',NULL,'active');
INSERT INTO "sessions" VALUES(15,'283ec01d-188b-4c76-a567-b6422cef8bb4',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(16,'d6d7f3f8-6197-4e25-87d7-3beb42688dc6',NULL,1,1,'2025-11-23 20:20:16',NULL,'active');
INSERT INTO "sessions" VALUES(17,'53e44648-9f2b-4989-b832-b7df689622e5',NULL,1,1,NULL,NULL,NULL);
INSERT INTO "sessions" VALUES(18,'87b03a99-75c9-47cd-8199-2547a2bb7608',NULL,1,1,'2025-11-23 16:47:26',NULL,'active');
INSERT INTO "sessions" VALUES(19,'e9d87252-51cf-4e87-992e-271a5b70a0b5',NULL,1,1,'2025-11-23 16:50:07',NULL,'active');
INSERT INTO "sessions" VALUES(20,'09df86c2-1337-4847-99c4-2c4fe4e7371d',NULL,1,1,'2025-11-23 17:08:41','2025-11-23 17:09:39','finished');
INSERT INTO "sessions" VALUES(21,'8a4072d6-d456-4f7d-a91d-7c780ca9921b',NULL,1,1,'2025-11-23 17:14:06',NULL,'active');
INSERT INTO "sessions" VALUES(22,'1929c313-4645-4cc3-a98f-6f311ca592ad',NULL,1,1,'2025-11-23 17:27:52',NULL,'active');
INSERT INTO "sessions" VALUES(23,'485078c2-8feb-4434-8c84-8cbd739b42f1',NULL,1,1,'2025-11-23 17:35:17',NULL,'active');
INSERT INTO "sessions" VALUES(24,'6a48f1e6-6220-44a1-b77e-b0e5ed3219c4',NULL,1,1,'2025-11-23 17:44:29',NULL,'active');
INSERT INTO "sessions" VALUES(25,'6d01458d-ece3-4979-af01-c4996098f170',NULL,1,1,'2025-11-23 18:11:50',NULL,'active');
INSERT INTO "sessions" VALUES(26,'9d974ba4-a1e5-4ab4-9bf8-3792e32ca014',NULL,1,1,'2025-11-23 18:12:17',NULL,'active');
INSERT INTO "sessions" VALUES(27,'35d36378-f8a7-410d-8ff2-a7d61787d480',NULL,1,1,'2025-11-23 18:18:17',NULL,'active');
INSERT INTO "sessions" VALUES(28,'5c841dbb-98ff-41bb-bda3-13cd6b15d453',NULL,1,1,'2025-11-24 04:23:31',NULL,'active');
INSERT INTO "sessions" VALUES(29,'e3ae30ee-b7bd-4ae1-ad4f-cf3d5e536e02',NULL,1,1,'2025-11-24 04:47:52',NULL,'active');
INSERT INTO "sessions" VALUES(30,'25258800-404b-4325-a0fd-57f7fbed8d8d',NULL,1,1,'2025-11-24 05:19:32',NULL,'active');
INSERT INTO "sessions" VALUES(31,'20c8697c-5f05-417d-936b-8d656f6632d5',NULL,1,1,'2025-11-24 05:20:01',NULL,'active');
INSERT INTO "sessions" VALUES(32,'f0b6e220-8bba-4c2c-bc2f-1111ee01ea80',NULL,1,1,'2025-11-24 06:09:34',NULL,'active');
INSERT INTO "sessions" VALUES(33,'c40ad83e-9817-402c-a0ae-4722b175b038',NULL,1,1,'2025-11-24 06:10:24',NULL,'active');
INSERT INTO "sessions" VALUES(34,'e115be95-bab3-4df9-af2f-525f5d5c1a5a',NULL,1,1,'2025-11-24 06:10:56',NULL,'active');
INSERT INTO "sessions" VALUES(35,'2f6e4420-9f33-4b9d-b790-477e2ea586f6',NULL,1,1,'2025-11-24 06:10:58',NULL,'active');
INSERT INTO "sessions" VALUES(36,'0f4cf96a-5951-460d-968c-b54907fddda0',NULL,1,1,'2025-11-24 06:11:12',NULL,'active');
INSERT INTO "sessions" VALUES(37,'ffb93e90-b081-4cf0-a3bf-99f71a64c26e',NULL,1,1,'2025-11-24 06:11:58',NULL,'active');
INSERT INTO "sessions" VALUES(38,'6c725875-9261-485c-adb1-66de18665011',NULL,1,1,'2025-11-24 06:12:47',NULL,'active');
CREATE TABLE test_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  test_id INTEGER,
  question_id INTEGER,
  seq INTEGER
);
INSERT INTO "test_questions" VALUES(1,1,1,1);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('questions',1);
INSERT INTO "sqlite_sequence" VALUES('test_questions',1);
INSERT INTO "sqlite_sequence" VALUES('assignments',1);
INSERT INTO "sqlite_sequence" VALUES('sessions',38);
INSERT INTO "sqlite_sequence" VALUES('answers',19);
COMMIT;
