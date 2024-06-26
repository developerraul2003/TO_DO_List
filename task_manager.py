import pyodbc
from task import Task


class TaskManager:
    def __init__(self, server, database):
        self.conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
        )
    
    def add_task(self, task_name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO Tasks (TaskName, Status) VALUES (?, ?)", (task_name, 'Pending'))
        self.conn.commit()

    def list_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT TaskID, TaskName, Status FROM Tasks")
        tasks = cursor.fetchall()
        return [Task(task_id=row.TaskID, task_name=row.TaskName, status=row.Status) for row in tasks]

    def list_pending_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT TaskID, TaskName, Status FROM Tasks WHERE Status = 'Pending'")
        tasks = cursor.fetchall()
        return [Task(task_id=row.TaskID, task_name=row.TaskName, status=row.Status) for row in tasks]

    def search_task(self, search_term):
        cursor = self.conn.cursor()
        cursor.execute("SELECT TaskID, TaskName, Status FROM Tasks WHERE TaskName LIKE ?", ('%' + search_term + '%',))
        tasks = cursor.fetchall()
        return [Task(task_id=row.TaskID, task_name=row.TaskName, status=row.Status) for row in tasks]

    def update_task_status(self, task_id, new_status):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE Tasks SET Status = ? WHERE TaskID = ?", (new_status, task_id))
        self.conn.commit()

    def mark_task_completed(self, task_id):
        self.update_task_status(task_id, 'Completed')

    def edit_task_name(self, task_id, new_name):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE Tasks SET TaskName = ? WHERE TaskID = ?", (new_name, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT TaskID, TaskName, Status FROM Tasks WHERE TaskID = ?", (task_id,))
        deleted_task = cursor.fetchone()  # Fetch the deleted task
        cursor.execute("DELETE FROM Tasks WHERE TaskID = ?", (task_id,))
        self.conn.commit()
        self.renumber_task_ids()
        return deleted_task  # Return the deleted task

    def renumber_task_ids(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT TaskID, TaskName, Status FROM Tasks ORDER BY TaskID")
        tasks = cursor.fetchall()

        # Create a temporary table to hold the renumbered tasks
        cursor.execute("""
            CREATE TABLE #TempTasks (
                TaskID INT PRIMARY KEY,
                TaskName NVARCHAR(255),
                Status NVARCHAR(50)
            )
        """)
        
        # Insert tasks into the temporary table with new sequential IDs
        for index, row in enumerate(tasks):
            new_id = index + 1
            cursor.execute("INSERT INTO #TempTasks (TaskID, TaskName, Status) VALUES (?, ?, ?)", (new_id, row.TaskName, row.Status))
        
        self.conn.commit()

        # Enable IDENTITY_INSERT to allow explicit TaskID insertion
        cursor.execute("SET IDENTITY_INSERT Tasks ON")
        
        # Clear the original table and insert renumbered tasks back
        cursor.execute("DELETE FROM Tasks")
        cursor.execute("INSERT INTO Tasks (TaskID, TaskName, Status) SELECT TaskID, TaskName, Status FROM #TempTasks")
        
        # Disable IDENTITY_INSERT
        cursor.execute("SET IDENTITY_INSERT Tasks OFF")
        self.conn.commit()

        # Drop the temporary table
        cursor.execute("DROP TABLE #TempTasks")
        self.conn.commit()

    def close(self):
        self.conn.close()
