import tkinter as tk
from tkinter import filedialog
import ffmpeg
from fractions import Fraction
import subprocess
import os
from tkinter import messagebox
import time
import pathlib
from PIL import Image, ImageTk


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
        self.set_keyboard_position_button = tk.Button(text="鍵盤の位置を指定", command=self.open_Setting_position)
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
        self.images_dir = os.getcwd() + "\\images\\"
        print(self.filename)
        print(self.images_dir)

        #すでに存在する画像を削除
        self.check_dir = pathlib.Path(self.images_dir)
        for file in self.check_dir.iterdir():
            if file.is_file():
                file.unlink()


        #動画情報をピックアップ (解像度、フレームレート)
        self.width = self.video_info["streams"][0]["width"]
        self.height = self.video_info["streams"][0]["height"]
        self.fps = self.video_info["streams"][0]["avg_frame_rate"]
        self.avg_fps = float(Fraction(self.fps)) #平均のfpsを計算
        
        #guiの動画情報を更新
        self.label_resolusion["text"] = f"解像度: {self.width} x {self.height}"
        self.label_fps["text"] = f"fps: {self.avg_fps}"

        #ffmpegのコマンドを設定
        self.ffmpeg_command = f'ffmpeg -i "{self.filename}" -vcodec png "{self.images_dir}%01d.png"'
        subprocess.call(self.ffmpeg_command, shell=True)
        
        time.sleep(0.1)

        #ボタンを元に戻す
        self.start_button["text"] = "動画を画像に変換"
        self.start_button["state"] = "active"

        #変換終了のポップアップ
        messagebox.showinfo("infomation", "変換が正常に終了しました")


    def open_Setting_position(self):
        # 既に開いている場合はフォーカス
        if hasattr(self, "setting_win") and self.setting_win.winfo_exists():
            self.setting_win.lift()
            self.setting_win.focus_set()
            return
        # 親(self.root)を持つ Toplevel を生成
        self.setting_win = Setting_position(self.root)


class Setting_position(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        #ウィンドウ設定
        self.title("Setting_position")
        self.geometry("1000x700")
        # 親との結び付け
        self.transient(master)     # タスクバーに別表示しない
        self.grab_set()

        #キャンバスの作成
        self.canvas_height=400
        self.canvas_width=800
        self.canvas = tk.Canvas(self, bg="lightgray", height=self.canvas_height, width=self.canvas_width)
        self.canvas.place(x=10, y=10)

        #変換前の画像のパスを取得
        images_path =f"{os.getcwd()}\\images\\1.png"
        
        #変換した画像を変数に格納
        resized_image = self._resize_image(images_path)
        
        if resized_image:
            #画像を表示
            self.canvas.create_image(self.canvas_width / 2, self.canvas_height / 2, anchor=tk.CENTER, image=resized_image)
            
            self.canvas.image = resized_image

            #スライダーの作成
            self.scale = tk.Scale(self, from_=0, to=100)
    

    def _resize_image(self, image_path):
        try:
            pil_image = Image.open(image_path)
            image_width, image_height = pil_image.size

            #幅と高さの縮小率を計算
            width_ratio = self.canvas_width / image_width
            height_ratio = self.canvas_height / image_height
            #小さいほうの縮小率を使用
            ratio = min(width_ratio, height_ratio)

            #画像の縮小後のサイズを計算
            new_width = int(image_width * ratio)
            new_height = int(image_height * ratio)

            #Pillowで画像をリサイズ
            resized_pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            #tkinter用の形式に変換
            resized_tk_image = ImageTk.PhotoImage(resized_pil_image)

            return resized_tk_image
        
        except FileNotFoundError:
            messagebox.showerror("error", "動画を画像に変換してください")
            return None
        except Exception as e:
            messagebox.showerror("error", f"予期せぬエラーが発生しました({{e}})")
            return None



if __name__ == "__main__":
    App()