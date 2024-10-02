from sqlalchemy import text

def sample_selector(session):
    session.execute(text("select * from sample;"))
