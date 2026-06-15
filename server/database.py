from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "postgresql://postgres:1234@localhost:5432/logistics"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session():
    """Получить сессию для работы с БД"""
    return SessionLocal()


if __name__ == "__main__":
    print("🔌 Тестирую подключение к PostgreSQL...")

    try:
        # Открываем соединение
        with engine.connect() as conn:
            # ⚠️ ВАЖНО: используем text() для сырых SQL-запросов в SQLAlchemy 2.0
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]

            print("✅ Подключение успешно!")
            print(f"📦 Версия PostgreSQL: {version}")

            # Дополнительная проверка: есть ли наша база
            db_check = conn.execute(text("SELECT current_database();"))
            print(f"🗄 Подключены к базе: {db_check.fetchone()[0]}")

            # Проверка наличия таблиц
            tables = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            table_list = [row[0] for row in tables.fetchall()]
            print(f"📋 Найдено таблиц ({len(table_list)}): {', '.join(table_list)}")

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("\n💡 Проверьте:")
        print("   1. Запущен ли сервер PostgreSQL (Службы Windows)")
        print("   2. Правильный ли пароль в строке DATABASE_URL")
        print("   3. Создана ли база данных 'logistics' в pgAdmin")