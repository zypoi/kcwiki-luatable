#!/usr/bin/env python3

import asyncio
import functools
import os
import subprocess
import time
from os import environ, path

from config import (AIRPOWER_TABLE, AKASHI_LIST_OUTPUT_LUA, BONUS_JS, DB_PATH,
                    ENTITIES_DB, ITEM_TYPES_DB, ITEMS_DATA, ITEMS_DB,
                    JSON_PATH, KCDATA_SHIP_ALL_JSON, KCDATA_SLOTITEM_ALL_JSON,
                    LUATABLE_PATH, OUPUT_PATH, SCRIPTS_PATH, SEASONAL_PATH,
                    SHINKAI_ITEMS_DATA, SHINKAI_SHIPS_DATA, SHIP_CLASSES_DB,
                    SHIP_NAMESUFFIX_DB, SHIP_SERIES_DB,
                    SHIP_TYPE_COLLECTIONS_DB, SHIP_TYPES_DB, SHIPS_DATA,
                    SHIPS_DB)
from crawlers import (AkashiListCrawler, SeasonalCrawler, WikiaCrawler,
                      WikiwikiCrawler)
from DBDownloader import DBDownloader
from DiffTool import DiffTool
from ShinkaiLuatable import ShinkaiLuatable
from ShipLuatable import ShipLuatable
from utils import nedb2json
from WikiBot import WikiBot


def LuatableBotTask(fn):
    async def wrapper(*args, **kw):
        print('[{}]: Task starting...'.format(fn.__name__))
        START = time.time()
        await fn(*args, **kw)
        END = time.time()
        print('[{}]: Task total used {}s'.format(
            fn.__name__, round(END - START, 3)))
    return wrapper


class LuatableBotException(Exception):
    def __init__(self, message):
        super().__init__(message)


class LuatableBot:

    def __init__(self):
        self.diff = False
        if not path.isdir(DB_PATH):
            os.mkdir(DB_PATH)
        if not path.isdir(OUPUT_PATH):
            os.mkdir(OUPUT_PATH)
        if not path.isdir(OUPUT_PATH + LUATABLE_PATH):
            os.mkdir(OUPUT_PATH + LUATABLE_PATH)
        if not path.isdir(OUPUT_PATH + JSON_PATH):
            os.mkdir(OUPUT_PATH + JSON_PATH)
        if not path.isdir(OUPUT_PATH + SEASONAL_PATH):
            os.mkdir(OUPUT_PATH + SEASONAL_PATH)

    @LuatableBotTask
    async def FetchDBS(self):
        dbDownloader = DBDownloader()
        dbDownloader.appendTask('https://kcwikizh.github.io/kcdata/ship/all.json', DB_PATH + KCDATA_SHIP_ALL_JSON)
        dbDownloader.appendTask('https://kcwikizh.github.io/kcdata/slotitem/all.json', DB_PATH + KCDATA_SLOTITEM_ALL_JSON)
        dbDownloader.appendTask('https://raw.githubusercontent.com/TeamFleet/WhoCallsTheFleet-DB/master/db/entities.nedb')
        dbDownloader.appendTask('https://raw.githubusercontent.com/TeamFleet/WhoCallsTheFleet-DB/master/db/item_types.nedb')
        dbDownloader.appendTask('https://raw.githubusercontent.com/TeamFleet/WhoCallsTheFleet-DB/master/db/items.nedb')
        dbDownloader.appendTask('https://raw.githubusercontent.com/TeamFleet/WhoCallsTheFleet-DB/master/db/ship_classes.nedb')
        dbDownloader.appendTask('https://raw.githubusercontent.com/TeamFleet/WhoCallsTheFleet-DB/master/db/ship_namesuffix.nedb')
        dbDownloader.appendTask('https://raw.githubusercontent.com/TeamFleet/WhoCallsTheFleet-DB/master/db/ship_series.nedb')
        dbDownloader.appendTask('https://raw.githubusercontent.com/TeamFleet/WhoCallsTheFleet-DB/master/db/ship_types.nedb')
        dbDownloader.appendTask('https://raw.githubusercontent.com/TeamFleet/WhoCallsTheFleet-DB/master/db/ship_type_collections.nedb')
        dbDownloader.appendTask('https://raw.githubusercontent.com/TeamFleet/WhoCallsTheFleet-DB/master/db/ships.nedb')
        await dbDownloader.start()

    @LuatableBotTask
    async def Nedb2json(self):
        nedb2json(DB_PATH + ENTITIES_DB + '.nedb', DB_PATH + ENTITIES_DB + '.json')
        nedb2json(DB_PATH + ITEM_TYPES_DB + '.nedb', DB_PATH + ITEM_TYPES_DB + '.json')
        nedb2json(DB_PATH + ITEMS_DB + '.nedb', DB_PATH + ITEMS_DB + '.json')
        nedb2json(DB_PATH + SHIP_CLASSES_DB + '.nedb', DB_PATH + SHIP_CLASSES_DB + '.json')
        nedb2json(DB_PATH + SHIP_NAMESUFFIX_DB + '.nedb', DB_PATH + SHIP_NAMESUFFIX_DB + '.json')
        nedb2json(DB_PATH + SHIP_SERIES_DB + '.nedb', DB_PATH + SHIP_SERIES_DB + '.json')
        nedb2json(DB_PATH + SHIP_TYPES_DB + '.nedb', DB_PATH + SHIP_TYPES_DB + '.json')
        nedb2json(DB_PATH + SHIP_TYPE_COLLECTIONS_DB + '.nedb', DB_PATH + SHIP_TYPE_COLLECTIONS_DB + '.json')
        nedb2json(DB_PATH + SHIPS_DB + '.nedb', DB_PATH + SHIPS_DB + '.json')

    @LuatableBotTask
    async def AkashiList(self):
        akashiListCrawler = AkashiListCrawler()
        await akashiListCrawler.start()

    @LuatableBotTask
    async def WikiaData(self):
        wikiaCrawler = WikiaCrawler()
        await wikiaCrawler.start()

    @LuatableBotTask
    async def WikiwikiData(self):
        wikiwikiCrawler = WikiwikiCrawler()
        await wikiwikiCrawler.start()

    @LuatableBotTask
    async def SeasonalSubtitles(self):
        seasonalCrawler = SeasonalCrawler()
        await seasonalCrawler.start()

    @LuatableBotTask
    async def ShipLuatable(self):
        shipLuatable = ShipLuatable()
        shipLuatable.start()

    @LuatableBotTask
    async def ShinkaiLuatable(self):
        shinkaiLuatable = ShinkaiLuatable()
        await shinkaiLuatable.start()

    @LuatableBotTask
    async def WikiBotUpdate(self):
        UPDATE_FORCE = environ.get('UPDATE_FORCE')
        if not UPDATE_FORCE and not self.diff:
            print('Skip the kcwiki pages update (no file changes).')
            return
        KCWIKI_UPDATE = environ.get('KCWIKI_UPDATE')
        if KCWIKI_UPDATE:
            KCWIKI_ACCOUNT = environ.get('KCWIKI_ACCOUNT')
            KCWIKI_PASSWORD = environ.get('KCWIKI_PASSWORD')
            wikiBot = WikiBot(KCWIKI_ACCOUNT, KCWIKI_PASSWORD)
            await wikiBot.start()
        else:
            print('Skip the kcwiki pages update (`KCWIKI_UPDATE` not set).')

    @LuatableBotTask
    async def BonusJson(self):
        self.__exec_js(SCRIPTS_PATH + BONUS_JS)

    @LuatableBotTask
    async def DiffFiles(self):
        diffTool = DiffTool()
        self.diff = await diffTool.perform()

    def __exec_lua(self, filename):
        res = subprocess.Popen(['lua', filename], stderr=subprocess.PIPE)
        print('lua ' + filename)
        err = res.stderr.read().decode()
        res.stderr.close()
        if err:
            raise LuatableBotException(err)

    def __exec_js(self, filename):
        res = subprocess.Popen(['node', filename], stderr=subprocess.PIPE)
        print('node ' + filename)
        err = res.stderr.read().decode()
        res.stderr.close()
        if err:
            raise LuatableBotException(err)

    @LuatableBotTask
    async def CheckLuatable(self):
        self.__exec_lua(OUPUT_PATH + LUATABLE_PATH + SHIPS_DATA + '.lua')
        self.__exec_lua(OUPUT_PATH + LUATABLE_PATH + ITEMS_DATA + '.lua')
        self.__exec_lua(OUPUT_PATH + LUATABLE_PATH + SHINKAI_ITEMS_DATA + '.lua')
        self.__exec_lua(OUPUT_PATH + LUATABLE_PATH + SHINKAI_SHIPS_DATA + '.lua')
        self.__exec_lua(OUPUT_PATH + LUATABLE_PATH + AKASHI_LIST_OUTPUT_LUA)
        self.__exec_lua(OUPUT_PATH + LUATABLE_PATH + AIRPOWER_TABLE)
        print('CheckLuatable: All the lua files is valid!')

    async def main(self):
        await self.FetchDBS()
        await self.BonusJson()
        await self.Nedb2json()
        await self.SeasonalSubtitles()
        await self.AkashiList()
        await self.WikiaData()
        await self.WikiwikiData()
        await self.ShipLuatable()
        await self.ShinkaiLuatable()
        await self.CheckLuatable()
        await self.DiffFiles()
        await self.WikiBotUpdate()


if __name__ == '__main__':
    luatableBot = LuatableBot()
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(luatableBot.main())
