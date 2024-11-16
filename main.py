import time
import cv2
import numpy as np
from cv2.typing import MatLike
from pynput.keyboard import Controller, Listener, Key
from mss import mss
import threading
from dataclasses import dataclass
import queue

DEBUG = False

# 自定义左键和右键
LEFT_CLICK = 'j'
RIGHT_CLICK = 'l'

TWIG_MATCH_VAR = 0.7  # 树枝匹配度阈值
END_MATCH_VAR = 0.6  # 游戏结束匹配度阈值


def log(*args):
    if DEBUG:
        print(*args)


@dataclass
class TemplateCache:
    """缓存模板图像及其处理后的版本"""
    left_empty: MatLike
    left_twig: MatLike
    right_twig: MatLike
    end: MatLike

    @classmethod
    def load_templates(cls):
        """预加载所有模板并转换为灰度图"""
        return cls(
            left_empty=cv2.cvtColor(cv2.imread('./img/left_empty.png'), cv2.COLOR_BGR2GRAY),
            left_twig=cv2.cvtColor(cv2.imread('./img/left_twig.png'), cv2.COLOR_BGR2GRAY),
            right_twig=cv2.cvtColor(cv2.imread('./img/right_twig.png'), cv2.COLOR_BGR2GRAY),
            end=cv2.cvtColor(cv2.imread('./img/end.png'), cv2.COLOR_BGR2GRAY)
        )


class ScreenCapture:
    """线程安全的屏幕捕获类"""

    def __init__(self):
        self._local = threading.local()
        self._lock = threading.Lock()
        # 获取初始显示器信息
        with mss() as sct:
            monitor = sct.monitors[0]
            # 计算ROI
            self.roi = {
                'top': monitor['top'] + monitor['height'] // 4,
                'left': monitor['left'] + monitor['width'] // 4,
                'width': monitor['width'] // 2,
                'height': monitor['height'] // 2
            }

    def _get_sct(self):
        """获取当前线程的mss实例"""
        if not hasattr(self._local, 'sct'):
            self._local.sct = mss()
        return self._local.sct

    def grab(self) -> MatLike:
        with self._lock:
            sct = self._get_sct()
            screenshot = np.array(sct.grab(self.roi))[:, :, :3]
            return cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    def cleanup(self):
        """清理资源"""
        if hasattr(self._local, 'sct'):
            self._local.sct.close()


class Game:
    def __init__(self):
        self.keyboard = Controller()
        self.screen = ScreenCapture()
        self.templates = TemplateCache.load_templates()
        self.running = False
        self.left = True
        self.click_queue = queue.Queue()
        self.click_thread = threading.Thread(target=self._click_worker, daemon=True)
        self.click_thread.start()

    @staticmethod
    def match_one(target: MatLike, template: MatLike) -> float:
        """模板匹配"""
        res = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return max_val

    def _click_worker(self):
        """处理点击事件的工作线程"""
        while True:
            try:
                click_func = self.click_queue.get(timeout=1)
                click_func()
                self.click_queue.task_done()
            except queue.Empty:
                continue

    def double_click(self, key: Key):
        """执行双击"""
        self.keyboard.press(key)
        self.keyboard.release(key)
        time.sleep(0.01)
        self.keyboard.press(key)
        self.keyboard.release(key)

    def left_click(self):
        """添加左双击到队列"""
        log('执行操作: 左双击')
        self.click_queue.put(lambda: self.double_click(Key.left))

    def right_click(self):
        """添加右双击到队列"""
        log('执行操作: 右双击')
        self.click_queue.put(lambda: self.double_click(Key.right))

    def detect_position(self) -> bool:
        """检测起始位置"""
        img = self.screen.grab()
        return self.match_one(img, self.templates.left_empty) > 0.9

    def main_loop(self):
        """主游戏循环"""
        try:
            self.left = self.detect_position()
            log(f'起始位置: {"左侧" if self.left else "右侧"}')

            self.running = True
            while self.running:
                time.sleep(0.11)  # 等游戏动画结束
                try:
                    img = self.screen.grab()
                    # 保存
                    cv2.imwrite(f'temp/{time.time_ns()}.png', img)
                    # 选择模板并匹配
                    template = self.templates.left_twig if self.left else self.templates.right_twig
                    match_val = self.match_one(img, template)

                    log(f'检测{"左" if self.left else "右"}边树枝')
                    log('树枝匹配度:', match_val)

                    if match_val < END_MATCH_VAR:
                        if self.match_one(img, self.templates.end) > 0.9:
                            self.running = False
                            print('游戏结束')

                    if match_val > TWIG_MATCH_VAR:
                        if self.left:
                            self.right_click()
                        else:
                            self.left_click()
                        self.left = not self.left
                    else:
                        if self.left:
                            self.left_click()
                        else:
                            self.right_click()

                    log('*' * 20)

                except Exception as e:
                    print(f"循环中发生错误: {e}")
                    time.sleep(0.1)

        except Exception as e:
            print(f"主循环发生错误: {e}")
        finally:
            self.running = False
            self.screen.cleanup()

    def on_press(self, key):
        """按键处理"""
        try:
            if key == Key.esc:
                print('已停止自动砍树')
                self.running = False

            if key == Key.up:
                if not self.running:
                    print('已开始自动砍树')
                    # 在新线程中启动主循环
                    threading.Thread(target=self.main_loop, daemon=True).start()

            if str(key) == f"'{LEFT_CLICK}'":
                self.left_click()
            elif str(key) == f"'{RIGHT_CLICK}'":
                self.right_click()

        except Exception as e:
            log(f"按键处理错误: {e}")


if __name__ == '__main__':
    print('脚本开始运行...\n按<ESC>键停止自动砍树，按<方向上键>开始自动砍树\nJ键 = 双击方向左键, L键 = 双击方向右键')
    game = Game()
    with Listener(on_press=game.on_press) as listener:
        listener.join()
