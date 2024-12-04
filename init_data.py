import sqlite3

def initialize_db():
    conn = sqlite3.connect('tweets.db')
    cursor = conn.cursor()

    # Create table for tweets
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tweets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        sentiment TEXT,
        country TEXT,
        timestamp TEXT
    )
    ''')

    # Sample data
    cursor.executemany('''
    INSERT INTO tweets (text, sentiment, country, timestamp) VALUES (?, ?, ?, ?)
    ''', [
        ('I love the weather today!', 'positive', 'India', '2024-11-19 12:00:00'),
        ('I am feeling down lately.', 'negative', 'India', '2024-11-19 12:10:00'),
        ('Great job on the new product!', 'positive', 'USA', '2024-11-19 12:20:00')
    ])

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_db()
