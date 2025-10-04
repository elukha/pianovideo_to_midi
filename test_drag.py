import tkinter as tk

class DraggableRectangle:
    def __init__(self, canvas, x, y, width, height, color):
        self.canvas = canvas
        self.item = canvas.create_rectangle(x, y, x+width, y+height, fill=color)
        self.canvas.tag_bind(self.item, '<Button-1>', self.on_press)
        self.canvas.tag_bind(self.item, '<B1-Motion>', self.on_drag)

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        print(f"onpres() startx={self.start_x}, start_y={self.start_y}")

    def on_drag(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        print(f"on_drag() dx={dx}, dy={dy}")

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
        print(f"on_drag() start_x={self.start_x}, start_y={self.start_y}")

    def get_position(self):
        position = self.canvas.coords(self.item)
        print(f"position: {position}")
        return position
        



root = tk.Tk()
root.geometry("600x600")
canvas = tk.Canvas(root, width=400, height=400, bg="gray")
canvas.pack()


rectangle1 = DraggableRectangle(canvas, 50, 50, 100, 80, "red")
rectangle2 = DraggableRectangle(canvas, 20, 20, 50, 50, "blue")

get_position_button = tk.Button(root, text="座標を取得", command=rectangle1.get_position)
get_position_button.place(x=10, y=500)






root.mainloop()