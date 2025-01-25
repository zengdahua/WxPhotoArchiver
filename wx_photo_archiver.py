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

def on_message(wcf: Wcf, msg: WxMsg):
    """处理接收到的消息"""
    try:
        # 添加调试日志
        logger.info(f"Received message - Type: {msg.type}, Sender: {msg.sender}")
        
        # 只处理图片消息
        if msg.type != 3:  # 3 是图片消息类型
            logger.debug(f"Skipping non-image message type: {msg.type}")
            return

        # 忽略自己发送的消息
        if msg.from_self():
            logger.debug("Skipping self-sent message")
            return

        # 获取发送者信息
        sender = wcf.get_info_by_wxid(msg.sender)
        if not sender:
            logger.warning(f"Cannot get sender info for wxid: {msg.sender}")
            return

        sender_name = sender.name
        logger.info(f"Processing image from: {sender_name}")
        
        # 如果是群消息，添加群名前缀
        if msg.from_group():
            group_info = wcf.get_info_by_wxid(msg.roomid)
            if group_info:
                sender_name = f"{group_info.name}_{sender_name}"
                logger.info(f"Group message from: {group_info.name}")
        
        # 替换文件名中的非法字符
        sender_name = "".join(x for x in sender_name if x.isalnum() or x in (' ', '-', '_'))
        
        # 获取消息时间
        msg_time = datetime.fromtimestamp(msg.timestamp)
        
        # 确保目录存在
        base_path = "C:\\photo"
        date_str = msg_time.strftime("%Y%m%d")
        save_path = os.path.join(base_path, sender_name, date_str)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            logger.info(f"Created directory: {save_path}")
        
        # 生成文件名（使用时间戳确保唯一性）
        file_name = f"{int(time.time())}_{msg_time.strftime('%H%M%S')}.jpg"
        save_file = os.path.join(save_path, file_name)
        
        # 下载并保存图片
        if wcf.download_image(msg, save_file):
            logger.info(f"Successfully saved image from {sender_name} to {save_file}")
        else:
            logger.error(f"Failed to save image from {sender_name}")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)

def main():
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            wcf = Wcf()
            logger.info("Starting WxPhotoArchiver...")
            
            # 等待微信登录
            logger.info("Waiting for WeChat login...")
            while not wcf.is_login():
                time.sleep(1)
            logger.info("WeChat logged in successfully!")
            
            # 启动消息接收
            wcf.enable_receiving_msg()
            logger.info("Started receiving messages...")
            
            # 注册消息回调
            wcf.msg_callback = on_message
            logger.info("Message callback registered...")
            
            # 主循环
            while wcf.is_login():
                time.sleep(1)
            
            break  # 如果正常退出循环，就跳出重试
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Error occurred (attempt {retry_count}/{max_retries}): {str(e)}", exc_info=True)
            
            if retry_count < max_retries:
                logger.info("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                logger.error("Max retries reached. Please make sure WeChatFerry service is running.")
                logger.error("You can try these steps:")
                logger.error("1. Make sure WeChat is running")
                logger.error("2. Run WeChatFerry service (wcf.exe)")
                logger.error("3. Try again")
        finally:
            try:
                wcf.disable_recv_msg()
                wcf.cleanup()
                logger.info("Cleanup completed")
            except:
                pass

if __name__ == "__main__":
    main() 