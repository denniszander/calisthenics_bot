import sqlite3
import time


class DBHelper:
    def __init__(self, dbname="./DB/Calisthenics"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)
        self.plan_id = None
        self.training_id = None
        self.exercise_id = None

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
        if self.training_id is not None:
            return
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

    def get_last_exercise_info(self):
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
        args = (self.exercise_id, self.exercise_id, self.exercise_id)
        cursor = self.conn.execute(stmt, args)
        resultsRaw = cursor.fetchone()
        if resultsRaw is None:
            return F"You have not done this exercise yet."
        # Return time in format dd.mm.yyyy with hour and minute
        return F"Exercise: {resultsRaw[0]} \nReps: {resultsRaw[1]} \nDate: {time.strftime('%d.%m.%Y %H:%M', time.localtime(resultsRaw[3]))} \nRemark: {resultsRaw[2]}"

    def update_history_reps(self, reps):
        """
        Update the history table with the given exercise, reps 
        If we already have a training session started and did the exercise before append the new reps to the old ones
        Args:
            reps (str): number of reps
        """
        stmt = "SELECT Reps FROM History WHERE TrainingID = ? AND ExerciseID = ?"
        args = (self.training_id, self.exercise_id)
        cursor = self.conn.execute(stmt, args)
        resultsRaw = cursor.fetchone()
        if resultsRaw is None:
            stmt = "INSERT INTO History (TrainingID, ExerciseID, Reps) VALUES (?, ?, ?)"
            args = (self.training_id, self.exercise_id, reps)
        else:
            stmt = "UPDATE History SET Reps = ? WHERE TrainingID = ? AND ExerciseID = ?"
            args = (resultsRaw[0] + ", " + reps, self.training_id, self.exercise_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def update_history_remark(self, remark):
        """
        Update the history table with the given remark 
        Overwrite the old remark, if there is one
        Args:
            remark (str): remark
        """
        stmt = "SELECT Remark FROM History WHERE TrainingID = ? AND ExerciseID = ?"
        args = (self.training_id, self.exercise_id)
        cursor = self.conn.execute(stmt, args)
        resultsRaw = cursor.fetchone()
        if resultsRaw is None:
            stmt = "INSERT INTO History (TrainingID, ExerciseID, Remark) VALUES (?, ?, ?)"
            args = (self.training_id, self.exercise_id, remark)
        else:
            stmt = "UPDATE History SET Remark = ? WHERE TrainingID = ? AND ExerciseID = ?"
            args = (remark, self.training_id, self.exercise_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_exercise_data(self):
        """
        Delete all data from the history table for the current exercise in training session
        """
        stmt = "DELETE FROM History WHERE TrainingID = ? AND ExerciseID = ?"
        args = (self.training_id, self.exercise_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

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

