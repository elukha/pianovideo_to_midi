import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ffmpeg
from fractions import Fraction
import subprocess
import os
import pathlib
from PIL import Image, ImageTk
import pretty_midi
import threading
import sys
import time
import tempfile
import shutil

class App:
    def __init__(self):
        # tkinter初期化
        self.root = tk.Tk()
        self.root.title("Pianorole to MIDI")
        self.root.geometry("600x300")

        # --- 一時ディレクトリの設定 (権限エラー回避・自動削除) ---
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.images_dir = self.temp_dir_obj.name

        # --- EXE化用のパス解決ヘルパー ---
        self.base_path = self.get_base_path()
        
        # メンバ変数の初期化
        self.key_positions = {}
        self.color_tolerance = 30
        self.left_color = None
        self.right_color = None
        self.is_two_color_mode = False
        self.is_converting_video = False 
        self.total_video_frames = 0      
        
        self.create_widget()

        # アプリ終了時に一時フォルダを掃除
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def get_base_path(self):
        """実行環境（EXEかScriptか）に応じたベースパスを取得"""
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def get_ffmpeg_path(self):
        """ffmpegの実行ファイルパスを取得"""
        bin_name = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
        
        # 1. EXE同梱 or 開発環境
        bundled_path = os.path.join(self.base_path, bin_name)
        if os.path.exists(bundled_path):
            return bundled_path
            
        # 2. EXEと同じフォルダ
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            external_path = os.path.join(exe_dir, bin_name)
            if os.path.exists(external_path):
                return external_path

        # 3. PATH環境変数
        return bin_name
        
    def get_ffprobe_path(self):
        """ffprobeの実行ファイルパスを取得"""
        bin_name = "ffprobe.exe" if os.name == 'nt' else "ffprobe"
        
        bundled_path = os.path.join(self.base_path, bin_name)
        if os.path.exists(bundled_path):
            return bundled_path
            
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            external_path = os.path.join(exe_dir, bin_name)
            if os.path.exists(external_path):
                return external_path
                
        return bin_name

    def on_closing(self):
        try:
            self.temp_dir_obj.cleanup()
        except:
            pass
        self.root.destroy()
    
    def create_widget(self):
        # 動画情報表示ラベル
        self.label_resolusion = tk.Label(self.root, text="解像度 -")
        self.label_resolusion.place(x=120, y=50)

        self.label_fps = tk.Label(self.root, text="FPS: -")
        self.label_fps.place(x=120, y=70)

        # ファイル参照関連
        self.entry_box = tk.Entry(self.root, width=40, state="readonly")
        self.entry_box.place(x=10, y=10)
        
        self.file_dir_button = tk.Button(self.root, text="①動画参照", command=self.open_file, width=9)
        self.file_dir_button.place(x=260, y=10)

        self.reset_button = tk.Button(self.root, text="リセット", command=self.reset_file, width=4, bg="orange")
        self.reset_button.place(x=340, y=10)

        # 動画から画像に変換ボタン
        self.video_to_image_button = tk.Button(self.root, text="②動画を画像に変換", command=self.start_video_to_image_thread)
        self.video_to_image_button.place(x=10, y=50)
        
        # 鍵盤の位置設定ボタン
        self.set_keyboard_position_button = tk.Button(self.root, text="③鍵盤の位置を指定", command=self.open_Setting_position)
        self.set_keyboard_position_button.place(x=10, y=90)

        # 分析開始ボタン
        self.detect_notes_button = tk.Button(self.root, text="⑤MIDI化開始", command=self.start_detect_notes_thread)
        self.detect_notes_button.place(x=10, y=130)

        # 色の差の許容範囲スライダー
        self.scale = tk.Scale(self.root, from_=0, to=255, length=400, orient=tk.HORIZONTAL, label="④色の差の許容範囲(単色の場合30、2色の場合140程度を推奨)", command=self.color_tolerance_setting)
        self.scale.place(x=10, y=170)
        self.scale.set(30)

        # 進捗バー
        self.progress_label = tk.Label(self.root, text="待機中...")
        self.progress_label.place(x=10, y=220)
        self.progressbar = ttk.Progressbar(self.root, orient="horizontal", length=560, mode="determinate")
        self.progressbar.place(x=10, y=240)


    def color_tolerance_setting(self, value):
        self.color_tolerance = int(value)


    # 【変更点】mp4以外も対応
    def open_file(self):
        self.entry_box.configure(state="normal")
        self.idir = os.path.expanduser("~") # 初期位置をホームディレクトリに
        self.file_type=[("Video Files", "*.mp4;*.mov;*.avi;*.mkv;*.webm;*.flv;*.wmv"), ("All Files", "*.*")]
        self.filename = filedialog.askopenfilename(filetypes=self.file_type, initialdir=self.idir)
        self.entry_box.delete(0, tk.END)
        self.entry_box.insert(tk.END, self.filename)
        self.entry_box.config(state="readonly")


    def reset_file(self):
        self.entry_box.configure(state="normal")
        self.entry_box.delete(0, tk.END)
        self.entry_box.configure(state="readonly")
        self.label_resolusion["text"] = "解像度 -"
        self.label_fps["text"] = "FPS -"
        self.filename = None
        self.progressbar["value"] = 0
        self.progress_label["text"] = "リセットしました"


    def set_ui_state(self, state):
        self.file_dir_button.configure(state=state)
        self.reset_button.configure(state=state)
        self.video_to_image_button.configure(state=state)
        self.set_keyboard_position_button.configure(state=state)
        self.detect_notes_button.configure(state=state)
        self.scale.configure(state=state)


    # =================================================================================
    #  動画変換 (Video to Image)
    # =================================================================================
    def start_video_to_image_thread(self):
        if not hasattr(self, 'filename') or not self.filename:
             messagebox.showerror("Error", "ファイルが選択されていません")
             return

        self.set_ui_state("disabled")
        self.progress_label["text"] = "動画変換の準備中..."
        self.progressbar["value"] = 0

        thread = threading.Thread(target=self.video_to_image_thread_logic)
        thread.daemon = True
        thread.start()


    def video_to_image_thread_logic(self):
        try:
            ffmpeg_exe = self.get_ffmpeg_path()
            ffprobe_exe = self.get_ffprobe_path()

            # ffmpeg-python用パス設定
            os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_exe)

            # 動画情報を取得
            try:
                self.video_info = ffmpeg.probe(self.filename, cmd=ffprobe_exe)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"動画情報の取得に失敗しました: {e}"))
                return

            duration = 0
            frames = 0
            
            if 'format' in self.video_info and 'duration' in self.video_info['format']:
                try:
                    duration = float(self.video_info['format']['duration'])
                except: pass

            for stream in self.video_info['streams']:
                if stream['codec_type'] == 'video':
                    self.width = stream['width']
                    self.height = stream["height"]
                    self.fps = stream.get("avg_frame_rate", "30/1")
                    if 'nb_frames' in stream:
                        try:
                            frames = int(stream['nb_frames'])
                        except: pass
                    break
            
            try:
                self.avg_fps = float(Fraction(self.fps))
            except:
                self.avg_fps = 30.0
            
            if frames == 0 and duration > 0:
                frames = int(duration * self.avg_fps)
            
            self.total_video_frames = frames

            self.root.after(0, lambda: self.label_resolusion.config(text=f"解像度: {self.width} x {self.height}"))
            self.root.after(0, lambda: self.label_fps.config(text=f"fps: {self.avg_fps:.2f}"))

            # --- 画像保存フォルダの初期化 ---
            self.root.after(0, self.update_progress_ui, 0, "作業用フォルダを初期化中...")
            for filename in os.listdir(self.images_dir):
                file_path = os.path.join(self.images_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception: pass

            # --- 変換実行 ---
            output_pattern = os.path.join(self.images_dir, "%01d.png")
            cmd = [
                ffmpeg_exe, '-i', self.filename, '-vcodec', 'png', output_pattern, '-y'
            ]
            
            self.is_converting_video = True
            self.root.after(500, self.monitor_conversion)

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            ret_code = subprocess.call(cmd, shell=False, startupinfo=startupinfo)
            
            self.is_converting_video = False
            
            if ret_code == 0:
                self.root.after(0, self.update_progress_ui, 100, "変換完了")
                self.root.after(0, lambda: messagebox.showinfo("infomation", "変換が正常に終了しました"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", f"変換エラー: コード {ret_code}"))

        except Exception as e:
            self.is_converting_video = False
            self.root.after(0, lambda: messagebox.showerror("Error", f"変換例外: {e}"))
        finally:
            self.is_converting_video = False
            self.root.after(0, lambda: self.set_ui_state("normal"))


    def monitor_conversion(self):
        if not self.is_converting_video:
            return

        try:
            current_frames = len([name for name in os.listdir(self.images_dir) if name.endswith('.png')])

            if self.total_video_frames > 0:
                progress = (current_frames / self.total_video_frames) * 100
                if progress > 99: progress = 99
                self.update_progress_ui(progress, f"動画変換中... {current_frames}/{self.total_video_frames} フレーム")
            else:
                self.update_progress_ui(0, f"動画変換中... {current_frames} フレーム生成済み")
        except Exception:
            pass
        
        if self.is_converting_video:
            self.root.after(500, self.monitor_conversion)


    # =================================================================================
    #  MIDI化 (Detect Notes)
    # =================================================================================
    def start_detect_notes_thread(self):
        self.set_ui_state("disabled")
        self.progress_label["text"] = "画像解析の準備中..."
        self.progressbar["value"] = 0
        
        thread = threading.Thread(target=self.detect_notes_thread_logic)
        thread.daemon = True
        thread.start()


    def detect_notes_thread_logic(self):
        try:
            if not hasattr(self, 'filename') or not self.filename:
                self.root.after(0, lambda: messagebox.showerror("Error", "ファイルが選択されていません"))
                return
            
            # FPSの再取得
            if not hasattr(self, 'avg_fps'):
                try:
                    ffprobe_exe = self.get_ffprobe_path()
                    self.video_info = ffmpeg.probe(self.filename, cmd=ffprobe_exe)
                    for stream in self.video_info['streams']:
                        if stream['codec_type'] == 'video':
                            self.fps = stream.get('avg_frame_rate', "30/1")
                            break
                    self.avg_fps = float(Fraction(self.fps))
                except:
                    self.root.after(0, lambda: messagebox.showerror("Error", "動画情報の取得に失敗しました。先に動画変換を行ってください。"))
                    return
            
            if not hasattr(self, "key_positions") or not self.key_positions:
                self.root.after(0, lambda: messagebox.showerror("error", "座標または色のしきい値が指定されていません"))
                return

            if not hasattr(self, 'is_two_color_mode'):
                self.is_two_color_mode = False

            if self.is_two_color_mode:
                self.left_note_states = {key: [] for key in self.key_positions.keys()}
                self.right_note_states = {key: [] for key in self.key_positions.keys()}
            else:
                self.note_states = {key: [] for key in self.key_positions.keys()}

            files = []
            if os.path.exists(self.images_dir):
                for f in os.listdir(self.images_dir):
                    if f.lower().endswith('.png'):
                        try:
                            int(os.path.splitext(f)[0])
                            files.append(f)
                        except ValueError: pass

            sorted_files = sorted(files, key=lambda f: int(os.path.splitext(f)[0]))
            total_files = len(sorted_files)

            if total_files == 0:
                self.root.after(0, lambda: messagebox.showerror("Error", "画像が見つかりません。動画変換を行ってください。"))
                return

            for i, image_file_name in enumerate(sorted_files):
                img_path = os.path.join(self.images_dir, image_file_name)
                try:
                    with Image.open(img_path) as img:
                        rgb_img = img.convert("RGB")
                        
                        for key, data in self.key_positions.items():
                            now_position = data["position"]
                            px, py = int(now_position[0]), int(now_position[1])
                            
                            if px < 0 or py < 0 or px >= rgb_img.width or py >= rgb_img.height:
                                continue

                            r, g, b = rgb_img.getpixel((px, py))

                            if self.is_two_color_mode:
                                if self.left_color is None or self.right_color is None: continue

                                left_R, left_G, left_B = self.left_color
                                right_R, right_G, right_B = self.right_color

                                diff_left = (abs(r - left_R) < self.color_tolerance and
                                             abs(g - left_G) < self.color_tolerance and
                                             abs(b - left_B) < self.color_tolerance)
                                
                                diff_right = (abs(r - right_R) < self.color_tolerance and
                                              abs(g - right_G) < self.color_tolerance and
                                              abs(b - right_B) < self.color_tolerance)

                                self.left_note_states[key].append(diff_left)
                                self.right_note_states[key].append(diff_right)
                            else:
                                if data["color"] is None: continue
                                
                                diff = abs((r + g + b) - (data["color"][0] + data["color"][1] + data["color"][2]))
                                is_pressed = diff > self.color_tolerance
                                self.note_states[key].append(is_pressed)
                    
                except Exception: pass

                if i % 20 == 0:
                    progress = (i + 1) / total_files * 100
                    self.root.after(0, self.update_progress_ui, progress, f"画像解析中... {i+1}/{total_files} フレーム")

            self.root.after(0, lambda: self.progress_label.config(text="MIDIファイルを作成中..."))
            self.create_midi()
            
            self.root.after(0, self.update_progress_ui, 100, "完了")
            self.root.after(0, lambda: messagebox.showinfo("infomation", "MIDI出力に成功しました"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"予期せぬエラー: {e}"))
            import traceback
            traceback.print_exc()
        finally:
            self.root.after(0, lambda: self.set_ui_state("normal"))


    def update_progress_ui(self, value, text):
        self.progressbar["value"] = value
        self.progress_label["text"] = text


    # 【変更点】保存先ダイアログを追加
    def create_midi(self):
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
        
        midi_data = pretty_midi.PrettyMIDI()
        piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
        velocity = 100

        # 保存先ダイアログ
        output_path = filedialog.asksaveasfilename(defaultextension=".mid", filetypes=[("MIDI files", "*.mid")], initialfile="output.mid")
        if not output_path:
            return # キャンセル時は何もしない

        if self.is_two_color_mode:
            left_piano = pretty_midi.Instrument(program=piano_program, name="Left Hand")
            right_piano = pretty_midi.Instrument(program=piano_program, name="Right Hand")
            all_note_states = {"left": self.left_note_states, "right": self.right_note_states}

            for hand, notes_dict in all_note_states.items():
                target_inst = left_piano if hand == "left" else right_piano
                for key, states in notes_dict.items():
                    if key not in piano_notes: continue 
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
                            target_inst.notes.append(note)
                    if is_playing:
                        start_time = start_frame / self.avg_fps
                        end_time = (len(states) + 1) / self.avg_fps
                        note = pretty_midi.Note(velocity=velocity, pitch=piano_notes[key], start=start_time, end=end_time)
                        target_inst.notes.append(note)

            midi_data.instruments.append(left_piano)
            midi_data.instruments.append(right_piano)
        else:
            piano = pretty_midi.Instrument(program=piano_program)
            for key, states in self.note_states.items():
                if key not in piano_notes: continue
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

        midi_data.write(output_path)


    def open_Setting_position(self):
        first_img_path = os.path.join(self.images_dir, "1.png")
        if not os.path.exists(first_img_path):
            messagebox.showerror("error", "画像ファイルが見つかりません。\n動画を画像に変換してください")
            return

        if hasattr(self, "setting_win") and self.setting_win.winfo_exists():
            self.setting_win.lift()
            self.setting_win.focus_set()
            return
        self.setting_win = Setting_position(self)


class Setting_position(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master.root)
        self.app  = master 
        self.title("Setting_position")
        self.geometry("950x700")
        self.transient(master.root)
        self.grab_set()

        self.key_positions = {}
        self.octave_offset_x = 0
        self.canvas_height=450
        self.canvas_width=800
        self.canvas = tk.Canvas(self, bg="lightgray", height=self.canvas_height, width=self.canvas_width, highlightthickness=0, borderwidth=0)
        self.canvas.place(x=10, y=10)

        self.images_dir = self.app.images_dir
        
        first_img_path = os.path.join(self.images_dir, "1.png")
        resized_image, new_width, new_height = self.resize_image(first_img_path)
        
        if resized_image:
            self.canvas.config(width=new_width, height=new_height)
            self.image_id = self.canvas.create_image(new_width / 2, new_height / 2, anchor=tk.CENTER, image=resized_image)
            self.canvas.image = resized_image
            self.canvas.lower(self.image_id)

            pathlib_images_dir = pathlib.Path(self.images_dir)
            total_frames = 0
            if pathlib_images_dir.exists():
                for f in pathlib_images_dir.iterdir():
                     if f.is_file() and f.suffix.lower() == '.png':
                         try:
                             int(f.stem)
                             total_frames += 1
                         except: pass
            if total_frames == 0: total_frames = 1

            self.scale = tk.Scale(self, from_=1, to=total_frames, orient=tk.HORIZONTAL, length=800, troughcolor="skyblue", command=self.update_image)
            self.scale.place(x=10, y=500)

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

        self.C4_box = DraggableRectangle(self.canvas, 20, 20, 7, 15, "red")
        self.C4_Sharp_box = DraggableRectangle(self.canvas, 30, 20, 6, 15, "green")
        self.B4_box = DraggableRectangle(self.canvas, 40, 20, 7, 15, "blue")

        self.add_key_button = tk.Button(self, text="鍵盤を自動追加", command=self.add_all_octaves)
        self.add_key_button.place(x=20, y=580)

        self.confirm_positions_button = tk.Button(self, text="座標を確定", command=self.apply_position)
        self.confirm_positions_button.place(x=20, y=620)

        self.set_threshold_button = tk.Button(self, text="色のしきい値を取得", command=self.set_threshold)
        self.set_threshold_button.place(x=120, y=580)

        self.state_is_two_color_mode = tk.BooleanVar()
        self.checkbox_is_two_color_mode = tk.Checkbutton(self, text="鍵盤の色が2色の時はチェックしてください", font=12, variable=self.state_is_two_color_mode)
        self.checkbox_is_two_color_mode.place(x=450, y=470)

    
    def resize_image(self, image_path):
        try:
            self.image_path = image_path
            with Image.open(image_path) as pil_image:
                image_width, image_height = pil_image.size
                width_ratio = self.canvas_width / image_width
                height_ratio = self.canvas_height / image_height
                self.ratio = min(width_ratio, height_ratio)
                new_width = int(image_width * self.ratio)
                new_height = int(image_height * self.ratio)
                resized_pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                resized_tk_image = ImageTk.PhotoImage(resized_pil_image)
            return resized_tk_image, new_width, new_height
        except Exception as e:
            messagebox.showerror("error", f"画像読み込みエラー: {e}")
            self.destroy()
            return None, 0, 0

    
    def update_image(self, val):
        path = os.path.join(self.images_dir, f"{val}.png")
        resized_image, _, _ = self.resize_image(path)
        if resized_image:
            self.canvas.itemconfig(self.image_id, image=resized_image)
            self.canvas.image = resized_image
            self.canvas.lower(self.image_id)


    def add_all_octaves(self):
        self.add_key_button["state"] = "disable"
        self.all_dragable_keys = {}
        self.key_positions = {}

        if self.C4_box:
            self.canvas.itemconfig(self.C4_box.item, state="hidden")
            self.canvas.itemconfig(self.C4_Sharp_box.item, state="hidden")
            self.canvas.itemconfigure(self.B4_box.item, state="hidden")

        self.add_keys(octave=4)
        for oct in [1, 2, 3, 5, 6, 7]:
            self.add_keys(octave=oct)


    def add_keys(self, octave):
        C_x, C_y = self.C4_box.get_position()
        self.C_y = C_y
        _, C_Sharp_y = self.C4_Sharp_box.get_position()
        self.C_Sharp_y = C_Sharp_y
        B_x, _ = self.B4_box.get_position()
        canvas_width = self.canvas.winfo_width()

        keys=["C", "C_Sharp", "D", "D_Sharp", "E", "E_None", "F", "F_Sharp", "G", "G_Sharp", "A", "A_Sharp", "B"]
        t = len(keys) - 1

        base_C4_offset_x = octave - 4

        if not octave==4:
            C4_x, _ = self.all_dragable_keys["C_4"].get_position()
            C4_Sharp_x, _ = self.all_dragable_keys["C_Sharp_4"].get_position()
            B4_x, _ = self.all_dragable_keys["B_4"].get_position()
            self.octave_offset_x = B4_x - C4_x
            self.note_distance_x = C4_Sharp_x - C4_x
            self.octave_offset_x = self.octave_offset_x + (self.note_distance_x * 2)

        octave_distance = self.octave_offset_x * base_C4_offset_x

        for i, note in enumerate(keys):
            note = note + "_" + str(octave)
            x = (1 - (i / t)) * C_x + ((i / t) * B_x)
            x = x + octave_distance

            if note == f"E_None_{octave}":
                continue

            if "_Sharp" in note:
                w, h = 6, 15
                center_y = C_Sharp_y
                x1 = x - w / 2
                y1 = center_y - h / 2
            else:
                w, h = 7, 15
                center_y = C_y
                x1 = x - w / 2
                y1 = center_y - h / 2
            
            x2 = x1 + w
            if 0 <= x1 and x2 <= canvas_width:
                self.all_dragable_keys[note] = DraggableRectangle(self.canvas, x1, y1, w, h, "gray")
            else:
                if note in self.all_dragable_keys:
                    self.canvas.delete(self.all_dragable_keys[note].item)
                    self.all_dragable_keys.pop(note, None)


    def set_threshold(self):
        if not hasattr(self, "all_dragable_keys") or not self.all_dragable_keys:
            messagebox.showerror("error", "鍵盤を自動追加してください")
            return
        
        try:
            with Image.open(self.image_path) as img:
                rgb_img = img.convert("RGB")
                for key in self.all_dragable_keys:
                    x, y = self.all_dragable_keys[key].get_position()
                    orig_x = int(x / self.ratio)
                    orig_y = int(y / self.ratio)
                    
                    if 0 <= orig_x < rgb_img.width and 0 <= orig_y < rgb_img.height:
                        r, g, b = rgb_img.getpixel((orig_x, orig_y))
                        if key not in self.key_positions:
                            self.key_positions[key] = {}
                        self.key_positions[key]["color"] = [r, g, b]
                        self.key_positions[key]["position"] = [orig_x, orig_y]

            self.app.key_positions = self.key_positions
            print(f"座標としきい値が確定されました")

            if self.state_is_two_color_mode.get():
                for key in self.all_dragable_keys:
                    self.all_dragable_keys[key].hide()
                self.left_block = DraggableRectangle(self.canvas, 30, 30, 7, 15, "orange")
                self.right_block = DraggableRectangle(self.canvas, 50, 30, 7, 15, "purple")
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
        except Exception as e:
            messagebox.showerror("Error", f"しきい値取得エラー: {e}")

    
    def get_two_colors(self):
        try:
            left_position = self.left_block.get_position()
            right_position = self.right_block.get_position()
            with Image.open(self.image_path) as img:
                rgb_img = img.convert("RGB")
                lx, ly = int(left_position[0] / self.ratio), int(left_position[1] / self.ratio)
                rx, ry = int(right_position[0] / self.ratio), int(right_position[1] / self.ratio)
                r_r, r_g, r_b = rgb_img.getpixel((lx, ly))
                self.left_color = [r_r, r_g, r_b]
                l_r, l_g, l_b = rgb_img.getpixel((rx, ry))
                self.right_color = [l_r, l_g, l_b]
            self.app.left_color = self.left_color
            self.app.right_color = self.right_color
            self.app.is_two_color_mode = self.state_is_two_color_mode.get()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"2色取得エラー: {e}")


    def apply_position(self):
        if not hasattr(self, "all_dragable_keys"):
            messagebox.showerror("error", "座標を指定してください")
        else:
            for key in self.all_dragable_keys:
                x, y = self.all_dragable_keys[key].get_position()
                if key not in self.key_positions:
                    self.key_positions[key] = {"color": None}
                self.key_positions[key]["position"] = [x / self.ratio, y / self.ratio]
            self.app.key_positions = self.key_positions
            apply_position_label = tk.Label(self, text="座標を確定しました", font=2)
            apply_position_label.place(x=20, y=660)


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
        if x1 + dx < 0: dx = -x1
        if y1 + dy < 0: dy = -y1
        if x2 + dx > canvas_width: dx = canvas_width - x2
        if y2 + dy > canvas_height: dy = canvas_height - y2
        self.canvas.move(self.item, dx, dy)
        self.start_x = event.x
        self.start_y = event.y

    def get_position(self):
        position = self.canvas.coords(self.item)
        x = (position[0] + position[2]) / 2
        y = (position[1] + position[3]) / 2
        return x, y


if __name__ == "__main__":
    app=App()