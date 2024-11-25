import logging


def setup_logging():
    # Configure logging settings
    # ログ設定を構成する
    logging.basicConfig(
        level=logging.DEBUG,  # Set log level to DEBUG (can also be INFO, WARNING, ERROR, CRITICAL)
                             # ログレベルをDEBUGに設定（INFO、WARNING、ERROR、CRITICALも可能）
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set log format
                                                                        # ログフォーマットを設定
        filename='app.log',  # Output to file (if not set, outputs to console)
                           # ファイルに出力（設定しない場合はコンソールに出力）
        filemode='w'  # 'w' for write mode, 'a' for append mode
                     # 'w'は上書きモード、'a'は追記モード
    )

    # Add a StreamHandler to output logs to console
    # コンソールにログを出力するためのStreamHandlerを追加
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Set console log level
                                            # コンソールのログレベルを設定
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger('').addHandler(console_handler)
    logging.debug('logging start...')


# Example: Log a message
# 例：メッセージをログに記録
# logging.info("This is an info message")
