#atwikiの更新通知機能
#launchd,cronなどを使えば、定時実行が可能
import time
import datetime
import sys
import requests
user = "44murakami"
passward = "paopao634"
date_now = datetime.datetime.now()
date = date_now.strftime('%Y-%m-%d')


def line(mes):
    line_notify_token = 'kUbiMgwQ7XSioEh3Fh7g3Q7kfA181N6kOrkzZpB7HK7'
    line_notify_api = 'https://notify-api.line.me/api/notify'
    #変数messageに文字列をいれて送信。 トークン名の隣に文字が来てしまうので最初に改行
    message = '\n' + mes
    payload = {'message': message}
    headers = {'Authorization': 'Bearer ' + line_notify_token}
    line_notify = requests.post(line_notify_api, data=payload, headers=headers)

try:
    # webdriverを使ってスクレイピング
    from selenium.webdriver import Chrome, ChromeOptions
    from selenium.webdriver.common.keys import Keys
    options = ChromeOptions()
    # ヘッドレスモードを有効にする（次driver = Chrome(executable_path='/chromedriver' ,options=options)の行をコメントアウトすると画面が表示される）。
    options.add_argument('--headless')
    # ChromeのWebDriverオブジェクトを作成する。
    driver = Chrome(executable_path='/Users/murakaminaoki/git/atwiki/chromedriver' ,options=options)
    driver.implicitly_wait(2)
    driver.get("https://www65.atwiki.jp/44teck/pages/1.html")
    driver.find_element_by_link_text("ログイン").click()
    driver.find_element_by_name("user").send_keys(user)
    driver.find_element_by_name("pass").send_keys(passward)
    driver.find_element_by_name("login").click()
    time.sleep(10)
    day =  driver.find_elements_by_class_name("plugin_recent_day")
    cont =  driver.find_elements_by_class_name("plugin_recent_day_div")
    #recent = driver.find_element_by_class_name("atwiki_plugin_recent_25a1b13fb87d062d43bd6fe2d4a85a7d").text
except:
    print("例外が発生しました（ネットワークに繋がっているかご確認ください")
    sys.exit()

#文字列処理（過去2日分の更新情報を通知)
his = 'updated!\n'
for i in range(2):
    his += '\n'
    his += day[i].text
    his += '\n'
    his += cont[i].text
    his += '\n'

driver.find_element_by_link_text("ログアウト").click()
time.sleep(6)
driver.quit()




#前回の結果を読み込む
with open("/Users/murakaminaoki/git/atwiki/text.txt", encoding="utf-8") as f:
    lines = f.read()
#前回の結果と同じなら処理終了
if lines == his:
    sys.exit()
#前回の結果と違うなら、ファイルを上書き
else:
    with open("/Users/murakaminaoki/git/atwiki/text.txt", "w", encoding="utf-8") as f:
        f.write(his)
line(his)
