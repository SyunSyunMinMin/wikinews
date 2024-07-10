import asyncio
import calendar
import config
import datetime
import json
import requests
import time

cur_time = datetime.datetime.now()
S = requests.Session()
URL = "https://ja.wikinews.org/w/api.php"
DATA_PATH = './wikinews/data/wikinews_update.json'

with open(DATA_PATH) as f:
	Lastdata = json.load(f)
last_date = Lastdata["created"]
last_year = last_date["year"]
last_month = last_date["month"]
update_time = datetime.datetime(last_year, last_month, 1)

async def init():
	if ((update_time - cur_time) < datetime.timedelta(days=60)):
		print('現在時刻: ' + cur_time.strftime('%Y年%m月%d日') + ' - 最終更新: ' + update_time.strftime('%Y年%m月') + ' - 更新します')
		await login()
		await monthly_update()
	print('現在時刻: ' + cur_time.strftime('%Y年%m月%d日') + ' - 最終更新: ' + update_time.strftime('%Y年%m月') + ' - 更新の必要はありません')

async def login():
	Result = S.get(url=URL, params={
		"action": "query",
		"format": "json",
		"meta": "tokens",
		"formatversion": "2",
		"type": "login"
	})
	Data = Result.json()
	Token = Data['query']['tokens']['logintoken']
	S.post(URL, data={
		"action": "login",
		"format": "json",
		"lgname": config.username,
		"lgpassword": config.password,
		"lgtoken": Token,
		"formatversion": "2",
	})

async def monthly_update():
	year = last_year
	month = last_month
	for i in range(4):
		if (month + 1) > 12:
			year += 1
			month = 1
			await annual(year)
		else:
			month += 1
		await monthly(year, month)
	Newdata = Lastdata
	Newdata["created"]["year"] = year
	Newdata["created"]["month"] = month
	with open(DATA_PATH, 'w') as f:
		json.dump(Newdata, f, indent=2)

async def annual(year):
	await annual_main_page(year)
	await annual_cat_page(year)
	await annual_tanshin_page(year)

async def annual_main_page(year):
	pagename = f'ウィキニュース:{year}年'
	content = f'<div class="floatright">\n[[ウィキニュース:{year - 1}年|{year - 1}年]] - [[ウィキニュース:{year + 1}年|{year + 1}年]]\n</div>\n{year}年に公開されたウィキニュースの記事索引です。\n'
	content += f'\n*[[ウィキニュース:{year}年/1月]]'
	content += f'\n*[[ウィキニュース:{year}年/2月]]'
	content += f'\n*[[ウィキニュース:{year}年/3月]]'
	content += f'\n*[[ウィキニュース:{year}年/4月]]'
	content += f'\n*[[ウィキニュース:{year}年/5月]]'
	content += f'\n*[[ウィキニュース:{year}年/6月]]'
	content += f'\n*[[ウィキニュース:{year}年/7月]]'
	content += f'\n*[[ウィキニュース:{year}年/8月]]'
	content += f'\n*[[ウィキニュース:{year}年/9月]]'
	content += f'\n*[[ウィキニュース:{year}年/10月]]'
	content += f'\n*[[ウィキニュース:{year}年/11月]]'
	content += f'\n*[[ウィキニュース:{year}年/12月]]'
	content += f'\n\n詳しい内容はそれぞれの月ごとのページをご覧ください。\n\n[[Category:日付別記事一覧|{year}]]'
	await editpage(pagename, content)

async def annual_cat_page(year):
	pagename = f'カテゴリ:{year}年'
	content = '{{Wikipediacat|Category:' + str(year) + '年}}\n{{Commonscat|' + str(year) + '}}\n[[カテゴリ:毎日の記事]]'
	await editpage(pagename, content)

async def annual_tanshin_page(year):
	pagename = f'短信:{year}年'
	content = f'[[ウィキニュース:{year}年|{year}年]]の短信です。\n'
	content += f'\n*[[短信:{year}年/1月]]'
	content += f'\n*[[短信:{year}年/2月]]'
	content += f'\n*[[短信:{year}年/3月]]'
	content += f'\n*[[短信:{year}年/4月]]'
	content += f'\n*[[短信:{year}年/5月]]'
	content += f'\n*[[短信:{year}年/6月]]'
	content += f'\n*[[短信:{year}年/7月]]'
	content += f'\n*[[短信:{year}年/8月]]'
	content += f'\n*[[短信:{year}年/9月]]'
	content += f'\n*[[短信:{year}年/10月]]'
	content += f'\n*[[短信:{year}年/11月]]'
	content += f'\n*[[短信:{year}年/12月]]'
	content += f'\n\n[[Category:{year}年|*短信]]\n[[Category:短信|{year}年]]'
	await editpage(pagename, content)


async def monthly(year, month):
	calen = calendar.monthrange(year, month)
	dayOfWeek = calen[0]
	numOfDays = calen[1]
	youbi = ['月', '火', '水', '木', '金', '土', '日']
	dayOfWeek = youbi[dayOfWeek]
	await create_month_main_page(year, month, generateTemplate(year, month, dayOfWeek, numOfDays, False))
	await create_month_tanshin_page(year, month, generateTemplate(year, month, dayOfWeek, numOfDays, True))
	await create_month_cat_page(year, month)
	for day in range(1, numOfDays + 1):
		await create_day_page(year, month, day)
		await create_cat_page(year, month, day)
		await create_tanshin_page(year, month, day)
	

def generateTemplate(year, month, dayOfWeek, numOfDays, tanshin):

	if month == 1: # 前月
		premonth = '12'
		premonyear = year - 1
	else:
		premonth = month - 1
		premonyear = year

	if month == 12: # 次月
		nextmonth = '1'
		nextmonyear = year + 1
	else:
		nextmonth = month + 1
		nextmonyear = year

	if tanshin: # 短信
		suffix = '\n|分類=短信'
	else:
		suffix = ''
	
	preyear = year - 1
	nextyear = year + 1
	template = '{{' + dayOfWeek + '曜からの月|\n|日数=' + str(numOfDays) + '\n|年=' + str(year) + '\n|月=' + str(month) + '\n|前月=' + str(premonth) + '\n|翌月=' + str(nextmonth) + '\n|前月の年=' + str(premonyear) + '\n|翌月の年=' + str(nextmonyear) + '\n|前年=' + str(preyear) + '\n|翌年=' + str(nextyear) + suffix + '\n}}'

	return template

async def create_month_main_page(year, month, template):
	pagename = f'ウィキニュース:{year}年/{month}月'
	content = '{{メインページお知らせ}}\n' + template
	await editpage(pagename, content)

async def create_month_tanshin_page(year, month, template):
	pagename = f'短信:{year}年/{month}月'
	content = template
	await editpage(pagename, content)

async def create_month_cat_page(year, month):
	pagename = f'カテゴリ:{year}年{month}月'
	content = f'[[Category:{year}年]]'
	await editpage(pagename, content)

async def create_day_page(year, month, day):
	pagename = f'ウィキニュース:{year}年/{month}月/{day}日'
	fulldate = f'{year}年{month}月{day}日'
	content = '<onlyinclude>{|style="clear:right; float:right; background:transparent; border-spacing:0; width:100px"\n<!-- 画像は100px幅以内で -->\n<!--[[ファイル:ファイル名.拡張子|right|100px|代替文]]-->\n|}\n<DynamicPageList>\ncategory=公開中\ncategory='
	content += fulldate
	content += '\nnotcategory=議論中\nsuppresserrors=true\nnamespace=0\n</DynamicPageList></onlyinclude>\n\n[[カテゴリ:'
	content += fulldate
	content += '|*]]'
	await editpage(pagename, content)

async def create_cat_page(year, month, day):
	pagename = f'カテゴリ:{year}年{month}月{day}日'
	content = '{{カテゴリ日付|' + str(year) + str(month) + str(day) + '}}'
	await editpage(pagename, content)

async def create_tanshin_page(year, month, day):
	pagename = f'短信:{year}年/{month}月/{day}日'
	content = '{{短信}}{{短信ヘッダ|' + str(year) + '|' + str(month) + '|' + str(day) + '}}\n<onlyinclude>\n<!--↓短信フォーマット↓\n*（政治/経済/社会/文化/スポーツ/学術/ひと/気象/脇ニュース）短信本文 - [http://（出典URL） 発行者]\n-->\n</onlyinclude>\n{{短信フッタ|' + str(year) + '|' + str(month) + '|' + str(day) + '}}'
	await editpage(pagename, content)

async def editpage(pagename, content, botflag = True):
	Result = S.get(url=URL, params={
		"action": "query",
		"format": "json",
		"meta": "tokens",
		"formatversion": "2",
	})
	Data = Result.json()

	Token = Data['query']['tokens']['csrftoken']
	Result = S.post(URL, data={
		"action": "edit",
		"assert": "user",
		"bot": botflag,
		"format": "json",
		"formatversion": "2",
		"title": pagename,
		"token": Token,
		"text": content,
		"summary": '月次更新'
	})
	EditData = Result.json()
	assert EditData["edit"]["result"] == 'Success', '編集に失敗しました'
	await asyncio.sleep(5)
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
	loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
	loop.run_until_complete(init())
except KeyboardInterrupt as e:
	print('KeyboardInterrupt: 中止します。')
finally:
	loop.close()