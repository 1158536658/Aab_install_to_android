"""
Author: Edward G
Date: 2024-05-01
Description: This is an AAB installation on an Android device.
-- Windows
"""



import os
import sys
import subprocess
import time
import uuid
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QVBoxLayout,
                             QPushButton, QLabel, QWidget, QPlainTextEdit)
from PyQt5.QtCore import QThread, pyqtSignal


def get_connected_devices():
    devices_raw = subprocess.check_output(["adb", "devices"])
    device_ids = [
        device.split("\t")[0]
        for device in devices_raw.decode("utf-8").strip().split("\n")[1:]
    ]
    return device_ids


def generate_keystore(keystore_path, alias, storepass, keypass):
    keytool_command = [
            "C:\\Program Files\\Java\\jdk-20\\bin\\keytool.exe", # 改为你自己本地的
            "-genkey",
            "-v",
            "-keystore",
            keystore_path,
            "-alias",
            alias,
            "-storepass",
            storepass,
            "-keypass",
            keypass,
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "10000",
            "-dname",
            "CN=china, OU=YourOrgUnit, O=YourOrg, L=beijing, S=guangzhou, C=china",
    ]

    try:
        result = subprocess.run(keytool_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return keystore_path

    except subprocess.CalledProcessError as e:
        print(f"Error while generating keystore: {e}, {e.stderr}, {e.stdout}")
        return None

def build_and_install_apks(bundletool_path, aab_path, keystore_path, alias, storepass, keypass):
    apk_output = os.path.splitext(aab_path)[0] + ".apks"
    if os.path.exists(apk_output):
        os.remove(apk_output)

    result = subprocess.run(
        [
            "java",
            "-jar",
            bundletool_path,
            "build-apks",
            f"--bundle={aab_path}",
            f"--output={apk_output}",
            f"--ks={keystore_path}",
            f"--ks-pass=pass:{storepass}",
            f"--ks-key-alias={alias}",
            f"--key-pass=pass:{keypass}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode:
        print(f"Error: Failed to generate APKS from AAB. Error: {result.stderr.decode('utf-8')}")
        return

    print("APKS generated successfully!")

    device_ids = get_connected_devices()

    failed_install_count = 0  # 添加初始化 failed_install_count 为 0 的代码

    for device_id in device_ids:
        result = subprocess.run(
            [
                "java",
                "-jar",
                bundletool_path,
                "install-apks",
                f"--apks={apk_output}",
                f"--device-id={device_id}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if result.returncode:
            print(f"Error: Failed to install APKs on {device_id}. Error: {result.stderr.decode('utf-8')}")
            failed_install_count += 1  # 如果失败，则递增失败计数
        else:
            print(f"APKs installed successfully on {device_id}!")

    if failed_install_count == 0:  # 在此添加代码段
        return "success"
    else:
        return "Error: Failed to install APKs on devices"


def generate_alias():
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    alias = f"my-key-alias-{current_time}"
    return alias


class GenerateKeystoreThread(QThread):
    result_signal = pyqtSignal(str, str)

    def __init__(self, keystore_path, alias, storepass, keypass):
        super().__init__()
        self.keystore_path = keystore_path
        self.alias = f"my-key-alias-{int(time.time())}"
        self.storepass = storepass
        self.keypass = keypass

    def run(self):
        print("Starting generate_keystore thread...")  # 使用 print 函数添加调试输出
        res = generate_keystore(self.keystore_path, self.alias, self.storepass, self.keypass)
        if res:
            print(f"Finished generate_keystore, keystore_path: {res}")
        else:
            print(f"Failed generate_keystore")
        self.result_signal.emit(res, self.alias)


class InstallApksThread(QThread):
    result_signal = pyqtSignal(str)

    def __init__(self, bundletool_path, aab_path, keystore_path, alias, storepass, keypass):
        super().__init__()
        self.bundletool_path = bundletool_path
        self.aab_path = aab_path
        self.keystore_path = keystore_path
        self.alias = alias
        self.storepass = storepass
        self.keypass = keypass

    def run(self):
        # 更改：在调用 build_and_install_apks() 时将 storepass 设置为 KEYSTORE_STOREPASS
        res = build_and_install_apks(self.bundletool_path, self.aab_path, self.keystore_path, self.alias, self.storepass, self.keypass)
        print(f"Finished installing APKs, result: {res}")
        self.result_signal.emit(res)



class AABInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.generated_alias = ''
        self.init_ui()
        jks_filename = f"auto_generated-{uuid.uuid4().hex[:8]}.jks"
        self.keystore_path = os.path.join(os.path.expanduser("~"), "Downloads", jks_filename)

    def init_ui(self):
        self.setWindowTitle("AAB Installer")
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        open_aab_btn = QPushButton("Select AAB file")
        open_aab_btn.clicked.connect(self.open_aab)
        layout.addWidget(open_aab_btn)

        self.aab_text_edit = QPlainTextEdit()
        layout.addWidget(self.aab_text_edit)

        install_apks_btn = QPushButton("Install APKs to devices")
        install_apks_btn.clicked.connect(self.install_apks)
        layout.addWidget(install_apks_btn)

        self.setCentralWidget(central_widget)

    def open_aab(self):
        aab_path, _ = QFileDialog.getOpenFileName(None, "Select AAB file", "", "AAB files (*.aab)")
        self.aab_text_edit.setPlainText(aab_path)

        self.keystore_path = os.path.join(os.path.dirname(aab_path), "auto_generated.jks")
        new_alias = generate_alias()
        self.generate_keystore_thread = GenerateKeystoreThread(self.keystore_path, new_alias, KEYSTORE_STOREPASS,
                                                               KEYSTORE_KEYPASS)
        self.generate_keystore_thread.result_signal.connect(self.on_generate_keystore_finished)
        self.generate_keystore_thread.start()

    def on_generate_keystore_finished(self, keystore_path, alias):
        if keystore_path:
            self.status_label.setText("Keystore generated successfully!")
            self.generated_alias = alias
        else:
            self.status_label.setText("Error: Failed to generate keystore")

    def install_apks(self):
        aab_path = self.aab_text_edit.toPlainText()

        if aab_path and self.generated_alias:
            self.install_apks_thread = InstallApksThread(BUNDLETOOL_PATH, aab_path, self.keystore_path,
                                                         self.generated_alias, KEYSTORE_STOREPASS, KEYSTORE_KEYPASS)
            self.install_apks_thread.result_signal.connect(self.on_install_apks_finished)
            self.install_apks_thread.start()
            self.status_label.setText("Installing APKs...")
        elif not aab_path:
            self.status_label.setText("Please select an AAB file.")
        else:
            self.status_label.setText("Please wait for the keystore to be generated.")

    def on_install_apks_finished(self, result):
        if result == "success":
            self.status_label.setText("Done!")
        else:
            self.status_label.setText("Error: Failed to install APKs on devices")



def main():
    app = QApplication(sys.argv)
    main_win = AABInstaller()
    main_win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    KEYSTORE_STOREPASS = "123456"
    KEYSTORE_KEYPASS = "123456"
    BUNDLETOOL_PATH = r"C:\Users\****\Desktop\budletool-all-1.15.1.jar" # 改为你自己的本地路径
    main()
