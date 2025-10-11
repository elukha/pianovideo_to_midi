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
        self.set_keyboard_position_button.place(x=10, y=90)

        #動画から画像に変換ボタン
        self.start_button = tk.Button(text="動画を画像に変換", command=self.video_to_image)
        self.start_button.place(x=10, y=50)



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


    def detect_notes(self):
        if not self.video_info:
            try: #動画情報がないときに、情報を取得する
                self.video_info = ffmpeg.probe(self.filename)
                self.start_button["text"] = "動画を画像に変換"
                self.start_button["state"] = "normal"
                self.width = self.video_info["streams"][0]["width"]
                self.height = self.video_info["streams"][0]["height"]
                self.fps = self.video_info["streams"][0]["avg_frame_rate"]
                self.avg_fps = float(Fraction(self.fps)) #平均のfpsを計算
            except:
                #エラー時はポップアップし、ボタンを戻す
                messagebox.showerror("Error", "ファイルが選択されていません")

        

        

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
        self.app  = master #Appのインスタンスを保存
        #ウィンドウ設定
        self.title("Setting_position")
        self.geometry("1000x700")
        # 親との結び付け
        self.transient(master)     # タスクバーに別表示しない
        self.grab_set()

        #鍵盤の座標を保存する辞書
        self.key_positions = {}

        #オクターブの距離
        self.octave_offset_x = 0

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

        info_label = tk.Label(self, text="すべての鍵盤が押されてない状態にしてください", font=12)
        info_label.place(x=20, y=550)

        #座標を指定するウィジェットを追加
        self.C4_box = DraggableRectangle(self.canvas, 20, 20, 7, 15, "red")
        self.C4_Sharp_box = DraggableRectangle(self.canvas, 30, 20, 6, 15, "green")
        self.B4_box = DraggableRectangle(self.canvas, 40, 20, 7, 15, "blue")

        #自動で鍵盤の座標を補充するボタン
        self.add_key = tk.Button(self, text="鍵盤を自動追加", command=self.add_all_octaves)
        self.add_key.place(x=20, y=580)

        #鍵盤の色のしきい値を取得するボタン
        self.set_threshold_button = tk.Button(self, text="色のしきい値を取得", command=self.set_threshold)
        self.set_threshold_button.place(x=120, y=580)

        #座標としきい値の色を確定するボタン
        self.confirm_positions_button = tk.Button(self, text="座標を確定", command=self.apply_and_close, bg="coral")
        self.confirm_positions_button.place(x=20, y=620)
    

    def resize_image(self, image_path):
        try:
            self.image_path = image_path

            pil_image = Image.open(image_path)
            image_width, image_height = pil_image.size

            #幅と高さの縮小率を計算
            width_ratio = self.canvas_width / image_width
            height_ratio = self.canvas_height / image_height
            #小さいほうの縮小率を使用
            self.ratio = min(width_ratio, height_ratio)

            #画像の縮小後のサイズを計算
            new_width = int(image_width * self.ratio)
            new_height = int(image_height * self.ratio)

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


    def add_all_octaves(self):
        #移動可能なブロックのクラスを保存する辞書
        self.all_dragable_keys = {}

        #ブロックの座標を保存する辞書を初期化
        self.key_positions = {}

        #最初にユーザーが指定した座標ブロックをcanvasから隠す
        if self.C4_box:
            self.canvas.itemconfig(self.C4_box.item, state="hidden")
            self.canvas.itemconfig(self.C4_Sharp_box.item, state="hidden")
            self.canvas.itemconfigure(self.B4_box.item, state="hidden")

        #初回のC4の実行
        self.add_keys(octave=4)

        #他の生成したいオクターブのリストを作成
        other_octave = [1, 2, 3, 5, 6, 7]
        for oct in other_octave:
            self.add_keys(octave=oct)


    def add_keys(self, octave):
        C_x, C_y = self.C4_box.get_position()
        _, C_Sharp_y = self.C4_Sharp_box.get_position()
        B_x, _ = self.B4_box.get_position()
        canvas_width = self.canvas.winfo_width()

        keys=["C", "C_Sharp", "D", "D_Sharp", "E", "E_None", "F", "F_Sharp", "G", "G_Sharp", "A", "A_Sharp", "B"]
        t = len(keys) - 1 #鍵盤の数

        #C4を基準(0)として、左右に何オクターブずれるか計算
        base_C4_offset_x = octave - 4

        #C4からB4の距離を計算, CとD間の距離を計算
        if not octave==4:
            C4_x, _ = self.all_dragable_keys["C_4"].get_position()
            C4_Sharp_x, _ = self.all_dragable_keys["C_Sharp_4"].get_position()
            B4_x, _ = self.all_dragable_keys["B_4"].get_position()
            self.octave_offset_x = B4_x - C4_x
            
            self.note_distance_x = C4_Sharp_x - C4_x

            #11音に1音追加して12音分の距離にする
            print(f"{self.octave_offset_x + (self.note_distance_x * 2)} = {self.octave_offset_x} + {self.note_distance_x * 2}")
            self.octave_offset_x = self.octave_offset_x + (self.note_distance_x * 2)

        #オクターブのずれを計算
        octave_distance = self.octave_offset_x * base_C4_offset_x

        #1オクターブ分の鍵盤の座標を計算
        for i, note in enumerate(keys):
            note = note + "_" + str(octave)
            x = (1 - (i / t)) * C_x + ((i / t) * B_x) #線形補完で座標を計算

            #オクターブごとに座標をずらす
            x = x + octave_distance

            #Eの半音上はないのでスキップ
            if note == f"E_None_{octave}":
                continue

            #シャープはy座標が違うため分岐
            if "_Sharp" in note:
                w, h = 6, 15
                center_y = C_Sharp_y
                x1 = x - w / 2
                y1 = center_y - h / 2
                x2 = x1 + w
                # 範囲内のみ追加
                if 0 <= x1 and x2 <= canvas_width:
                    self.key_positions[note] = {"position": [x / self.ratio, center_y / self.ratio], "color": None} #縮小前の画像の座標にして辞書に追加
                    self.all_dragable_keys[note] = DraggableRectangle(self.canvas, x1, y1, w, h, "gray")
                else:
                    # クリーンアップ
                    self.key_positions.pop(note, None)
                    if note in self.all_dragable_keys:
                        self.canvas.delete(self.all_dragable_keys[note].item)
                        self.all_dragable_keys.pop(note, None)
            #白鍵の時の処理
            else:
                w, h = 7, 15
                center_y = C_y
                x1 = x - w / 2
                y1 = center_y - h / 2
                x2 = x1 + w
                if 0 <= x1 and x2 <= canvas_width:
                    self.key_positions[note] = {"position": [x / self.ratio, center_y / self.ratio], "color": None} #縮小前の画像の座標にして辞書に追加
                    self.all_dragable_keys[note] = DraggableRectangle(self.canvas, x1, y1, w, h, "gray")
                else:
                    self.key_positions.pop(note, None)
                    if note in self.all_dragable_keys:
                        self.canvas.delete(self.all_dragable_keys[note].item)
                        self.all_dragable_keys.pop(note, None)

        print(self.key_positions)


    def set_threshold(self):
        if not self.key_positions:
            messagebox.showerror("error", "座標を指定してください")
        else:
            for key in self.key_positions:
                img=Image.open(self.image_path)
                #画像をRGBモードに変換
                rgb_img = img.convert("RGB")
                #指定した座標の色を取得
                x = self.key_positions[key]["position"][0]
                y = self.key_positions[key]["position"][1]
                r, g, b = rgb_img.getpixel((x, y))
                #辞書にリスト型で色を追加 [r, g, b]
                self.key_positions[key]["color"] = [r, g, b]
                print(f"{key}の色は{r, g, b}")
 

    def apply_and_close(self):
        if not self.key_positions:
            messagebox.showerror("error", "座標を指定してください")
        else:
            self.app.key_positions = self.key_positions #Appに辞書を渡す
            print(f"座標が確定されました: {self.app.key_positions}")
            self.destroy()
        

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

    def get_position(self): #ブロックの中心の座標を返すメソッド
        position = self.canvas.coords(self.item)
        #ブロックの中央の座標を計算
        x = (position[0] + position[2]) / 2
        y = (position[1] + position[3]) / 2
        return x, y


if __name__ == "__main__":
    App()