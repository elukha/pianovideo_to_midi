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

        #鍵盤の座標を保存する辞書
        self.key_positions = {}

        #キャンバスの作成
        self.canvas_height=450
        self.canvas_width=800
        self.canvas = tk.Canvas(self, bg="lightgray", height=self.canvas_height, width=self.canvas_width, highlightthickness=0, borderwidth=0)
        self.canvas.place(x=10, y=10)

        #変換前の画像のディレクトリパスを取得
        self.images_dir =f"{os.getcwd()}\\images"
        
        #変換した画像を変数に格納
        resized_image, new_width, new_height = self.resize_image(f"{self.images_dir}\\1.png")
        
        #変換に成功したときだけ実行
        if resized_image:
            #canvasのサイズを画像と合わせる
            self.canvas.config(width=new_width, height=new_height)

            #画像を表示, 画像のIDを保存(画像更新時に使用)
            self.image_id = self.canvas.create_image(new_width / 2, new_height / 2, anchor=tk.CENTER, image=resized_image)
            self.canvas.image = resized_image

            #画像を最背面に設定
            self.canvas.lower(self.image_id)

            #ディレクトリをpathlib形式に変換
            pathlib_images_dir = pathlib.Path(self.images_dir)

            #ファイル数(フレーム数)をカウント
            total_frames = sum(1 for item in pathlib_images_dir.iterdir() if item.is_file())

            #スライダーの作成
            self.scale = tk.Scale(self, from_=1, to=total_frames, orient=tk.HORIZONTAL, length=800, troughcolor="skyblue", command=self.update_image)
            self.scale.place(x=10, y=500)

        #座標指定のlabel設定
        color_info_label1 = tk.Label(self, text="赤", font=20, fg="red")
        color_info_label2 = tk.Label(self, text=":C4,", font=20)
        color_info_label3 = tk.Label(self, text="緑", font=20, fg="green")
        color_info_label4 = tk.Label(self, text=":C4#,", font=20)
        color_info_label5 = tk.Label(self, text="青", font=20,fg="blue")
        color_info_label6 = tk.Label(self, text=":B4に移動してください", font=20)
        color_info_label1.place(x=20, y=470)
        color_info_label2.place(x=45, y=470)
        color_info_label3.place(x=90, y=470)
        color_info_label4.place(x=115, y=470)
        color_info_label5.place(x=160, y=470)
        color_info_label6.place(x=185, y=470)

        #座標を指定するウィジェットを追加
        self.C4_box = DraggableRectangle(self.canvas, 20, 20, 7, 15, "red")
        self.C4_Sharp_box = DraggableRectangle(self.canvas, 30, 20, 6, 15, "green")
        self.B4_box = DraggableRectangle(self.canvas, 40, 20, 7, 15, "blue")

        #自動で鍵盤の座標を補充するボタン
        self.add_key = tk.Button(self, text="鍵盤を自動追加", command=self.add_keys)
        self.add_key.place(x=20, y=580)
    

    def resize_image(self, image_path):
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

            return resized_tk_image, new_width, new_height
        
        except FileNotFoundError:
            messagebox.showerror("error", "画像ファイルが見つかりません。\n動画を画像に変換してください")
            self.destroy()
            return None
        except Exception as e:
            messagebox.showerror("error", f"予期せぬエラーが発生しました({{e}})")
            self.destroy()
            return None

    
    def update_image(self, val):
        path = f"{self.images_dir}\\{val}.png"
        resized_image, _, _ = self.resize_image(path)
        #現在の画像を置き換え
        self.canvas.itemconfig(self.image_id, image=resized_image)
        self.canvas.image = resized_image
        self.canvas.lower(self.image_id)


    def add_keys(self):
        #最初にユーザーが指定した座標ブロックをcanvasから隠す
        if self.C4_box:
            self.canvas.itemconfig(self.C4_box.item, state="hidden")
            self.canvas.itemconfig(self.C4_Sharp_box.item, state="hidden")
            self.canvas.itemconfigure(self.B4_box.item, state="hidden")

        C_x, C_y = self.C4_box.get_position()
        _, C_Sharp_y = self.C4_Sharp_box.get_position()
        B_x, _ = self.B4_box.get_position()
        
        octave=4
        keys=["C", "C_Sharp", "D", "D_Sharp", "E", "E_None", "F", "F_Sharp", "G", "G_Sharp", "A", "A_Sharp", "B"]
        t = len(keys) - 1 #鍵盤の数

        #推定した鍵盤のクラスを保存する辞書
        self.all_dragable_keys = {}

        #鍵盤の座標を計算
        for i, note in enumerate(keys):
            note = note + "_" + str(octave)
            x = (1 - (i / t)) * C_x + ((i / t) * B_x) #線形補完で座標を計算

            #Eの半音上はないのでスキップ
            if note == f"E_None_{octave}":
                pass
            #シャープはy座標が違うため分岐
            elif "_Sharp" in note:
                position = [x, C_Sharp_y]
                self.key_positions[note] = position

                #辞書に保存
                x1_s = x - (6 / 2) #center_x - (width / 2)
                y1_s = C_Sharp_y - (15 / 2) #center_y - (height / 2)
                self.all_dragable_keys[f"{note}_{octave}"] = DraggableRectangle(self.canvas, x1_s, y1_s, 6, 15, "gray")


            else: #白鍵の場合の処理
                position = [x, C_y]
                self.key_positions[note] = position

                #辞書に保存
                x1 = x - (7 / 2) #center_x - (width / 2)
                y1 = C_y - (15 / 2)
                self.all_dragable_keys[f"{note}_{octave}"] = DraggableRectangle(self.canvas, x1, y1, 7, 15, "gray")

        print(self.key_positions)




class DraggableRectangle:
    def __init__(self, canvas, x, y, width, height, color):
        self.canvas = canvas
        self.item = canvas.create_rectangle(x, y, x+width, y+height, fill=color)
        self.canvas.tag_bind(self.item, '<Button-1>', self.on_press)
        self.canvas.tag_bind(self.item, '<B1-Motion>', self.on_drag)

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_drag(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y

        x1, y1, x2, y2 = self.canvas.coords(self.item)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # 新しい座標がキャンバスの範囲内かチェックし、移動量を調整
        if x1 + dx < 0:
            dx = -x1
        if y1 + dy < 0:
            dy = -y1
        if x2 + dx > canvas_width:
            dx = canvas_width - x2
        if y2 + dy > canvas_height:
            dy = canvas_height - y2

        self.canvas.move(self.item, dx, dy)
        self.start_x = event.x
        self.start_y = event.y

    def get_position(self):
        position = self.canvas.coords(self.item)
        #ブロックの中央の座標を計算
        x = (position[0] + position[2]) / 2
        y = (position[1] + position[3]) / 2
        return x, y


if __name__ == "__main__":
    App()