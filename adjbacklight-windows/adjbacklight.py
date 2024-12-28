
import screen_brightness_control as sbc
import argparse

def main():
    parser = argparse.ArgumentParser(description="调整显示器亮度")
    parser.add_argument("brightness", type=int, help="亮度值 (0-100)")
    args = parser.parse_args()

    brightness = args.brightness

    if not 0 <= brightness <= 100:
        print("亮度值必须在 0 到 100 之间")
        return

    try:
        sbc.set_brightness(brightness)
        print(f"亮度已设置为 {brightness}")
    except sbc.ScreenBrightnessError as e:
        print(f"调整亮度失败：{e}")
        print("请确保你的显示器支持 DDC/CI 协议，并且已正确连接。")
        print("如果仍然无法工作，尝试使用管理员权限运行此脚本。")
    except Exception as e:
        print(f"发生未知错误：{e}")


if __name__ == "__main__":
    main()
