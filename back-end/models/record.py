from datetime import datetime
import pymysql
from config import MYSQL_CONFIG
import json

class Record:
    def __init__(self):
        self.conn = pymysql.connect(**MYSQL_CONFIG)
        self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        self.create_table()

    def create_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS detection_record (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            original_image_url TEXT,
            detected_image_url TEXT,
            detection_data JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_version VARCHAR(10),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
        self.cursor.execute(sql)
        self.conn.commit()

    def insert_record(self, user_id, original_url, detected_url, detection_data, total_defects, defect_types, created_at, model_version):
        sql = '''
        INSERT INTO detection_record (user_id, original_image_url, detected_image_url, detection_data, total_defects, defect_types, created_at, model_version)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        self.cursor.execute(sql, (
            user_id,
            original_url,
            detected_url,
            json.dumps(detection_data),
            total_defects,
            json.dumps(defect_types),
            created_at,
            model_version
        ))
        self.conn.commit()

    # def get_records_by_user(self, user_id):
    #     sql = "SELECT * FROM detection_record WHERE user_id = %s ORDER BY created_at DESC"
    #     self.cursor.execute(sql, (user_id,))
    #     rows = self.cursor.fetchall()
    #
    #     records = []
    #     for row in rows:
    #         records.append({
    #             'created_at': row['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
    #             'original_image_url': row['original_image_url'],
    #             'detected_image_url': row['detected_image_url'],
    #             'detection_data': json.loads(row['detection_data']),
    #             'total_defects': row.get('total_defects', 0),
    #             'defect_types': json.loads(row['defect_types']) if row.get('defect_types') else []
    #         })
    #     return records

    def get_records_by_user_paginated(self, user_id, page, per_page):
        offset = (page - 1) * per_page

        count_sql = "SELECT COUNT(*) as total FROM detection_record WHERE user_id = %s"
        self.cursor.execute(count_sql, (user_id,))
        total = self.cursor.fetchone()['total']

        sql = """
        SELECT * FROM detection_record
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        self.cursor.execute(sql, (user_id, per_page, offset))
        rows = self.cursor.fetchall()
        return [self._row_to_dict(row) for row in rows], total

    def delete_record(self, record_id, user_id):
        sql = "DELETE FROM detection_record WHERE id = %s AND user_id = %s"
        affected_rows = self.cursor.execute(sql, (record_id, user_id))
        self.conn.commit()
        return affected_rows > 0

    def _row_to_dict(self, row):
        return {
            'created_at': row['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
            'original_image_url': row['original_image_url'],
            'detected_image_url': row['detected_image_url'],
            'detection_data': json.loads(row['detection_data']),
            'total_defects': row.get('total_defects', 0),
            'defect_types': json.loads(row['defect_types']) if row.get('defect_types') else [],
            'model_version': row.get('model_version', ''),
            'id': row['id']
        }

