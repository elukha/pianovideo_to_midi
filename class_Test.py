import tkinter as tk

# --- 手順1: サブウィンドウの中身となるクラスを定義 ---
class SubWindowFrame(tk.Frame):
    """サブウィンドウに配置するフレーム"""
    def __init__(self, master=None):
        super().__init__(master)
        
        # masterはToplevelインスタンスになる
        self.master = master
        self.master.title("サブウィンドウ")
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # このフレーム(self)の中にウィジェットを作成・配置する
        self.label = tk.Label(self, text="名前を入力してください:")
        self.label.pack(pady=5)

        self.entry = tk.Entry(self)
        self.entry.pack(pady=5)

        self.button = tk.Button(self, text="閉じる", command=self.close_window)
        self.button.pack(pady=10)

    def close_window(self):
        # master(Toplevelインスタンス)を破棄する
        self.master.destroy()


class MainApp(tk.Frame):
    """メインウィンドウのアプリケーション"""
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()

        self.open_button = tk.Button(self, text="サブウィンドウを開く", command=self.open_sub_window)
        self.open_button.pack(padx=50, pady=30)

    def open_sub_window(self):
        # --- 手順2: サブウィンドウ(tk.Toplevel)を生成 ---
        # Toplevelはメインウィンドウ(self.master)を親として生成
        sub_window = tk.Toplevel(self.master)
        
        # --- 手順3: サブウィンドウの中に、定義したフレームを配置 ---
        # masterとしてsub_windowを渡すのが最重要ポイント
        sub_frame = SubWindowFrame(master=sub_window)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("メインウィンドウ")
    root.geometry("300x150")
    app = MainApp(master=root)
    app.mainloop()