import sqlite3
import time


class DBHelper:
    def __init__(self, dbname="./DB/Calisthenics"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)
        self.plan_id = None
        self.training_id = None

    def exercises(self):
        """
        Get all exercises and return them as a list.
        Returns: 
            list of tuples: (int, str, str) = (id, exercise, link to exercise)
        """
        stmt = "SELECT Id, Name, Link  FROM Exercises"
        cursor = self.conn.execute(stmt)
        resultsRaw = cursor.fetchall()
        results = []
        for row in resultsRaw:
            results.append(row)
        return results

    def start_training(self):
        """
        Insert start date and plan into Training table
        Start should be an intger representing the current time
        Plan should be the given instance variable 
        Finally set the training_id instance variable
        """
        start_int = int(time.time())
        stmt = "INSERT INTO Training (Start, Plan) VALUES (?, ?)"
        args = (start_int, self.plan_id)
        self.conn.execute(stmt, args)
        self.conn.commit()
        stmt = "SELECT Id FROM Training WHERE Start = ?"
        args = (start_int,)
        cursor = self.conn.execute(stmt, args)
        resultsRaw = cursor.fetchone()
        self.training_id = resultsRaw[0]

    def get_last_exercise_info(self, exercise_id):
        """
        Get the last time the exercise was done and reps from the database
        Args:
            exercise_id (str): name of the exercise
        Returns:
            str : Info message to be sent to the user
        """
        stmt ="""  WITH TrID as (SELECT max(h.TrainingID) as TrainingID FROM History h WHERE h.ExerciseID = ?)
                 SELECT e.name, h.Reps, h.Remark, t.Start
                   FROM Exercises e, History h, Training t, TrID
                  WHERE e.ID = ? AND h.ExerciseID = ? AND h.TrainingID = TrID.TrainingID AND t.ID = TrID.TrainingID;"""
        args = (exercise_id, exercise_id, exercise_id)
        cursor = self.conn.execute(stmt, args)
        resultsRaw = cursor.fetchone()
        if resultsRaw is None:
            return F"You have not done this exercise yet."
        return F"Last time you did {resultsRaw[0]} was {resultsRaw[1]} times on {time.strftime('%d.%m.%Y', time.localtime(resultsRaw[3]))} with the remark: {resultsRaw[2]}"

if __name__ == '__main__':
    db = DBHelper()
    #-#- Example to catch exercises
    # exercises = db.exercises()
    # print(exercises[0][0])
    #-#- Example to start a training session
    # db.start_training()
    # print(db.training_id)
    #-#- Example to get last exercise info
    print(db.get_last_exercise_info(2))

