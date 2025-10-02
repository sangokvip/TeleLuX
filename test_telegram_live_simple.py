#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram机器人真实集成测试 - 简化版本
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramBotTester:
    """Telegram机器人集成测试器"""
    
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.admin_chat_id = Config.ADMIN_CHAT_ID or Config.TELEGRAM_CHAT_ID
        self.application = None
        self.test_results = {}
        self.message_count = 0
        
    async def start_bot(self):
        """启动测试机器人"""
        try:
            print("正在启动Telegram测试机器人...")
            print(f"Bot Token: {self.bot_token[:10]}...")
            print(f"Admin Chat ID: {self.admin_chat_id}")
            
            # 创建应用
            self.application = Application.builder().token(self.bot_token).build()
            
            # 添加消息处理器
            message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_test_message)
            self.application.add_handler(message_handler)
            
            # 启动机器人
            await self.application.initialize()
            await self.application.start()
            
            print("机器人启动成功！")
            return True
            
        except Exception as e:
            print(f"机器人启动失败: {e}")
            traceback.print_exc()
            return False
    
    async def handle_test_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理测试消息"""
        try:
            self.message_count += 1
            message_text = update.message.text if update.message else ""
            chat_id = update.effective_chat.id
            user_name = update.effective_user.username or update.effective_user.first_name
            chat_type = update.effective_chat.type
            
            print(f"[{self.message_count}] 收到消息: '{message_text}' 来自: {user_name} (Chat ID: {chat_id}, 类型: {chat_type})")
            
            # 测试1: 基本回复
            if message_text.lower() == "测试":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="机器人基本回复功能正常！"
                )
                self.test_results['basic_reply'] = True
                print("基本回复测试完成")
            
            # 测试2: Twitter URL识别
            elif "twitter.com" in message_text.lower() or "x.com" in message_text.lower():
                tweet_id = self.extract_tweet_id(message_text)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"检测到Twitter URL，推文ID: {tweet_id if tweet_id else '无法提取'}"
                )
                self.test_results['twitter_url'] = True
                print("Twitter URL识别测试完成")
            
            # 测试3: 特殊指令"27"
            elif message_text == "27":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="特殊指令'27'识别正常！"
                )
                self.test_results['special_command'] = True
                print("特殊指令测试完成")
            
            # 测试4: HTML格式化
            elif message_text.lower() == "html测试":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="<b>粗体</b> 和 <i>斜体</i> 测试",
                    parse_mode='HTML'
                )
                self.test_results['html_formatting'] = True
                print("HTML格式化测试完成")
            
            # 测试5: 转发到群组
            elif message_text.lower() == "转发测试":
                if chat_type == 'private':
                    # 转发到配置的群组
                    target_chat_id = Config.TELEGRAM_CHAT_ID
                    await context.bot.send_message(
                        chat_id=target_chat_id,
                        text=f"来自私聊的转发测试消息\n发送者: {user_name}\n原消息: {message_text}"
                    )
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"消息已转发到群组 {target_chat_id}"
                    )
                    self.test_results['forward_to_group'] = True
                    print("转发到群组测试完成")
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="当前已在群组中，无需转发"
                    )
            
            # 测试6: 获取机器人信息
            elif message_text.lower() == "机器人信息":
                bot_info = await context.bot.get_me()
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"机器人信息:\n"
                         f"名称: {bot_info.first_name}\n"
                         f"用户名: @{bot_info.username}\n"
                         f"ID: {bot_info.id}"
                )
                self.test_results['bot_info'] = True
                print("机器人信息测试完成")
            
            # 测试7: 群组消息处理
            elif message_text.lower() == "群组测试":
                if chat_type == 'group' or chat_type == 'supergroup':
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"群组消息处理正常！\n"
                             f"群组ID: {chat_id}\n"
                             f"消息类型: {chat_type}"
                    )
                    self.test_results['group_message'] = True
                    print("群组消息测试完成")
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="当前是私聊，请在群组中测试"
                    )
            
            else:
                # 默认回复 - 提供测试命令列表
                help_text = (
                    "可用测试命令:\n"
                    "• 发送 测试 - 测试基本回复\n"
                    "• 发送 27 - 测试特殊指令\n"
                    "• 发送 Twitter URL - 测试URL识别\n"
                    "• 发送 html测试 - 测试HTML格式化\n"
                    "• 发送 转发测试 - 测试转发到群组\n"
                    "• 发送 机器人信息 - 获取机器人信息\n"
                    "• 发送 群组测试 - 测试群组消息处理\n"
                    "\n或直接发送任意消息测试基本响应"
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=help_text
                )
                
        except Exception as e:
            print(f"处理消息时出错: {e}")
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"处理消息时出错: {str(e)[:100]}"
                )
            except:
                pass
    
    def extract_tweet_id(self, text):
        """从文本中提取推文ID"""
        import re
        patterns = [
            r'(?:twitter|x)\.com/\w+/status/(\d+)',
            r'/status/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    async def send_test_message_to_admin(self):
        """向管理员发送测试消息"""
        try:
            print(f"正在向管理员发送测试消息...")
            await self.application.bot.send_message(
                chat_id=self.admin_chat_id,
                text="""Telegram机器人集成测试开始！

测试命令：
• 发送 测试 - 测试基本回复功能
• 发送 27 - 测试特殊指令
• 发送 Twitter URL - 测试URL识别
• 发送 html测试 - 测试HTML格式化
• 发送 转发测试 - 测试转发到群组
• 发送 机器人信息 - 获取机器人信息
• 发送 群组测试 - 测试群组消息处理

测试将在60秒后自动结束。""",
                parse_mode='HTML'
            )
            print("测试消息发送成功！")
            return True
        except Exception as e:
            print(f"发送测试消息失败: {e}")
            return False
    
    async def run_integration_test(self):
        """运行完整的集成测试"""
        print("=" * 60)
        print("Telegram机器人集成测试")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 初始化测试
        self.test_results = {
            'basic_reply': False,
            'twitter_url': False,
            'special_command': False,
            'html_formatting': False,
            'forward_to_group': False,
            'bot_info': False,
            'group_message': False
        }
        self.message_count = 0
        
        # 启动机器人
        if not await self.start_bot():
            return False
        
        # 发送测试消息
        if not await self.send_test_message_to_admin():
            print("无法发送测试消息，继续等待用户输入...")
        
        print("\n机器人已启动，正在等待消息...")
        print("请在Telegram中向机器人发送测试命令")
        print("测试将在60秒后自动结束")
        print("按 Ctrl+C 可以提前结束测试\n")
        
        try:
            # 启动机器人监听
            await self.application.updater.start_polling()
            
            # 运行60秒
            await asyncio.sleep(60)
            
            print("测试时间结束，正在停止机器人...")
            
        except KeyboardInterrupt:
            print("用户中断测试")
        except Exception as e:
            print(f"测试过程中出错: {e}")
        finally:
            # 停止机器人
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            except:
                pass
        
        return True
    
    def print_test_results(self):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("集成测试结果:")
        print("=" * 60)
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "通过" if result else "未测试"
            test_name_cn = {
                'basic_reply': "基本回复",
                'twitter_url': "Twitter URL识别", 
                'special_command': "特殊指令",
                'html_formatting': "HTML格式化",
                'forward_to_group': "转发到群组",
                'bot_info': "机器人信息",
                'group_message': "群组消息处理"
            }.get(test_name, test_name)
            
            print(f"{status} {test_name_cn}")
            if result:
                passed += 1
        
        print(f"\n总计: {passed}/{total} 项测试完成")
        print(f"收到消息总数: {self.message_count}")
        
        if passed == total:
            print("所有测试完成！机器人功能正常")
        elif passed > 0:
            print(f"部分测试完成 ({passed}/{total})")
        else:
            print("未收到任何测试消息")
        
        print("\n如果某些测试未通过，请:")
        print("1. 检查机器人是否启用了正确的权限")
        print("2. 确认机器人已被添加到目标群组")
        print("3. 验证网络连接是否正常")

async def main():
    """主函数"""
    print("开始Telegram机器人真实集成测试")
    print("=" * 60)
    
    try:
        # 验证配置
        print("正在验证配置...")
        Config._init_configs()
        
        if not Config.TELEGRAM_BOT_TOKEN:
            print("错误: Telegram Bot Token未配置")
            return 1
        
        if not Config.TELEGRAM_CHAT_ID:
            print("错误: Telegram Chat ID未配置")
            return 1
        
        print("配置验证通过")
        print(f"机器人将连接到: Chat ID {Config.TELEGRAM_CHAT_ID}")
        
        # 创建测试器并运行测试
        tester = TelegramBotTester()
        
        # 运行集成测试
        await tester.run_integration_test()
        
        # 打印结果
        tester.print_test_results()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 0
    except Exception as e:
        print(f"测试失败: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)