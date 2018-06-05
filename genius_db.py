import yaml
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base



def read_yaml(path):
    """Read YAML files containg credential info.

    Args:
        path (str): The path to the YAML file.
    Returns:
        dict containing the YAML data.
    """
    with open(path, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

def db_connect(echo=True):
    # dialect+driver://username:password@host:port/database
    creds = read_yaml('db/genius_db.yml')
    engine_config = 'mysql://{0}:{1}@{2}/{3}'.format(
        creds['username'],
        creds['password'],
        creds['host'],
        creds['database']
    )

    engine = create_engine(engine_config, echo=echo)
    return engine


def to_db(engine, df, tablename='songs_v3'):
    df.to_sql('songs_v4', engine, if_exists='append', chunksize=30)


Base = declarative_base()
# Store JSON as JSON? Arrays as Arrays?
class Song(Base):
    __tablename__ = 'songs_v4'

    # song_id = Column(Integer, primary_key=True)
    # title = Column(String(255))
    # title_with_featured = Column(String(255))
    # release_date = Column(DateTime)
    # url = Column(String(255))
    # published = Column(Boolean)
    # tags = Column(Text)
    # recording_location = Column(String(255))
    # artist = Column(String(255))
    # primary_artist_id = Column(Integer)
    # artist_url = Column(String(255))
    # featured_artist_ids = Column(Text)
    # featuring = Column(Text)
    # album_id = Column(Integer)
    # album__href = Column(String(255))
    # album__text = Column(String(255))
    # produced_by__href = Column(String(255))
    # produced_by__text = Column(String(255))
    # lyrics_language = Column(String(16))
    # lyrics_created_at = Column(DateTime)
    # lyrics_updated_at = Column(DateTime)
    # lyrics_state = Column(String(255))
    # lyrics = Column(Text)

    song_id = Column(Integer, primary_key=True)
    album_artist_id = Column(Integer)
    album_href = Column(String(255))
    album_id = Column(Integer)
    album_title = Column(String(255))
    artist = Column(String(255))
    artist_url = Column(String(255))
    featured_artist_ids = Column(Text)
    featuring = Column(Text)
    lyrics = Column(Text)
    lyrics_created_at = Column(DateTime)
    lyrics_language = Column(String(16))
    lyrics_state = Column(String(255))
    lyrics_updated_at = Column(DateTime)
    primary_artist_id = Column(Integer)
    produced_by = Column(Text)
    published = Column(Boolean)
    recording_location = Column(String(255))
    release_date = Column(DateTime)
    tags = Column(Text)
    title = Column(String(255))
    title_with_featured = Column(String(255))
    url = Column(String(255))

    def __repr__(self):
        return "<Song(song_id='{0}', title='{1}', url='{2}')>".format(
                            self.song_id, self.title, self.url)
