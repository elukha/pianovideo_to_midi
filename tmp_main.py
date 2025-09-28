import tkinter as tk
from tkinter import filedialog
import ffmpeg
from fractions import Fraction  # 追加


def file_dir_button():
    button = tk.Button(text="mp4参照", command=open_file, width=7)
    button.place(x=260, y=10)

    reset_button = tk.Button(text="リセット", command=reset_file, width=4, bg="orange")
    reset_button.place(x=320, y=10)



def open_file():
    entry_box.configure(state="normal") #Entry_boxを書き込み可に設定
    idir = "C:\\" #初期ディレクトリ

    filetype = [("MP4", ".mp4")] #選択できる拡張子を指定

    global filename
    filename = filedialog.askopenfilename(filetypes=filetype, initialdir=idir)
    
    entry_box.insert(tk.END, filename)
    entry_box.config(state="readonly")

def reset_file():
    entry_box.configure(state="normal")
    entry_box.delete(0, tk.END)
    entry_box.configure(state="readonly")

    #guiの動画情報をリセット
    label_resolution["text"] = "解像度: -"
    label_fps["text"] = "FPS: -"


def video_to_image():
    video_info = ffmpeg.probe(filename)
    width = video_info["streams"][0]["width"]
    height = video_info["streams"][0]["height"]
    fps = video_info["streams"][0]["avg_frame_rate"]
    avg_fps = float(Fraction(fps))
    print(width, height, avg_fps)
    
    #guiの動画情報を更新
    label_resolution["text"] = f"解像度: {width} x {height}"
    label_fps["text"] = f"FPS: {avg_fps}"



#tkinter初期設定
root = tk.Tk()
root.title("Pianorole to MIDI")
root.geometry("400x300")

label_resolution = tk.Label(root, text="解像度: -")
label_resolution.place(x=120, y=50)

label_fps = tk.Label(root, text="FPS: -")
label_fps.place(x=120, y=70)



#ファイル参照部分
entry_box = tk.Entry(width=40, state="readonly")
entry_box.place(x=10,y=10)
file_dir_button()

#処理開始ボタン
start_button = tk.Button(text="動画を画像に変換", command=video_to_image)
start_button.place(x=10, y = 50)



root.mainloop()