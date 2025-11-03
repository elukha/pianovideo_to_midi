import tkinter as tk
from tkinter import filedialog
import ffmpeg
from fractions import Fraction
import subprocess
import os
from tkinter import messagebox
import pathlib
from PIL import Image, ImageTk
import pretty_midi


class App:
    def __init__(self):
        #tkinter初期化
        self.root = tk.Tk()
        self.root.title("Pianorole to MIDI")
        self.root.geometry("600x600")

        #鍵盤の座標と色のしきい値を格納する辞書を初期化
        self.key_positions = {}
        
        #画像ディレクトリの取得
        self.images_dir = os.getcwd() + "\\images\\"

        #色の差の許容範囲 (0-765の値, 30程度を推奨)
        self.color_tolerance = 30

        #右手と左手の色を受け取る用
        self.left_color = None
        self.right_color = None
        #2種の色があるモードか
        self.is_two_color_mode = False
        
        self.create_widget()

        self.root.mainloop()


    
    def create_widget(self):
        #動画情報表示ラベルの定義
        self.label_resolusion = tk.Label(self.root, text="解像度 -")
        self.label_resolusion.place(x=120, y=50)

        self.label_fps = tk.Label(self.root, text="FPS: -")
        self.label_fps.place(x=120, y=70)

        #ファイル参照関連
        self.entry_box = tk.Entry(self.root, width=40, state="readonly")
        self.entry_box.place(x=10, y=10)
        
        self.file_dir_button = tk.Button(self.root, text="mp4参照", command=self.open_file, width=7)
        self.file_dir_button.place(x=260, y=10)

        self.reset_button = tk.Button(self.root, text="リセット", command=self.reset_file, width=4, bg="orange")
        self.reset_button.place(x=320, y=10)

        #動画から画像に変換ボタン
        self.video_to_image_button = tk.Button(self.root, text="動画を画像に変換", command=self.video_to_image)
        self.video_to_image_button.place(x=10, y=50)
        
        #鍵盤の位置を設定するウィンドウを開くボタン
        self.set_keyboard_position_button = tk.Button(self.root, text="鍵盤の位置を指定", command=self.open_Setting_position)
        self.set_keyboard_position_button.place(x=10, y=90)

        #分析開始ボタン
        self.detect_notes_button = tk.Button(self.root, text="MIDI化開始", command=self.detect_notes)
        self.detect_notes_button.place(x=10, y=130)

        #色の差の許容範囲のスライダー
        self.scale = tk.Scale(self.root, from_=0, to=765, length=400, orient=tk.HORIZONTAL, label="色の差の許容範囲(30を推奨)", command=self.color_tolerance_setting)
        self.scale.place(x=10, y=170)
        self.scale.set(30) #初期値を設定


    def color_tolerance_setting(self, value):
        #色の差の許容範囲 (0-765の値, 30程度を推奨)
        self.color_tolerance = int(value)


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

        #動画のpathをリセット
        self.filename = None



    def video_to_image(self):
        try:
            self.video_info = ffmpeg.probe(self.filename) #ffmpegで動画情報を取得
        except:
            #エラー時はポップアップし、ボタンを戻す
            messagebox.showerror("Error", "ファイルが選択されていません")
            self.video_to_image_button["text"] = "動画を画像に変換"
            self.video_to_image_button["state"] = "normal"
            return

        #すでに存在する画像を削除
        self.check_dir = pathlib.Path(self.images_dir)
        for file in self.check_dir.iterdir():
            if file.is_file():
                file.unlink()

        #動画情報をピックアップ (解像度、フレームレート)
        for stream in self.video_info['streams']:
            if stream['codec_type'] == 'video':
                self.width = stream['width']
                self.height = stream["height"]
                self.fps = stream["avg_frame_rate"]
                break
        self.avg_fps = float(Fraction(self.fps)) #平均のfpsを計算
        
        #guiの動画情報を更新
        self.label_resolusion["text"] = f"解像度: {self.width} x {self.height}"
        self.label_fps["text"] = f"fps: {self.avg_fps}"

        #ffmpegのコマンドを設定
        self.ffmpeg_command = f'ffmpeg -i "{self.filename}" -vcodec png "{self.images_dir}%01d.png"'
        subprocess.call(self.ffmpeg_command, shell=True)

        #変換終了のポップアップ
        messagebox.showinfo("infomation", "変換が正常に終了しました")


    def detect_notes(self):
        try: #動画情報を取得する
            self.video_info = ffmpeg.probe(self.filename) #ffmpegで動画情報を取得
            #動画情報をピックアップ (解像度、フレームレート)
            for stream in self.video_info['streams']:
                if stream['codec_type'] == 'video':
                    self.width = stream['width']
                    self.height = stream["height"]
                    self.fps = stream["avg_frame_rate"]
                    break
            self.avg_fps = float(Fraction(self.fps)) #平均のfpsを計算
        except:
            #エラー時はポップアップし、ボタンを戻す
            messagebox.showerror("Error", "ファイルが選択されていません")
            return
        
        #各鍵盤の状態をフレームごとに保存する辞書を定義
        if not hasattr(self, "key_positions") or not self.key_positions:
            messagebox.showerror("error", "座標または色のしきい値が指定されていません")
            return
        if self.is_two_color_mode:
            self.left_note_states = {key: [] for key in self.key_positions.keys()}
            self.right_note_states = {key: [] for key in self.key_positions.keys()}
        else:
            self.note_states = {key: [] for key in self.key_positions.keys()}

        #ディレクトリ内のすべてのファイルをリストに入れる
        pathlib_img_dir = pathlib.Path(self.images_dir)
        files = os.listdir(pathlib_img_dir)
        sorted_files = sorted(files, key=lambda f: int(os.path.splitext(f)[0]))

        #各フレームを開く
        for image_file_name in sorted_files:
            img = Image.open(f"images\\{image_file_name}")
            #画像をRGBモードに変換
            rgb_img = img.convert("RGB")
            for key, data in self.key_positions.items():
                #現在のフレームの色を取得
                now_position = data["position"]
                r, g, b = rgb_img.getpixel(now_position)

                if self.is_two_color_mode:
                    left_R, left_G, left_B = self.left_color
                    right_R, right_G, right_B = self.right_color

                    diff_left_R = abs(r - left_R) < self.color_tolerance
                    diff_left_G = abs(g - left_G) < self.color_tolerance
                    diff_left_B = abs(b - left_B) < self.color_tolerance
                    diff_right_R = abs(r - right_R) < self.color_tolerance
                    diff_right_G = abs(g - right_G) < self.color_tolerance
                    diff_right_B = abs(b - right_B) < self.color_tolerance

                    print(f"file_path : {image_file_name} ------------------------------")
                    print(f"key: {key}")
                    print(f"diff_left_R: {diff_left_R} = {r} - {left_R}({abs(r - left_R)}) < {self.color_tolerance}")
                    print(f"diff_left_G: {diff_left_G} = {g} - {left_G}({abs(g - left_G)}) < {self.color_tolerance}")
                    print(f"diff_left_B: {diff_left_B} = {b} - {left_B}({abs(b - left_B)}) < {self.color_tolerance}")
                    print(f"diff_right_R: {diff_right_R} = {r} - {right_R}({abs(r - right_R)}) < {self.color_tolerance}")
                    print(f"diff_right_G: {diff_right_G} = {g} - {right_G}({abs(g - right_G)}) < {self.color_tolerance}")
                    print(f"diff_right_B: {diff_right_B} = {b} - {right_B}({abs(b - right_B)}) < {self.color_tolerance}")

                    if diff_left_R and diff_left_G and diff_left_B:
                        self.left_note_states[key].append(True)
                    else:
                        self.left_note_states[key].append(False)

                    if diff_right_R and diff_right_G and diff_right_B:
                        self.right_note_states[key].append(True)
                    else:
                        self.right_note_states[key].append(False)
                    
                else:
                    #しきい値とフレームの色の差を計算
                    diff = abs((r + g + b) - (data["color"][0] + data["color"][1] + data["color"][2]))
                    
                    #差が許容範囲を超えたらTrue
                    is_pressed = diff > self.color_tolerance
                    self.note_states[key].append(is_pressed)
                
        self.create_midi()


    def create_midi(self):
        # 音名とMIDIノート番号の対応辞書
        piano_notes = {
            'A_0': 21, 'A_Sharp_0': 22, 'B_0': 23,
            'C_1': 24, 'C_Sharp_1': 25, 'D_1': 26, 'D_Sharp_1': 27, 'E_1': 28, 'F_1': 29, 'F_Sharp_1': 30, 'G_1': 31, 'G_Sharp_1': 32, 'A_1': 33, 'A_Sharp_1': 34, 'B_1': 35,
            'C_2': 36, 'C_Sharp_2': 37, 'D_2': 38, 'D_Sharp_2': 39, 'E_2': 40, 'F_2': 41, 'F_Sharp_2': 42, 'G_2': 43, 'G_Sharp_2': 44, 'A_2': 45, 'A_Sharp_2': 46, 'B_2': 47,
            'C_3': 48, 'C_Sharp_3': 49, 'D_3': 50, 'D_Sharp_3': 51, 'E_3': 52, 'F_3': 53, 'F_Sharp_3': 54, 'G_3': 55, 'G_Sharp_3': 56, 'A_3': 57, 'A_Sharp_3': 58, 'B_3': 59,
            'C_4': 60, 'C_Sharp_4': 61, 'D_4': 62, 'D_Sharp_4': 63, 'E_4': 64, 'F_4': 65, 'F_Sharp_4': 66, 'G_4': 67, 'G_Sharp_4': 68, 'A_4': 69, 'A_Sharp_4': 70, 'B_4': 71,
            'C_5': 72, 'C_Sharp_5': 73, 'D_5': 74, 'D_Sharp_5': 75, 'E_5': 76, 'F_5': 77, 'F_Sharp_5': 78, 'G_5': 79, 'G_Sharp_5': 80, 'A_5': 81, 'A_Sharp_5': 82, 'B_5': 83,
            'C_6': 84, 'C_Sharp_6': 85, 'D_6': 86, 'D_Sharp_6': 87, 'E_6': 88, 'F_6': 89, 'F_Sharp_6': 90, 'G_6': 91, 'G_Sharp_6': 92, 'A_6': 93, 'A_Sharp_6': 94, 'B_6': 95,
            'C_7': 96, 'C_Sharp_7': 97, 'D_7': 98, 'D_Sharp_7': 99, 'E_7': 100, 'F_7': 101, 'F_Sharp_7': 102, 'G_7': 103, 'G_Sharp_7': 104, 'A_7': 105, 'A_Sharp_7': 106, 'B_7': 107,
            'C_8': 108
            }
        
        #prettyMIDIオブジェクト作成
        midi_data = pretty_midi.PrettyMIDI()
        piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
        velocity = 100

        if self.is_two_color_mode:
            left_piano = pretty_midi.Instrument(program=piano_program)
            right_piano = pretty_midi.Instrument(program=piano_program)

            all_note_states = {"left": self.left_note_states, "right": self.right_note_states}

            for hand, notes_dict in all_note_states.items():
                for key, states in notes_dict.items():
                    is_playing = False
                    start_frame = 0
                    for idx, is_pressed in enumerate(states, start=1):
                        if is_pressed and not is_playing:
                            is_playing = True
                            start_frame = idx
                        elif not is_pressed and is_playing:
                            is_playing = False
                            end_frame = idx
                            start_time = start_frame / self.avg_fps
                            end_time = end_frame / self.avg_fps
                            note = pretty_midi.Note(velocity=velocity, pitch=piano_notes[key], start=start_time, end=end_time)
                            (left_piano if hand == "left" else right_piano).notes.append(note)
                    # 末尾まで押され続けていた場合
                    if is_playing:
                        start_time = start_frame / self.avg_fps
                        end_time = (len(states) + 1) / self.avg_fps
                        note = pretty_midi.Note(velocity=velocity, pitch=piano_notes[key], start=start_time, end=end_time)
                        (left_piano if hand == "left" else right_piano).notes.append(note)

            midi_data.instruments.append(left_piano)
            midi_data.instruments.append(right_piano)
            output_path = "sample.mid"
            midi_data.write(output_path)
            messagebox.showinfo("infomation", "MIDI出力に成功しました")
        else:
            piano = pretty_midi.Instrument(program=piano_program)
            for key, states in self.note_states.items():
                is_playing = False
                start_frame = 0
                for idx, is_pressed in enumerate(states, start=1):
                    if is_pressed and not is_playing:
                        is_playing = True
                        start_frame = idx
                    elif not is_pressed and is_playing:
                        is_playing = False
                        end_frame = idx
                        start_time = start_frame / self.avg_fps
                        end_time = end_frame / self.avg_fps
                        note = pretty_midi.Note(velocity=velocity, pitch=piano_notes[key], start=start_time, end=end_time)
                        piano.notes.append(note)
                if is_playing:
                    start_time = start_frame / self.avg_fps
                    end_time = (len(states) + 1) / self.avg_fps
                    note = pretty_midi.Note(velocity=velocity, pitch=piano_notes[key], start=start_time, end=end_time)
                    piano.notes.append(note)

            midi_data.instruments.append(piano)
            output_path = "sample.mid"
            midi_data.write(output_path)
            messagebox.showinfo("infomation", "MIDI出力に成功しました")
        

    def open_Setting_position(self):
        test_path = f"{self.images_dir}\\1.png"
        if os.path.exists(test_path):
            pass
        else:
            messagebox.showerror("error", "画像ファイルが見つかりません。\n動画を画像に変換してください")
            return


        # 既に開いている場合はフォーカス
        if hasattr(self, "setting_win") and self.setting_win.winfo_exists():
            self.setting_win.lift()
            self.setting_win.focus_set()
            return
        # 親(self.root)を持つ Toplevel を生成
        self.setting_win = Setting_position(self)



class Setting_position(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master.root)
        self.app  = master #Appのインスタンスを保存
        #ウィンドウ設定
        self.title("Setting_position")
        self.geometry("1000x700")
        # 親との結び付け
        self.transient(master.root)     # タスクバーに別表示しない
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
        self.color_info_label1 = tk.Label(self, text="赤", font=20, fg="red")
        self.color_info_label2 = tk.Label(self, text=":C4,", font=20)
        self.color_info_label3 = tk.Label(self, text="緑", font=20, fg="green")
        self.color_info_label4 = tk.Label(self, text=":C4#, ", font=20)
        self.color_info_label5 = tk.Label(self, text="青", font=20,fg="blue")
        self.color_info_label6 = tk.Label(self, text=":B4に移動してください", font=20)
        self.color_info_label1.place(x=20, y=470)
        self.color_info_label2.place(x=45, y=470)
        self.color_info_label3.place(x=90, y=470)
        self.color_info_label4.place(x=115, y=470)
        self.color_info_label5.place(x=160, y=470)
        self.color_info_label6.place(x=180, y=470)

        self.info_label = tk.Label(self, text="すべての鍵盤が押されてない状態にしてください", font=12)
        self.info_label.place(x=20, y=550)

        #座標を指定するウィジェットを追加
        self.C4_box = DraggableRectangle(self.canvas, 20, 20, 7, 15, "red")
        self.C4_Sharp_box = DraggableRectangle(self.canvas, 30, 20, 6, 15, "green")
        self.B4_box = DraggableRectangle(self.canvas, 40, 20, 7, 15, "blue")

        #自動で鍵盤の座標を補充するボタン
        self.add_key_button = tk.Button(self, text="鍵盤を自動追加", command=self.add_all_octaves)
        self.add_key_button.place(x=20, y=580)

        #座標を確定するボタン
        self.confirm_positions_button = tk.Button(self, text="座標を確定", command=self.apply_position)
        self.confirm_positions_button.place(x=20, y=620)

        #しきい値を確定してウィンドウを閉じるボタン
        self.set_threshold_button = tk.Button(self, text="色のしきい値を取得", command=self.set_threshold)
        self.set_threshold_button.place(x=120, y=580)

        #鍵盤の色が2色か指定するチェックボックス
        self.state_is_two_color_mode = tk.BooleanVar()
        self.checkbox_is_two_color_mode = tk.Checkbutton(self, text="鍵盤の色が2色の時はチェックしてください", font=12, variable=self.state_is_two_color_mode)
        self.checkbox_is_two_color_mode.place(x=450, y=470)

    
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
        #ボタンを無効化
        self.add_key_button["state"] = "disable"
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
        self.C_y = C_y
        _, C_Sharp_y = self.C4_Sharp_box.get_position()
        self.C_Sharp_y = C_Sharp_y
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
                    self.all_dragable_keys[note] = DraggableRectangle(self.canvas, x1, y1, w, h, "gray")
                else:
                    self.key_positions.pop(note, None)
                    if note in self.all_dragable_keys:
                        self.canvas.delete(self.all_dragable_keys[note].item)
                        self.all_dragable_keys.pop(note, None)

        print(self.key_positions)


    def set_threshold(self):
        if not self.key_positions:
            messagebox.showerror("error", "座標を確定してください")
            return
        
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
        self.app.key_positions = self.key_positions
        print(f"座標としきい値が確定されました: {self.app.key_positions}")

        #鍵盤の色が2種類のときに、色を指定する
        if self.state_is_two_color_mode.get():
            for key in self.all_dragable_keys: #補完した鍵盤の座標をすべて非表示にする
                self.all_dragable_keys[key].hide()
        
            self.left_block = DraggableRectangle(self.canvas, 30, 30, 7, 15, "orange")
            self.right_block = DraggableRectangle(self.canvas, 50, 30, 7, 15, "purple")

            #labelを変更
            self.color_info_label1.config(text="橙", fg="orange")
            self.color_info_label2["text"] = ":左手"
            self.color_info_label3.config(text="紫", fg="purple")
            self.color_info_label4["text"] = ":右手"
            self.color_info_label5.config(text="に移動してください", fg="black")
            self.color_info_label6.place_forget()
            self.info_label["text"] = "左手と右手の鍵盤が同時に押されてる状態にしてください"

            self.get_two_colors_button = tk.Button(self, text="2つの鍵盤の色を取得して閉じる", bg="coral" ,command=self.get_two_colors)
            self.get_two_colors_button.place(x=120, y=620)
        else:
            self.destroy()

    
    def get_two_colors(self):
        #座標を取得
        left_position = self.left_block.get_position()
        right_position = self.right_block.get_position()
        

        #画像から色を取得
        img=Image.open(self.image_path)
        rgb_img = img.convert("RGB")
        #左の色を取得
        r_r, r_g, r_b = rgb_img.getpixel((left_position[0] / self.ratio, left_position[1] / self.ratio))
        self.left_color = [r_r, r_g, r_b]
        #右の色を取得
        l_r, l_g, l_b = rgb_img.getpixel((right_position[0] / self.ratio, right_position[1] / self.ratio))
        self.right_color = [l_r, l_g, l_b]
        print(f"ratio: {self.ratio}")
        print(f"left: {left_position[0] / self.ratio}, {left_position[1] / self.ratio}")
        print(f"right: {right_position[0] / self.ratio}, {right_position[1] / self.ratio}")
        print(f"filepath:{self.image_path}")
        print(f"left:{self.left_color}, right: {self.right_color}")

        #Appクラスに左右の色を渡す
        self.app.left_color = self.left_color
        self.app.right_color = self.right_color
        self.app.is_two_color_mode = self.state_is_two_color_mode

        self.destroy()


    def apply_position(self):
        if not hasattr(self, "all_dragable_keys"):
            messagebox.showerror("error", "座標を指定してください")
        else:
            #座標を保存
            for key in self.all_dragable_keys:
                x, y = self.all_dragable_keys[key].get_position()
                if "Sharp" in key:
                    self.key_positions[key] = {"position": [x / self.ratio, y / self.ratio], "color": None} #縮小前の画像の座標にして辞書に追加
                else:
                    self.key_positions[key] = {"position": [x / self.ratio, y / self.ratio], "color": None} #縮小前の画像の座標にして辞書に追加


class DraggableRectangle:
    def __init__(self, canvas, x, y, width, height, color):
        self.canvas = canvas
        self.item = canvas.create_rectangle(x, y, x+width, y+height, fill=color)
        self.canvas.tag_bind(self.item, '<Button-1>', self.on_press)
        self.canvas.tag_bind(self.item, '<B1-Motion>', self.on_drag)

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def hide(self):
        self.canvas.itemconfig(self.item, state="hidden")

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
    app=App()