import os
from typing import List, Optional, Tuple
import sqlite3
import datetime


class Helper:
    def __init__(self, db_path: Optional[str] = None):
        base_path = os.path.abspath(os.path.dirname(__file__))
        project_root = os.path.abspath(os.path.join(base_path, "..", "..", ".."))
        self._db_path = db_path or os.path.join(
            project_root, "MyProjects\\DiscordBot\\SQL", "helper.db"
        )
        # print("helper dbpath: " + self._db_path)
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._initialize_database()

    def _initialize_database(self):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.executescript(
                """
CREATE TABLE IF NOT EXISTS PromptCache (
    HashedPrompt TEXT PRIMARY KEY,
    EncodedPrompt TEXT NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS GamblingCache (
    UserID TEXT PRIMARY KEY,
    Money DECIMAL(10, 2),
    LastUpdated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS JelqCache (
    JelqId INTEGER PRIMARY KEY AUTOINCREMENT,
    JelqDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    JelqAmount REAL NOT NULL,
    JelqAmountTotal REAL
);
CREATE TABLE IF NOT EXISTS CachePokemon (
    UserID INTEGER NOT NULL,
    PokeName TEXT NOT NULL,
    PokeAmt INTEGER DEFAULT 0,
    PokeCaught INTEGER DEFAULT 0,
    PokeImg TEXT,
    PRIMARY KEY (UserID, PokeName)
);
CREATE TABLE IF NOT EXISTS GirlsCache (
    GirlID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER NOT NULL,
    GirlName TEXT NOT NULL,
    GirlInfo TEXT NOT NULL,
    GirlImg TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS SpeakCache (
    StringValue TEXT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS AiGenerationCache (
    UserID INTEGER PRIMARY KEY,
    GenerationCount INTEGER NOT NULL DEFAULT 0,
    LastGenerated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
            )

    def save_jelq(self, date: datetime, amt: float):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
INSERT INTO JelqCache (JelqDate, JelqAmount, JelqAmountTotal)
VALUES (?, ?, COALESCE((SELECT SUM(JelqAmount) FROM JelqCache), 0) + ?)
""",
                (date, amt, amt),
            )

    def get_jelq(self) -> float:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(JelqAmount) FROM JelqCache")
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else -1

    def save_pokemon(
        self,
        user_id: int,
        pokemon: str,
        amount: int,
        caught: bool = True,
        image: Optional[str] = None,
    ):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
INSERT INTO CachePokemon (UserID, PokeName, PokeAmt, PokeCaught, PokeImg)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(UserID, PokeName) DO UPDATE SET
PokeAmt = excluded.PokeAmt,
PokeCaught = excluded.PokeCaught,
PokeImg = excluded.PokeImg
""",
                (user_id, pokemon, amount, int(caught), image),
            )

    def get_pokemon(self, user_id: int) -> List[Tuple[str, int, bool, str]]:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
SELECT PokeName, PokeAmt, PokeCaught, PokeImg
FROM CachePokemon
WHERE UserID = ?
ORDER BY SUBSTR(PokeName, 1, 4) ASC
""",
                (user_id,),
            )
            return [
                (row[0], row[1], bool(row[2]), row[3] if row[3] else "")
                for row in cursor.fetchall()
            ]

    def kill_pokemon(self, user_id: int, pokemon: str):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
DELETE FROM CachePokemon
WHERE UserID = ? AND PokeName LIKE ?
""",
                (user_id, f"{pokemon}%"),
            )

    def save_prompt(self, hashed_prompt: str, encoded_prompt: str):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
INSERT OR REPLACE INTO PromptCache (HashedPrompt, EncodedPrompt)
VALUES (?, ?)
""",
                (hashed_prompt, encoded_prompt),
            )

    def get_prompt(self, hashed_prompt: str) -> Optional[str]:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
SELECT EncodedPrompt FROM PromptCache WHERE HashedPrompt = ?
""",
                (hashed_prompt,),
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def save_money(self, user_id: int, money: float):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            rounded = round(money, 2)
            cursor.execute(
                """
INSERT INTO GamblingCache (UserID, Money)
VALUES (?, ?)
ON CONFLICT(UserID) DO UPDATE SET Money = Money + ?
""",
                (str(user_id), rounded, rounded),
            )

    def get_money(self, user_id: int) -> float:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Money FROM GamblingCache WHERE UserID = ?", (str(user_id),)
            )
            result = cursor.fetchone()
            return float(result[0]) if result else 0.0

    def save_girl(self, user_id: int, name: str, info: str, image: str):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
INSERT INTO GirlsCache (UserID, GirlName, GirlInfo, GirlImg)
VALUES (?, ?, ?, ?)
""",
                (user_id, name, info, image),
            )

    def delete_girl(self, user_id: int, name: str):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
DELETE FROM GirlsCache
WHERE UserID = ? AND GirlName LIKE ?
""",
                (user_id, f"%{name}%"),
            )

    def get_girl(self, user_id: int) -> List[Tuple[str, str, str]]:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT GirlName, GirlInfo, GirlImg FROM GirlsCache WHERE UserID = ?",
                (user_id,),
            )
            return [(row[0], row[1], row[2]) for row in cursor.fetchall()]

    def save_speak(self, string_value: str):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR IGNORE INTO SpeakCache (StringValue)
                VALUES (?)""",
                (string_value,),
            )

    def get_speak(self) -> List[str]:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT StringValue FROM SpeakCache",
            )
            return [row[0] for row in cursor.fetchall()]

    def get_gen(self, user_id: int) -> int:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT GenerationCount, LastGenerated FROM AiGenerationCache WHERE UserID = ?",
                (user_id,),
            )
            result = cursor.fetchone()
            
            if result:
                today = datetime.datetime.today().date()
                last_updated = datetime.datetime.fromisoformat(result[1]).date()
                if last_updated < today:
                    cursor.execute(
                        "UPDATE AiGenerationCache SET GenerationCount = 0, LastGenerated = ? WHERE UserID = ?",
                        (datetime.datetime.now(), user_id)
                    )
                print(f"Last updated: {last_updated}, Today: {today}\n"
                      f"Generation count: {result[0]}\n")
            
            return result[0] if result else 0

    def save_gen(self, user_id: int, count: int):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
INSERT INTO AiGenerationCache (UserID, GenerationCount, LastGenerated)
VALUES (?, ?, CURRENT_TIMESTAMP)
ON CONFLICT(UserID) DO UPDATE SET
GenerationCount = ?, LastGenerated = CURRENT_TIMESTAMP
""",
                (user_id, count, count),
            )
            conn.commit()
