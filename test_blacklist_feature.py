#!/usr/bin/env python3
"""
测试黑名单功能
"""

import sqlite3
import logging
from datetime import datetime
from database import Database

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_blacklist_functionality():
    """测试黑名单功能"""
    print("🧪 开始测试黑名单功能...")
    
    # 创建测试数据库
    db = Database("test_blacklist.db")
    
    # 测试数据
    test_user_id = 123456789
    test_user_name = "测试用户"
    test_username = "testuser"
    
    print("\n1. 测试添加用户到黑名单...")
    success = db.add_to_blacklist(
        user_id=test_user_id,
        user_name=test_user_name,
        username=test_username,
        leave_count=2,
        reason="测试多次离群"
    )
    print(f"   添加结果: {'✅ 成功' if success else '❌ 失败'}")
    
    print("\n2. 测试检查用户是否在黑名单中...")
    is_blacklisted = db.is_user_blacklisted(test_user_id)
    print(f"   检查结果: {'✅ 在黑名单中' if is_blacklisted else '❌ 不在黑名单中'}")
    
    print("\n3. 测试获取黑名单列表...")
    blacklist = db.get_blacklist()
    print(f"   黑名单用户数: {len(blacklist)}")
    if blacklist:
        for user in blacklist:
            print(f"   - 用户ID: {user[0]}, 姓名: {user[1]}, 用户名: @{user[2]}, 原因: {user[3]}")
    
    print("\n4. 测试获取黑名单数量...")
    count = db.get_blacklist_count()
    print(f"   黑名单数量: {count}")
    
    print("\n5. 测试从黑名单移除用户...")
    removed = db.remove_from_blacklist(test_user_id)
    print(f"   移除结果: {'✅ 成功' if removed else '❌ 失败'}")
    
    print("\n6. 再次检查用户是否在黑名单中...")
    is_blacklisted_after = db.is_user_blacklisted(test_user_id)
    print(f"   检查结果: {'❌ 仍在黑名单中' if is_blacklisted_after else '✅ 已从黑名单移除'}")
    
    print("\n7. 测试重复添加用户...")
    # 重新添加用户
    db.add_to_blacklist(test_user_id, test_user_name, test_username, 3, "重复测试")
    # 再次添加相同用户（应该更新而不是重复）
    db.add_to_blacklist(test_user_id, "更新的用户名", test_username, 4, "更新测试")
    
    blacklist_after_update = db.get_blacklist()
    print(f"   更新后黑名单数量: {len(blacklist_after_update)}")
    if blacklist_after_update:
        updated_user = blacklist_after_update[0]
        print(f"   更新后用户信息: {updated_user[1]}, 离群次数: {updated_user[4]}")
    
    print("\n🧹 清理测试数据...")
    db.remove_from_blacklist(test_user_id)
    
    # 删除测试数据库文件
    import os
    try:
        os.remove("test_blacklist.db")
        print("   测试数据库已删除")
    except:
        print("   测试数据库删除失败")
    
    print("\n✅ 黑名单功能测试完成！")

def simulate_user_leave_scenario():
    """模拟用户离群场景"""
    print("\n🎭 模拟用户离群场景...")
    
    # 模拟用户活动日志
    user_activity_log = {}
    
    def simulate_user_leave(user_id, user_name, username):
        """模拟用户离开"""
        current_time = datetime.now()
        
        if user_id not in user_activity_log:
            user_activity_log[user_id] = {
                'user_name': user_name,
                'username': username,
                'join_times': [],
                'leave_times': [],
                'total_joins': 0,
                'total_leaves': 0
            }
        
        # 记录离开
        user_activity_log[user_id]['leave_times'].append(current_time)
        user_activity_log[user_id]['total_leaves'] += 1
        
        leave_count = user_activity_log[user_id]['total_leaves']
        print(f"   用户 {user_name} 第 {leave_count} 次离开群组")
        
        # 检查是否需要加入黑名单
        if leave_count >= 2:
            print(f"   ⚠️  用户 {user_name} 离群次数达到 {leave_count} 次，应加入黑名单")
            return True
        else:
            print(f"   ℹ️  用户 {user_name} 离群次数为 {leave_count} 次，暂不加入黑名单")
            return False
    
    # 模拟场景
    test_user_id = 987654321
    test_user_name = "频繁离群用户"
    test_username = "frequent_leaver"
    
    print(f"\n模拟用户: {test_user_name} (@{test_username})")
    
    # 第一次离开
    print("\n第一次离开:")
    should_blacklist_1 = simulate_user_leave(test_user_id, test_user_name, test_username)
    
    # 第二次离开
    print("\n第二次离开:")
    should_blacklist_2 = simulate_user_leave(test_user_id, test_user_name, test_username)
    
    # 第三次离开
    print("\n第三次离开:")
    should_blacklist_3 = simulate_user_leave(test_user_id, test_user_name, test_username)
    
    print(f"\n📊 模拟结果总结:")
    print(f"   - 第1次离开: {'需要加入黑名单' if should_blacklist_1 else '不需要加入黑名单'}")
    print(f"   - 第2次离开: {'需要加入黑名单' if should_blacklist_2 else '不需要加入黑名单'}")
    print(f"   - 第3次离开: {'需要加入黑名单' if should_blacklist_3 else '不需要加入黑名单'}")

if __name__ == "__main__":
    print("🚀 黑名单功能测试开始")
    print("=" * 50)
    
    try:
        # 测试数据库功能
        test_blacklist_functionality()
        
        # 模拟用户场景
        simulate_user_leave_scenario()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()