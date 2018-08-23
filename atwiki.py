"""

根回しサイトatwikiの更新通知プログラム


概要
    atwikiをクローリング,スクレイピングし、更新履歴を参照して、更新があったかどうかをLINEで通知してくれるプログラム。
    前回の結果をtext.txtに保存(命名がダサいが最初にtestでこの名前にしてから面倒で変更してない）。
    python3系を使用。使用するにあたっては、pythonの知識があると望ましい。アルゴリズム入門の言語がrubyからpythonに変わるとかなんとか聞いたので、そこらへんは問題なさそう...？

    使用するにあたって主に調べるべきことは、
    ・web スクレイピング/クローリング の基本
    ・LINE Notify 
    ・pythonモジュールのselenium
    です。その他コードを読んでわからないことがあれば適宜調べましょう。

    launchd(mac用),cron(Linux用)などを使えば、定時自動実行が可能です。おすすめは、Microsoft Azureか、AWSでクラウドサーバーを借りて、cronで自動実行させることです。
    学生ならMicrosoft Azureは一年無料、AWSは学生じゃなくても一年無料、だったと思います。ただし使いすぎると料金がかかるのでよく調べましょう。


45期用に再構成する際の注意点
    atwikiのページ自体が45期用に変わるなら、大幅な変更が求められます。
    コメントは多めに入れているので、読んで検索すればある程度、分かる人には分かると思います。内容を理解しながら書き換えると良いでしょう。
    気になったことは、途中でエラーが発生するとデバッグしても次回seleniumが起動しないことがある、ということです。おそらくseleniumかChromeが正常に終了していないことが原因かと思われますが、正確なことはわかりません。サーバーを再起動させるとちゃんと動きました。
    
    変更するべき点,注意点をとりあえず思いつただけ書いていきます。
    ・まずは接続するatwikiのurlが変わる。
    ・当然パスワードも変わるだろう。更新履歴が見られるならどのアカウントでも構わないが...
    ・line_nofify_tokenは根回し通知用のグループ専用なので、新しくグループを作るなら、トークンを発行し直すこと
    ・相対パスを使ってエラーがでたので、絶対パスに書き直してしまいました（よくないけど...）。自分の環境のパスに変更するか、相対パスに変更してくださいな
    ・サイトの読み込みや接続に時間がかかるので、ちゃんとimplicitly_waitやtime sleepを設定する。短すぎるとエラーになったので試してみるか長めに設定すると良い
    ・今思えば、line()とline_me()なんて2つ関数を作ると重複があって美しく無いので、引数をmessageとtokenの2つにして一つの関数にすればよかったかなと。
    ・......


cronについて
    /etc/crontab を編集することで自動実行ができる。以下のような例を参考にして編集してみよう。
    00 9    * * *   root    /home/ubuntu/work/atwiki/run_atwiki.sh > /home/ubuntu/work/atwiki/atwiki.log 2>&1
    00 18   * * *   root    /home/ubuntu/work/atwiki/run_atwiki.sh > /home/ubuntu/work/atwiki/atwiki.log 2>&1

    ここで、run_atwiki.sh というのは、実行にあたって様々な設定をcrontabに書くとごちゃごちゃしてしまうので、自動実行したいプログラムごとにまとめるためである。
    virtualenv などを使う場合は便利だろう。
    

作成: 44期 村上

"""

import time
import datetime
import sys
import requests
from selenium.common.exceptions import TimeoutException  # error用
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.keys import Keys
# atwikiのパスワード(git hub などで公開する場合、本当はローカルに変数として保存して、それを読み込むのがよい)
user = "44murakami"
passward = "paopao634"


def line(mes):
    """
    LINEグループへの通知用関数
    """
    line_notify_token = 'kUbiMgwQ7XSioEh3Fh7g3Q7kfA181N6kOrkzZpB7HK7'
    line_notify_api = 'https://notify-api.line.me/api/notify'
    #変数messageに文字列をいれて送信。 トークン名の隣に文字が来てしまうので最初に改行
    message = '\n' + mes
    payload = {'message': message}
    headers = {'Authorization': 'Bearer ' + line_notify_token}
    line_notify = requests.post(line_notify_api, data=payload, headers=headers)


def line_me(mes):
    """
    エラー用通知関数
    lineで自分に連絡
    """
    line_notify_token = '1NS7LLBpds6tZRmSEIlBH0m5YhQ3aUQit9nfJd6KveW'
    line_notify_api = 'https://notify-api.line.me/api/notify'
    #変数messageに文字列をいれて送信。 トークン名の隣に文字が来てしまうので最初に改行
    message = '\n' + mes
    payload = {'message': message}
    headers = {'Authorization': 'Bearer ' + line_notify_token}
    line_notify = requests.post(line_notify_api, data=payload, headers=headers)


# 例外が生じた時に、自分に通知する
try:
    #webdriverを使ってスクレイピング
    options = ChromeOptions()
    # ヘッドレスモードを有効にする（次driver = Chrome(executable_path='/chromedriver' ,options=options)の行をコメントアウトすると画面が表示される）
    options.add_argument('--headless')
    # no sandbox で実行しないとcronが使えなかった
    options.add_argument('--no-sandbox')
    # ChromeのWebDriverオブジェクトを作成する
    driver = Chrome(executable_path='/home/ubuntu/bin/chromedriver' ,chrome_options=options)
    # 指定した待ち時間の間、要素が見つかるまで(ロードされるまで)待機するように設定。短いとTimeoutExceptionになった。
    driver.implicitly_wait(10)
    # atwikiのログインページなどはurlの直接入力で表示されないようになっているので、別のページからseleniumでログインページへ遷移する必要がある。
    driver.get("https://www65.atwiki.jp/44teck/pages/1.html")
    print("サイトに接続中...")
    driver.find_element_by_link_text("ログイン").click()
    driver.find_element_by_name("user").send_keys(user)
    driver.find_element_by_name("pass").send_keys(passward)
    driver.find_element_by_name("pass").submit()
    time.sleep(5)
    print("ログイン完了")
    day =  driver.find_elements_by_class_name("plugin_recent_day")
    cont =  driver.find_elements_by_class_name("plugin_recent_day_div")
    recent = driver.find_element_by_class_name("atwiki_plugin_recent_25a1b13fb87d062d43bd6fe2d4a85a7d").text

    #文字列処理（過去2日分の更新情報を通知)
    date_now = datetime.datetime.now()
    his = 'updated!\n'
    for i in range(2):
        tdate_now = datetime.datetime.strptime(day[i].text, '%Y-%m-%d')
        his += '\n'
        his += day[i].text
        if date_now.day == tdate_now.day and date_now.month == tdate_now.month :
            his += "(本日)"
        else:
            his += "("+str((date_now-tdate_now).days)+"日前)"
        his += '\n'
        his += cont[i].text
        his += '\n'

    driver.find_element_by_link_text("ログアウト").click()
    time.sleep(5)
    print("ログアウト完了")

    #前回の結果を読み込む
    with open("/home/ubuntu/work/atwiki/text.txt", encoding="utf-8") as f:
        lines = f.read()
    #前回の結果と同じなら処理終了
    if lines == recent:
        date = date_now.strftime('%Y-%m-%d %H:%M')
        com = date + "現在" + "\n更新はありませんでした"
        line_me(com)
        print("\n" + com)
    #前回の結果と違うなら、ファイルを上書き
    else:
        with open("/home/ubuntu/work/atwiki/text.txt", "w", encoding="utf-8") as f:
            f.write(recent)
        line(his)
        print("\n" + his)

    print("\n実行完了")

# 待機時間が短すぎるとdriverの要素が見つけられなくて（ロードできなくて）エラーになる
except TimeoutException:
    print("\nタイムアウトエラーが発生しました。")
    line("\nタイムアウトエラーが発生しました。")
    line_me("\nタイムアウトエラーが発生しました。")

# その他例外が発生したら通知
except Exception as e :
    print("エラーが発生しました。")
    print(str(e))
    line("エラーが発生しました。")
    line_me("不明なエラー\n"+str(e))

finally:
    driver.quit()
    sys.exit()
    
