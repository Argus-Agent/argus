#!/usr/bin/env python3
"""
CodeAgent基本功能测试
用于验证Agent和Code执行器是否正常工作
"""
import os
import sys
# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_code_executor():
    """测试代码执行器"""
    print("=== 测试代码执行器 ===")
    
    try:
        from core.computer.code import Code
        code_executor = Code()
        
        print(f"可用语言: {code_executor.language_list}")
        
        # 测试Python代码执行
        print("\n测试Python代码执行...")
        result_queue = code_executor.run("python", """
print("Hello from CodeAgent!")
import time
time.sleep(0.5)
print("测试完成!")
result = 2 + 3
print(f"2 + 3 = {result}")
        """)
        
        # 读取结果
        results = []
        while not result_queue.empty() or code_executor.is_running():
            try:
                result = result_queue.get(timeout=1)
                results.append(result)
                print(f"输出: {result}")
            except:
                if not code_executor.is_running():
                    break
        
        print(f"执行完成，共收到 {len(results)} 条结果")
        return True
        
    except Exception as e:
        print(f"代码执行器测试失败: {e}")
        return False

def test_agent_init():
    """测试Agent初始化"""
    print("\n=== 测试Agent初始化 ===")
    
    try:
        from core.llm.code.agent import CodeAgent
        agent = CodeAgent()
        
        print(f"Agent模型: {agent.model}")
        print(f"API Base: {agent.api_base}")
        print(f"系统提示长度: {len(agent.SYSTEM_PROMPT)} 字符")
        
        return True
        
    except Exception as e:
        print(f"Agent初始化测试失败: {e}")
        return False

def test_code_parser():
    """测试代码解析器"""
    print("\n=== 测试代码解析器 ===")
    
    try:
        from core.llm.code.code_parser import CodeParser
        
        test_text = """
这是一个测试文本

```python
def hello():
    print("Hello World!")
    return 42
```

```bash
echo "Hello Bash"
```
        
结束文本
        """
        
        codes = CodeParser(test_text)
        print(f"解析出 {len(codes)} 个代码块:")
        
        for i, code in enumerate(codes):
            print(f"代码块 {i}: 语言={code['lang']}, 内容长度={len(code['code'])}")
            print(f"内容预览: {code['code'][:50]}...")
        
        return len(codes) == 2
        
    except Exception as e:
        print(f"代码解析器测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("CodeAgent 基本功能测试")
    print("=" * 50)
    
    tests = [
        ("代码执行器", test_code_executor),
        ("Agent初始化", test_agent_init), 
        ("代码解析器", test_code_parser),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"{test_name}测试出现异常: {e}")
            results[test_name] = False
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    
    for test_name, success in results.items():
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 所有测试通过！可以启动UI界面了。")
        print("运行命令: python run_ui.py")
    else:
        print("\n⚠️  部分测试失败，请检查相关配置。")
    
    return all_passed

if __name__ == "__main__":
    main()
