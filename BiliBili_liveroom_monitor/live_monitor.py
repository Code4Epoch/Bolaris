# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        live_monitor
# Author:           ydyjya,lucien
# Version:          0.2
# Created:          2021/7/9
# Description:      监控b站某直播间，截取直播的信息流
# Function List:
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya          0.0             2021/7/9    create
#       lucien          0.1             2021/11/20  update for new protocol
#       ydyjya          0.2             2022/1/16   整理结构，解耦程序
# ------------------------------------------------------------------
import json
import time
import asyncio
import requests
import aiohttp
import struct
from aiohttp.client_ws import ClientWebSocketResponse


class BiliBili_live_monitor(object):

    def __init__(self, room_id, message_queue, config):
        self.real_room_id = room_id
        self.token = ''
        self.config = config
        self.message_queue = message_queue

        # bilibili的配置
        self.url = self.config['bilibili_config']['remote']
        self.heartbeat_time = self.config['bilibili_config']['heart_beat_time']
        self.error_time = self.config['bilibili_config']['error_time']
        self.room_conf_url = self.config['bilibili_api']['room_conf_url']
        self.room_info_url = self.config['bilibili_api']['room_info_url']

        # 心跳
        self.latest_heart_beat_time = time.time()

        # 直播间状态判别
        self.live_status = 'preparing'

        # 异步任务列表
        self.task = []

        # 心跳和验证协议值
        self.PROTOCOL_VERSION_RAW_JSON = 0
        self.PROTOCOL_VERSION_HEARTBEAT = 1
        self.PROTOCOL_VERSION_ZLIB_JSON = 2
        self.PROTOCOL_VERSION_BROTLI_JSON = 3

        self.DATAPACK_TYPE_HEARTBEAT = 2
        self.DATAPACK_TYPE_HEARTBEAT_RESPONSE = 3
        self.DATAPACK_TYPE_NOTICE = 5
        self.DATAPACK_TYPE_VERIFY = 7
        self.DATAPACK_TYPE_VERIFY_SUCCESS_RESPONSE = 8

        self.STATUS_INIT = 0
        self.STATUS_CONNECTING = 1
        self.STATUS_ESTABLISHED = 2
        self.STATUS_CLOSING = 3
        self.STATUS_CLOSED = 4
        self.STATUS_ERROR = 5

    def get_livestream(self):
        try:
            asyncio.run(self.__listen_live_room())
        except KeyboardInterrupt as exc:
            print("Quit.")

    # 获取房间token
    def __get_room_token(self):
        room_conf_url = self.room_conf_url % self.real_room_id
        try:
            self.token = json.loads(requests.get(room_conf_url).text)['data']['token']
        except Exception as e:
            print('获取房间token失败！', e)

    # 获取真实房间id
    def __get_real_room_id(self):
        room_info_url = self.room_info_url % self.real_room_id
        try:
            self.real_room_id = str(json.loads(requests.get(room_info_url).text)['data']['room_id'])
        except Exception as e:
            print('获取房间real_room_id失败！', e)

    # 根据url进行监听
    async def __listen_live_room(self):
        print('[Notice] Connecting...')
        self.__get_room_token()
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.url) as ws:
                self.websocket = ws
                print('[Notice] Send Verify Packet')
                # 发送验证信息
                await self.__send_verify_data(ws)
                # 接收验证返回信息
                verify_back = await self.__rece_one_data_packet(ws)
                if verify_back.type == aiohttp.WSMsgType.BINARY:
                    print('[Notice] Validation succeeded')
                else:
                    print('[Notice] Validation failed')
                    raise Exception
                self.tasks = [asyncio.create_task(self.__send_heartbeat(ws)),
                              asyncio.create_task(self.__rece_data_packet(ws))]
                await asyncio.wait(self.tasks)

    # 发送心跳
    async def __send_heartbeat(self, websocket: ClientWebSocketResponse):
        # 发送一个心跳防止被断开连接
        while True:
            await asyncio.sleep(self.heartbeat_time)
            """if time.time() - self.latest_heart_beat_time > self.heartbeat_time + self.error_time:
                await self.websocket.close()
                self.tasks = [asyncio.create_task(self.__listen_live_room())]
                self.latest_heart_beat_time = time.time()
                print('[Notice] try reconnect')
                await asyncio.wait(self.tasks)
                return"""
            HEARTBEAT = self.__pack(b'[object Object]', self.PROTOCOL_VERSION_HEARTBEAT, self.DATAPACK_TYPE_HEARTBEAT)
            await websocket.send_bytes(HEARTBEAT)
            print('[Notice] Sent HeartBeat')

    # 单次接收信息，并返回
    async def __rece_one_data_packet(self, websocket: ClientWebSocketResponse):
        return await websocket.receive()

    # 持续接收信息
    async def __rece_data_packet(self, websocket: ClientWebSocketResponse):
        while True:
            recv_text = await websocket.receive()
            self.message_queue.put(recv_text.data)

    # 发送验证包
    async def __send_verify_data(self, websocket: ClientWebSocketResponse):
        verifyData = {"uid": 0, "roomid": int(self.real_room_id),
                      "protover": 3, "platform": "web", "type": 2, "key": self.token}
        data = self.__pack(json.dumps(verifyData).encode(), self.PROTOCOL_VERSION_HEARTBEAT, self.DATAPACK_TYPE_VERIFY)
        await websocket.send_bytes(data)

    # 打包到字节流，方法来自BILIBILI-API作者moyu
    @staticmethod
    def __pack(data: bytes, protocol_version: int, datapack_type: int):
        sendData = bytearray()
        sendData += struct.pack(">H", 16)
        sendData += struct.pack(">H", protocol_version)
        sendData += struct.pack(">I", datapack_type)
        sendData += struct.pack(">I", 1)
        sendData += data
        sendData = struct.pack(">I", len(sendData) + 4) + sendData
        return bytes(sendData)
