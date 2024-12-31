
from websockets import connect
import asyncio
import sys
import sqlite3
import aiosqlite
import json

# Connect to our data folder
cnct = sqlite3.connect("./data.db")

# Using SQL queries in order to create a Table for our data
cursor = cnct.cursor()
cursor.execute("DROP TABLE IF EXISTS trades")
cursor.execute(""" CREATE TABLE trades(
                        id int PRIMARY KEY,
                        time int,
                        quantity int,
                        price float)""")

cursor.execute("CREATE INDEX index_time ON trades(time)")

cnct.commit()
cnct.close()

url = "wss://stream.binance.com:9443/stream?streams=ethusdt@aggTrade/btcusdt@aggTrade"

async def save_down(url):

    # Receiving data from Binance websocket
    async with connect(url) as websocket:
        
        trade_buffer = []
        while True:
            
            # Grabbing Trade information
            data = await websocket.recv()
            data = json.loads(data)
            data = data['data']
            print(data)
            # Grabbing trade ID, Time, Quantity and Price
            trade_buffer.append((data['a'], data['T'], data['q'], data['p']))

            #Inserting data in buffer if length is bigger than 10
            if len(trade_buffer) > 10:

                print("Updating DB")

                async with aiosqlite.connect("./data.db") as db:

                    # Inserting information from trade buffer into db
                    await db.executemany("""INSERT INTO trades
                                            (id, time, quantity, price) VALUES (?,?,?,?)""", trade_buffer)
                    await db.commit()

                    print("commit")
                
                trade_buffer = []


asyncio.run(save_down(url))