"""
Author: Edward G
Date: 2024-05-01
Description: This is an AAB installation on an Android device.
-- Mac
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


os.environ["PATH"] = os.environ["PATH"] + ":/opt/homebrew/bin"


def get_connected_devices():
    devices_raw = subprocess.check_output(["adb", "devices"])
    device_ids = [
        device.split("\t")[0]
        for device in devices_raw.decode("utf-8").strip().split("\n")[1:]
    ]
    return device_ids


def generate_keystore(keystore_path, alias, storepass, keypass):
    keytool_command = [
        "keytool",
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
        result = subprocess.run(keytool_command, check=True, capture_output=True, text=True)
        return keystore_path

    except subprocess.CalledProcessError as e:
        print(f"Error while generating keystore: {e}, {e.stderr}, {e.stdout}")
        return None


def build_and_install_apks(bundletool_path, aab_path, keystore_path, alias, storepass, keypass):
    apk_output = os.path.splitext(aab_path)[0] + ".apks"

    # 这里删除旧的 apks 文件并重命名当前 apks 文件
    previous_apk_output = apk_output.replace(".apks", "_previous.apks")

    if os.path.exists(apk_output):
        if os.path.exists(previous_apk_output):
            os.remove(previous_apk_output)
        os.rename(apk_output, previous_apk_output)

    bundletool_dir = os.path.dirname(bundletool_path)  # 获取 bundletool 文件所在的目录
    JAVA_EXEC_PATH = '/usr/bin/java'
    result = subprocess.run(
        [
            JAVA_EXEC_PATH,
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
        cwd=bundletool_dir,  # 添加 cwd 参数
    )

    if result.returncode:
        print(f"Error: Failed to generate APKS from AAB. Error: {result.stderr.decode('utf-8')}")
        return False

    print("APKS generated successfully!")

    device_ids = get_connected_devices()
    all_installed = True
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
            all_installed = False
        else:
            print(f"APKs installed successfully on {device_id}!")

    return all_installed


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
        res = build_and_install_apks(self.bundletool_path, self.aab_path, self.keystore_path, self.alias,
                                     self.storepass, self.keypass)
        if res:
            print(f"Finished installing APKs, result: {res}")
            self.result_signal.emit("Done!")
        else:
            print(f"Failed installing APKs, result: {res}")
            self.result_signal.emit("Error: Failed to install APKs on devices")


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

        self.keystore_path = os.path.join(os.path.dirname(aab_path), "../auto_generated.jks")
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

    def on_install_apks_finished(self, message):
        self.status_label.setText(message)


def main():
    app = QApplication(sys.argv)
    main_win = AABInstaller()
    main_win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    KEYSTORE_STOREPASS = "123456"
    KEYSTORE_KEYPASS = "123456"
    BUNDLETOOL_PATH = "/**/Downloads/bundletool-all-1.15.1.jar" # 改为你自己的本地路径
    main()
