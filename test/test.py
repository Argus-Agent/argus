import tkinter as tk
from queue import Queue

# 后端消息队列
backend_messages = Queue()

# 后端函数
def send_to_backend(msg):
    print("后端收到消息:", msg)
    # 后端处理后生成确认消息
    backend_messages.put(f"确认收到: {msg}")

# 前端 GUI
def send_message():
    msg = entry.get()
    send_to_backend(msg)  # 发送给后端
    entry.delete(0, tk.END)

def check_backend():
    while not backend_messages.empty():
        msg = backend_messages.get()
        listbox.insert(tk.END, msg)
    root.after(500, check_backend)  # 每500ms检查一次

root = tk.Tk()
root.title("异步交互示例")

entry = tk.Entry(root)
entry.pack()

tk.Button(root, text="发送消息", command=send_message).pack()

listbox = tk.Listbox(root, width=50)
listbox.pack()

# 开始轮询
root.after(500, check_backend)
root.mainloop()
