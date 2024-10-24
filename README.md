# AAB懒人工具（适用于 MacOS 和 Windows）

包含用于在 macOS 和 Windows 平台上自动将 Android App Bundle（AAB）安装到 Android 设备的 Python 脚本。

## 系统要求
- Python 3
- PyQt5
- Bundletool（从 https://github.com/google/bundletool/releases 下载最新版本，也可使用代码里的版本）
- Android Debug Bridge（ADB）
- Java Development Kit（JDK）

## 安装

1. 下载此项目:

git clone https://github.com/your-username/aab-installer.git

2. 安装所需的 Python 包：

pip install PyQt5
pip install pyqtwebengine(windows 安装不上可先安装这个库，再安装上面的，mac不需要)

3. 确保 ADB、JDK 和 Bundletool 已在您的系统上正确安装和配置。

4. 将 'mac_install_aab.py' 和 'win_install_aab.py' 中的 'BUNDLETOOL_PATH' 变量设置为已下载的 Bundletool JAR 文件的路径。

## 使用方法

1. 运行适用于您平台的脚本：

- 对于 macOS：使用 Python 运行 'mac_script.py'：

  '''
  python mac_install_aab.py
  '''

- 对于 Windows：使用 Python 运行 'win_install_aab.py'：

  '''
  python win_install_aab.py
  '''

2. 点击 "选择 AAB 文件" 按钮，选择您的 Android App Bundle（AAB）文件。

3. 等待脚本生成用于签名 APK 的密钥库。密钥库生成后，显示消息 "密钥库生成成功！"。

4. 点击 "安装 APK 至设备" 按钮，开始将 APK 安装到所有连接的 Android 设备。

5. 安装完成后，根据安装过程的结果，将显示 "完成！" 或 "错误：无法在设备上安装 APK"。
