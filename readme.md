# Auto-LumberJack

全自动 [LumberJack](https://t.me/gamebot) 小工具, 使用 OpenCV 实现

![](https://i.iij.li/i/20250921/68ced6ff72281.png)

> [!IMPORTANT]
> 图像识别模板来自 2560*1600 分辨率显示器，其他分辨率须自行调整修改，不能开箱即用。
> 使用时建议将游戏窗口放到屏幕中间

工具需要以下依赖库：

- `mss` - 截取屏幕
- `opencv-python` - 图像识别
- `pynput` - 键盘输入监听与鼠标控制

启动终端进入仓库目录，执行以下命令：

- 安装：`pip install -r requirements.txt`

- 启动：`python main.py`

## 按键操作

|  控制按键  | 功能     |
|:------:|--------|
| `方向上键` | 开始自动砍树 |
| `Esc`  | 停止自动砍树 |
|  `j`   | 双击左键   |
|  `l`   | 双击右键   |

参考项目:

- [virtcat/auto-shawarma](https://github.com/virtcat/auto-shawarma)