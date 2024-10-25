"""
@Time   : 2023/11/13 7:27 下午
@Author : edward.gong
@Mail   : edwardgong@gmail.com
@Desc   :
       Mac Install aab to add alias
"""
import os
import sys
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QVBoxLayout,
                             QPushButton, QLabel, QWidget, QLineEdit, QGridLayout)


def get_connected_devices():
    devices_raw = subprocess.check_output(["adb", "devices"])
    device_ids = [
        device.split("\t")[0]
        for device in devices_raw.decode("utf-8").strip().split("\n")[1:]
    ]
    return device_ids


def build_and_install_apks(bundletool_path, aab_path, keystore_path, alias, storepass, keypass):
    apk_output = os.path.splitext(aab_path)[0] + ".apks"

    previous_apk_output = apk_output.replace(".apks", "_previous.apks")

    if os.path.exists(apk_output):
        if os.path.exists(previous_apk_output):
            os.remove(previous_apk_output)
        os.rename(apk_output, previous_apk_output)

    # 更改环境变量PATH
    my_env = os.environ.copy()
    bundletool_dir = os.path.dirname(bundletool_path)
    my_env["PATH"] = my_env["PATH"] + f"{os.pathsep}{bundletool_dir}"

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
        env=my_env  # 使用新环境变量
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


class AABInstaller(QMainWindow):

    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("AAB Installer")
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        open_aab_btn = QPushButton("Select AAB file")
        open_aab_btn.clicked.connect(self.open_aab)
        layout.addWidget(open_aab_btn)

        self.aab_label = QLabel("No AAB file selected.")
        layout.addWidget(self.aab_label)

        open_keystore_btn = QPushButton("Select Keystore")
        open_keystore_btn.clicked.connect(self.open_keystore)
        layout.addWidget(open_keystore_btn)

        self.keystore_label = QLabel("No keystore selected.")
        layout.addWidget(self.keystore_label)

        password_label_layout = QGridLayout()

        password_label_layout.addWidget(QLabel("Store Password:"), 0, 0)
        self.store_password_field = QLineEdit()
        self.store_password_field.setEchoMode(QLineEdit.Password)
        password_label_layout.addWidget(self.store_password_field, 0, 1)

        password_label_layout.addWidget(QLabel("Key Password:"), 1, 0)
        self.key_password_field = QLineEdit()
        self.key_password_field.setEchoMode(QLineEdit.Password)
        password_label_layout.addWidget(self.key_password_field, 1, 1)

        layout.addLayout(password_label_layout)

        # 添加别名的标签和输入字段
        alias_label_layout = QGridLayout()

        alias_label_layout.addWidget(QLabel("Alias:"), 0, 0)
        self.alias_field = QLineEdit()
        alias_label_layout.addWidget(self.alias_field, 0, 1)

        layout.addLayout(alias_label_layout)

        install_apks_btn = QPushButton("Install APKs to devices")
        install_apks_btn.clicked.connect(self.install_apks)
        layout.addWidget(install_apks_btn)

        output_label = QLabel("Install Result:")
        layout.addWidget(output_label)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setCentralWidget(central_widget)

    def open_aab(self):
        aab_path, _ = QFileDialog.getOpenFileName(self, "Open AAB file", "", "AAB files (*.aab)")
        if aab_path:
            print(f"Selected AAB path: {aab_path}")
            self.aab_label.setText(f"AAB file selected: {aab_path}")

    def open_keystore(self):
        keystore_path, _ = QFileDialog.getOpenFileName(self, "Open Keystore", "", "Keystore files (*.jks *.keystore)")
        if keystore_path:
            self.keystore_label.setText(f"Keystore selected: {keystore_path}")

    def install_apks(self):
        aab_path = self.aab_label.text()[18:].strip()
        keystore_path = self.keystore_label.text()[18:].strip()

        storepass = self.store_password_field.text()
        keypass = self.key_password_field.text()

        alias = self.alias_field.text()

        if aab_path and keystore_path and storepass and keypass and alias:
            result = build_and_install_apks(BUNDLETOOL_PATH, aab_path, keystore_path, alias, storepass, keypass)

            # 获取 AAB 文件的前缀
            aab_prefix = os.path.splitext(os.path.basename(aab_path))[0]

            if result:
                self.status_label.setText(f"{aab_prefix} installed successfully")
            else:
                self.status_label.setText(f"Failed to install {aab_prefix}")


def main():
    app = QApplication(sys.argv)
    main_win = AABInstaller()
    main_win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    BUNDLETOOL_PATH = "/Users/edward/Downloads/bundletool-all-1.15.4.jar"
    main()