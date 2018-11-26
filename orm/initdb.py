'''
Created on Mar 17, 2017

@author: Bogdan Vasilescu
'''

import logging

import yaml
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import sessionmaker
import configparser

import os
from .base import Base

logger = logging.getLogger('SZZ')


class SessionWrapper:
    proto = 'mysql'
    server = None
    db_name = None
    u = None
    p = None

    @staticmethod
    def load_config():
        with open(os.path.join(os.getcwd(), "config.yml"), 'r') as config:
            cfg = yaml.load(config)
            SessionWrapper.server = cfg[SessionWrapper.proto]['host']
            SessionWrapper.db_name = cfg[SessionWrapper.proto]['db']
            SessionWrapper.u = cfg[SessionWrapper.proto]['user']
            SessionWrapper.p = cfg[SessionWrapper.proto]['passwd']
            if SessionWrapper.p != '':
                SessionWrapper.p = ':' + SessionWrapper.p

    @staticmethod
    def new(init=False):
        engine = create_engine('{0}://{1}{2}@{3}/{4}?charset=utf8mb4'.format(SessionWrapper.proto, SessionWrapper.u,
                                                                             SessionWrapper.p, SessionWrapper.server,
                                                                             SessionWrapper.db_name))
        if not database_exists(engine.url):
            logger.info("Database %s created" % SessionWrapper.db_name)
            create_database(engine.url, encoding='utf8mb4')
        logger.debug(msg='Connection established to {0}@{1}.'.format(SessionWrapper.proto, SessionWrapper.server))

        if init:
            SessionWrapper.__init_db(engine)
            logger.info(msg='Structure for database %s created.' % SessionWrapper.db_name)

        _session = sessionmaker(engine)
        return _session()

    @staticmethod
    def __init_db(engine):
        metadata = Base.metadata
        metadata.create_all(engine)

class SessionWrapper_GHT:
    def new():
        settings = configparser.ConfigParser()
        settings.read(os.path.join(os.getcwd(), "config.ini"))
        user_name = settings.get('GHT','User')
        password = settings.get('GHT','Pass')
        engine_ght = create_engine('mysql+pymysql://%s:%s@localhost/ghtorrent-2018-03?charset=utf8mb4'%(user_name, password))
        Session_GHT = sessionmaker(engine_ght)
        return Session_GHT()
