from sqlalchemy import Column, BigInteger, String
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado_sqlalchemy import (as_future, declarative_base, call_blocking,
                                make_session_factory, SessionMixin)
from tornado.web import RequestHandler, Application

define("database-url", default="mysql+mysqldb://user:pass@localhost/db", help="DB uri")

DeclarativeBase = declarative_base()


class User(DeclarativeBase):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(String(128), unique=True)


class SyncWebRequestHandler(RequestHandler, SessionMixin):
    def get(self):
        with self.make_session() as session:
            count = session.query(User).count()

        self.write('{} users so far!'.format(count))

class AnotherAsyncSyncWebRequestHandler(RequestHandler, SessionMixin):
    async def get(self):
        with self.make_session() as session:
            count = await call_blocking(session.query(User).count)

        self.write('{} users so far!'.format(count))

class AsyncWebRequestHandler(RequestHandler, SessionMixin):
    @coroutine
    def get(self):
        with self.make_session() as session:
            count = yield as_future(session.query(User).count)

        self.write('{} users so far!'.format(count))


class UsesSelfSessionRequestHandler(RequestHandler, SessionMixin):
    @coroutine
    def get(self):
        count = self.session.query(User).count()

        self.write('{} users so far!'.format(count))


if __name__ == '__main__':
    options.parse_command_line()
    session_factory = make_session_factory(options.database_url)
    #DeclarativeBase.metadata.drop_all(session_factory.engine)
    DeclarativeBase.metadata.create_all(session_factory.engine)
    
    Application([
        (r'/sync', SyncWebRequestHandler),
        (r'/async', AsyncWebRequestHandler),
        (r'/aasync',AnotherAsyncSyncWebRequestHandler),
        (r'/uses-self-session', UsesSelfSessionRequestHandler),
    ], session_factory=session_factory).listen(8888)

    IOLoop.current().start()
