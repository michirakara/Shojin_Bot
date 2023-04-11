from keep_alive import keep_alive
import os
import discord
import datetime
import time
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import random

TOKEN = os.environ["TOKEN"]
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

prev_api_call = 0


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    #await tree.sync()


@tree.command(name="subtoday", description="今日の提出の結果を返します")
async def subtoday(ctx, username: str):
    global prev_api_call
    if time.time() - prev_api_call < 3:
        await ctx.response.send_message("Please wait at least 3 seconds")
        return
    prev_api_call = time.time()
    unix_time = int(
        datetime.datetime.now(datetime.timezone(
            datetime.timedelta(hours=9))).replace(hour=0,
                                                  minute=0,
                                                  second=0,
                                                  microsecond=0).timestamp())
    url = f"https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user={username}&from_second={unix_time}"
    res = requests.get(url)
    data = res.json()
    ac_cnt = wa_cnt = tle_cnt = re_cnt = ce_cnt = 0
    for js in data:
        i = js["result"]
        if i == "AC":
            ac_cnt += 1
        if i == "WA":
            wa_cnt += 1
        if i == "TLE":
            tle_cnt += 1
        if i == "RE":
            re_cnt += 1
        if i == "CE":
            ce_cnt += 1
    await ctx.response.send_message(
        f"{ac_cnt} AC\n{wa_cnt} WA\n{tle_cnt} TLE\n{re_cnt} RE\n{ce_cnt} CE")


@tree.command(name="ac",
              description="指定された期間からのACの状況を返します(startが指定されていないと今日のAC)")
async def ac(ctx, username: str, start: str = "-1"):
    global prev_api_call
    if time.time() - prev_api_call < 3:
        await ctx.response.send_message("Please wait at least 3 seconds")
        return
    prev_api_call = time.time()
    if start == "-1":
        unix_time = int(
            datetime.datetime.now(
                datetime.timezone(datetime.timedelta(hours=9))).replace(
                    hour=0, minute=0, second=0, microsecond=0).timestamp())
    else:
        unix_time = int(
            datetime.datetime.strptime(start + "+09:00",
                                       "%Y/%m/%d%z").timestamp())
    url = f"https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user={username}&from_second={unix_time}"
    res = requests.get(url)
    data = res.json()

    problemset = set()
    for js in data:
        if js["result"] == "AC":
            problemset.add(js["problem_id"])

    diff = requests.get(
        "https://kenkoooo.com/atcoder/resources/problem-models.json").json()
    diff_list = [0] * 9
    for prob in problemset:
        if prob not in diff:
            diff_list[0] += 1
            continue
        if "difficulty" not in diff[prob]:
            diff_list[0] += 1
            continue
        diff_list[min(max(diff[prob]["difficulty"], 0) // 400, 7) + 1] += 1
    for i in range(9):
        if diff_list[i] == 0:
            diff_list[i] += 0.1
    print(diff_list)

    fig, ax = plt.subplots()
    ax.bar(
        range(9),
        diff_list,
        width=1,
        color=[
            "#404040",
            "#808080",
            "#804000",
            "#008000",
            "#00C0C0",
            "#0000FF",
            "#C0C000",
            "#FF8000",
            "#FF0000",
        ],
    )
    ax.set_xticks(
        range(9),
        [
            "undefined",
            "gray",
            "brown",
            "green",
            "cyan",
            "blue",
            "yellow",
            "orange",
            "red",
        ],
    )
    if max(diff_list) < 5:
        ax.set_ylim(0, 5)
    fig.savefig(f"graph.png")
    await ctx.response.send_message(file=discord.File(f"graph.png"))


@tree.command(
    name="gacha",
    description="指定されたdiffの問題から一つランダムに選んで返します(指定されないと任意のdifficultyの問題)")
async def gacha(ctx, low_diff: int = -1000, high_diff: int = 10000):
    global prev_api_call
    if time.time() - prev_api_call < 3:
        await ctx.response.send_message("Please wait at least 3 seconds")
        return
    prev_api_call = time.time()

    diff = requests.get(
        "https://kenkoooo.com/atcoder/resources/problem-models.json").json()
    problemset = set()
    for key in diff.keys():
        if "difficulty" not in diff[key]:
            continue
        if low_diff <= diff[key]["difficulty"] <= high_diff:
            problemset.add(key)

    if len(problemset) == 0:
        await ctx.response.send_message("problem not found")
        return

    ret = random.choice([*problemset])
    await ctx.response.send_message(
        f"https://atcoder.jp/contests/{'-'.join(ret.split('_')[:-1])}/tasks/{ret}"
    )


keep_alive()
try:
    bot.run(TOKEN)
except:
    os.system("kill 1")
