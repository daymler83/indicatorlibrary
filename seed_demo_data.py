from pathlib import Path
import csv
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "indicator_system.db"
INDICATORS_CSV = BASE_DIR / "data" / "indicators.csv"
VALUES_CSV = BASE_DIR / "data" / "indicator_values.csv"

AR_TRANSLATIONS = {
    "Unemployment Rate": "معدل البطالة",
    "GDP Growth Rate": "معدل نمو الناتج المحلي الإجمالي",
    "Energy Access Rate": "معدل الوصول إلى الطاقة",
    "School Enrollment Rate": "معدل الالتحاق بالمدارس",
    "CO2 Emissions per Capita": "انبعاثات ثاني أكسيد الكربون للفرد",
}

DEFAULT_PERMISSIONS = [
    ("view_indicators", "Can view indicators"),
    ("edit_indicators", "Can create and edit indicators"),
    ("upload_values", "Can upload indicator values"),
    ("approve_indicators", "Can approve indicators"),
    ("manage_users", "Can manage users and permissions"),
    ("view_dashboard", "Can access dashboard features"),
]


def _normalize(value):
    if value is None:
        return None
    value = str(value).strip()
    return None if value == "" else value


def seed_permissions(cur):
    for name, description in DEFAULT_PERMISSIONS:
        cur.execute(
            "INSERT OR IGNORE INTO permissions (name, description) VALUES (?, ?)",
            (name, description),
        )


def seed_indicators(cur):
    if not INDICATORS_CSV.exists():
        print(f"Missing indicators CSV: {INDICATORS_CSV}")
        return

    with INDICATORS_CSV.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            indicator_id = _normalize(row.get("id"))
            if not indicator_id:
                continue

            version = row.get("version")
            cur.execute(
                """
                INSERT OR IGNORE INTO indicators
                (id, name, definition, formula, owner, status, version, dimension, sector, type, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    indicator_id,
                    _normalize(row.get("name")),
                    None,
                    None,
                    _normalize(row.get("owner")),
                    _normalize(row.get("status")),
                    float(version) if _normalize(version) else None,
                    _normalize(row.get("dimension")),
                    _normalize(row.get("sector")),
                    "operational",
                    "medium",
                ),
            )

            cur.execute(
                """
                INSERT OR IGNORE INTO indicator_texts
                (indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    indicator_id,
                    "en",
                    _normalize(row.get("name")),
                    None,
                    None,
                    _normalize(row.get("owner")),
                    _normalize(row.get("dimension")),
                    _normalize(row.get("sector")),
                    0,
                    "official",
                    "en",
                ),
            )

            cur.execute(
                "SELECT 1 FROM indicator_texts WHERE indicator_id = ? AND language = ?",
                (indicator_id, "ar"),
            )
            if cur.fetchone() is None:
                cur.execute(
                    """
                    INSERT INTO indicator_texts
                    (indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        indicator_id,
                        "ar",
                        AR_TRANSLATIONS.get(_normalize(row.get("name")), _normalize(row.get("name"))),
                        None,
                        None,
                        _normalize(row.get("owner")),
                        _normalize(row.get("dimension")),
                        _normalize(row.get("sector")),
                        1,
                        "official",
                        "en",
                    ),
                )


def seed_values(cur):
    if not VALUES_CSV.exists():
        print(f"Missing values CSV: {VALUES_CSV}")
        return

    with VALUES_CSV.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            indicator_id = _normalize(row.get("indicator_id"))
            year = _normalize(row.get("year"))
            if not indicator_id or not year:
                continue

            region = _normalize(row.get("region"))
            province = _normalize(row.get("province"))
            gender = _normalize(row.get("gender"))
            value = _normalize(row.get("value"))
            tracking_status = _normalize(row.get("tracking_status"))
            tracking_message = _normalize(row.get("tracking_message"))

            cur.execute(
                """
                SELECT 1
                FROM indicator_values
                WHERE indicator_id = ? AND year = ? AND COALESCE(region, '') = COALESCE(?, '')
                  AND COALESCE(province, '') = COALESCE(?, '')
                  AND COALESCE(gender, '') = COALESCE(?, '')
                """,
                (indicator_id, int(year), region, province, gender),
            )
            if cur.fetchone() is not None:
                continue

            cur.execute(
                """
                INSERT INTO indicator_values
                (indicator_id, year, region, province, gender, value, tracking_status, tracking_message, imported_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    indicator_id,
                    int(year),
                    region,
                    province,
                    gender,
                    value,
                    tracking_status,
                    tracking_message,
                    "seed_demo_data",
                ),
            )


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        seed_permissions(cur)
        seed_indicators(cur)
        seed_values(cur)
        conn.commit()
        print("Demo data seeded.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
