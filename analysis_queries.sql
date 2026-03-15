USE resume_analyzer;
CREATE TABLE IF NOT EXISTS analysis_results (
            id SERIAL PRIMARY KEY,
            resume_name VARCHAR(255),
            match_score FLOAT,
            job_description TEXT,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_resume TEXT
        )
INSERT INTO analysis_results
                (resume_name, match_score, job_description, analysis_date,processed_resume)
                VALUES (%s, %s, %s, %s,%s)
            """, (n, s, job_desc[:1000], datetime.now(),t[:1000]))


SELECT * FROM analysis_results
ORDER BY analysis_date DESC;

DELETE FROM analysis_results
WHERE id IN (
    SELECT id
    FROM analysis_results
    ORDER BY analysis_date DESC
    LIMIT 4
);