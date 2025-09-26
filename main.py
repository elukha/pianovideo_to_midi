import tkinter as tk
from tkinter import filedialog
import ffmpeg
from fractions import Fraction
import subprocess
import os
from tkinter import messagebox
import time
import pathlib


class App:
    def __init__(self):
        #tkinter初期化
        self.root = tk.Tk()
        self.root.title("Pianorole to MIDI")
        self.root.geometry("600x600")
        
        self.create_widget()

        self.root.mainloop()


    
    def create_widget(self):
        #動画情報表示ラベルの定義
        self.label_resolusion = tk.Label(self.root, text="解像度 -")
        self.label_resolusion.place(x=120, y=50)

        self.label_fps = tk.Label(self.root, text="FPS: -")
        self.label_fps.place(x=120, y=70)

        #ファイル参照関連
        self.entry_box = tk.Entry(width=40, state="readonly")
        self.entry_box.place(x=10, y=10)
        
        self.file_dir_button = tk.Button(text="mp4参照", command=self.open_file, width=7)
        self.file_dir_button.place(x=260, y=10)

        self.reset_button = tk.Button(text="リセット", command=self.reset_file, width=4, bg="orange")
        self.reset_button.place(x=320, y=10)

        #鍵盤の位置を設定するウィンドウを開くボタン
        self.set_keyboard_position_button = tk.Button(text="鍵盤の位置を指定", command="")
        self.set_keyboard_position_button.place(x=10, y=50)

        #動画から画像に変換ボタン
        self.start_button = tk.Button(text="動画を画像に変換", command=self.video_to_image)
        self.start_button.place(x=10, y=90)



    def open_file(self):
        self.entry_box.configure(state="normal") #entryboxを書き込み可に設定
        self.idir = "C:\\" #初期ディレクトリ

        self.file_type=[("MP4", "mp4")] #選択できる

        self.filename = filedialog.askopenfilename(filetypes=self.file_type, initialdir=self.idir)

        self.entry_box.insert(tk.END, self.filename)
        self.entry_box.config(state="readonly")



    def reset_file(self):
        self.entry_box.configure(state="normal")
        self.entry_box.delete(0, tk.END)
        self.entry_box.configure(state="readonly")

        #guiの動画情報をリセット
        self.label_resolusion["text"] = "解像度 -"
        self.label_fps["text"] = "FPS -"



    def video_to_image(self):
        #実行中はボタンを無効化
        self.start_button["text"] = "変換中..."
        self.start_button["state"] = "disable"


        try:
            self.video_info = ffmpeg.probe(self.filename) #ffmpegで動画情報を取得
        except:
            #エラー時はポップアップし、ボタンを戻す
            messagebox.showerror("Error", "ファイルが選択されていません")
            self.start_button["text"] = "動画を画像に変換"
            self.start_button["state"] = "normal"

        #現在のディレクトリを取得
        self.working_dir = os.getcwd() + "\\images\\"
        print(self.filename)
        print(self.working_dir)

        #すでに存在する画像を削除
        self.check_dir = pathlib.Path(self.working_dir)
        for self.file in self.check_dir.iterdir():
            if self.file.is_file():
                self.file.unlink()


        #動画情報をピックアップ (解像度、フレームレート)
        self.width = self.video_info["streams"][0]["width"]
        self.height = self.video_info["streams"][0]["height"]
        self.fps = self.video_info["streams"][0]["avg_frame_rate"]
        self.avg_fps = float(Fraction(self.fps)) #平均のfpsを計算
        
        #guiの動画情報を更新
        self.label_resolusion["text"] = f"解像度: {self.width} x {self.height}"
        self.label_fps["text"] = f"fps: {self.avg_fps}"

        #ffmpegのコマンドを設定
        self.ffmpeg_command = f'ffmpeg -i "{self.filename}" -vcodec png "{self.working_dir}%03d.png"'
        subprocess.call(self.ffmpeg_command, shell=True)
        
        time.sleep(0.1)

        #ボタンを元に戻す
        self.start_button["text"] = "動画を画像に変換"
        self.start_button["state"] = "active"

        #変換終了のポップアップ
        messagebox.showinfo("infomation", "変換が正常に終了しました")


if __name__ == "__main__":
    App()