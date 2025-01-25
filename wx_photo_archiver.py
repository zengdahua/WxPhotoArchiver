import os
from datetime import datetime
from wcferry import Wcf, WxMsg
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.FileHandler('wx_photo_archiver.log'),
                       logging.StreamHandler()
                   ])
logger = logging.getLogger(__name__)

class WxPhotoArchiver:
    def __init__(self):
        # 初始化 WCF 客户端
        self.wcf = Wcf()
        # 基础保存路径
        self.base_path = "C:\\photo"
        # 注册消息回调
        self.wcf.register_msg_callback(self.handle_message)
        
    def ensure_dir(self, path):
        """确保目录存在，如果不存在则创建"""
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Created directory: {path}")

    def get_save_path(self, sender_name, msg_time):
        """获取保存路径"""
        date_str = msg_time.strftime("%Y%m%d")
        save_path = os.path.join(self.base_path, sender_name, date_str)
        self.ensure_dir(save_path)
        return save_path

    def handle_message(self, msg: WxMsg):
        """处理接收到的消息"""
        try:
            # 只处理图片消息
            if msg.type != 3:  # 3 是图片消息类型
                return

            # 获取发送者信息
            sender = self.wcf.get_info_by_wxid(msg.sender)
            if not sender:
                logger.warning(f"Cannot get sender info for wxid: {msg.sender}")
                return

            sender_name = sender.name
            # 替换文件名中的非法字符
            sender_name = "".join(x for x in sender_name if x.isalnum() or x in (' ', '-', '_'))
            
            # 获取消息时间
            msg_time = datetime.fromtimestamp(msg.timestamp)
            
            # 获取保存路径
            save_path = self.get_save_path(sender_name, msg_time)
            
            # 生成文件名（使用时间戳确保唯一性）
            file_name = f"{int(time.time())}_{msg_time.strftime('%H%M%S')}.jpg"
            save_file = os.path.join(save_path, file_name)
            
            # 下载并保存图片
            if self.wcf.download_image(msg, save_file):
                logger.info(f"Successfully saved image from {sender_name} to {save_file}")
            else:
                logger.error(f"Failed to save image from {sender_name}")

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)

    def run(self):
        """运行监听器"""
        try:
            logger.info("Starting WxPhotoArchiver...")
            self.ensure_dir(self.base_path)
            logger.info("Started listening for messages...")
            # 启动消息监听
            self.wcf.enable_recv_msg()
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}", exc_info=True)
        finally:
            self.wcf.cleanup()
            logger.info("Cleanup completed")

if __name__ == "__main__":
    archiver = WxPhotoArchiver()
    archiver.run() 