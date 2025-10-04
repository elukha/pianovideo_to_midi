import tkinter as tk

def on_scale(val):
    label.config(text=str(val) + "%")


#ウィンドウの作成
root = tk.Tk()
root.title("scale_test")
root.geometry("500x300")

#スライダーの作成
scale = tk.Scale(root, from_=0, to=500,length=300 ,orient=tk.HORIZONTAL, command=on_scale)
scale.pack()

#ラベルの作成
label = tk.Label(root, text="0")
label.pack()

root.mainloop()