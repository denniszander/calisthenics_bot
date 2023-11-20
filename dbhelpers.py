import sqlite3

class DBHelper:
    def __init__(self, dbname="./DB/Calisthenics"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def exercises(self):
        """
        Get all exercises and return them as a list.
        Returns: 
            list of tuples: (str, str) = (exercise, link to exercise)
        """
        stmt = "SELECT Name, Link  FROM Exercises"
        cursor = self.conn.execute(stmt)
        resultsRaw = cursor.fetchall()
        results = []
        for row in resultsRaw:
            results.append(row)
        return results

if __name__ == '__main__':
    db = DBHelper()
    exercises = db.exercises()
    print(exercises[0][0])

