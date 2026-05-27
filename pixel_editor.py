#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
import json
import math

# 默认尺寸
DEFAULT_WIDTH = 48
DEFAULT_HEIGHT = 48
PIXEL_SIZE = 12
CANVAS_BG = "#2d2d2d"
GRID_COLOR = "#555555"

# 调色板
DEFAULT_PALETTE = [
    ("黑色", (0, 0, 0)), ("白色", (255, 255, 255)),
    ("亮红", (255, 60, 60)), ("深红", (180, 0, 0)),
    ("亮绿", (0, 255, 80)), ("深绿", (0, 120, 0)),
    ("亮蓝", (60, 120, 255)), ("深蓝", (0, 40, 120)),
    ("橙色", (255, 140, 0)), ("琥珀", (255, 180, 40)),
    ("青色", (0, 210, 210)), ("紫色", (160, 80, 255)),
    ("灰色", (160, 160, 160)), ("深灰", (80, 80, 80)),
    ("肤色", (255, 210, 150)), ("粉色", (255, 100, 150)),
]


class PixelEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("像素画编辑器")
        self.root.geometry("1200x780")

        self.width = DEFAULT_WIDTH
        self.height = DEFAULT_HEIGHT
        self.pixels = []
        self.current_color = (255, 255, 255)
        self.pixel_size = PIXEL_SIZE
        self.brush_size = 1
        self.canvas = None
        self.rect_ids = []

        self.init_ui()
        self.new_icon(self.width, self.height)

    def init_ui(self):
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # 画布尺寸设置
        ttk.Label(control_frame, text="宽度:").pack(side=tk.LEFT, padx=(5, 2))
        self.width_entry = ttk.Entry(control_frame, width=5)
        self.width_entry.insert(0, str(DEFAULT_WIDTH))
        self.width_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(control_frame, text="高度:").pack(side=tk.LEFT, padx=(5, 2))
        self.height_entry = ttk.Entry(control_frame, width=5)
        self.height_entry.insert(0, str(DEFAULT_HEIGHT))
        self.height_entry.pack(side=tk.LEFT, padx=2)

        ttk.Button(control_frame, text="新建画布", command=self.new_from_size).pack(side=tk.LEFT, padx=5)

        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 画笔粗细
        ttk.Label(control_frame, text="画笔大小:").pack(side=tk.LEFT, padx=(10, 2))
        self.brush_var = tk.IntVar(value=1)
        brush_combo = ttk.Combobox(control_frame, textvariable=self.brush_var, values=[1, 2, 3, 4, 5], width=3,
                                   state="readonly")
        brush_combo.pack(side=tk.LEFT, padx=2)
        brush_combo.bind("<<ComboboxSelected>>", lambda e: self.set_brush_size())

        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 操作按钮
        ttk.Button(control_frame, text="清空", command=self.clear_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="全部填充", command=self.fill_all).pack(side=tk.LEFT, padx=2)

        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 形状工具
        ttk.Label(control_frame, text="形状:").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(control_frame, text="● 圆形", command=lambda: self.draw_shape("circle")).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="■ 方形", command=lambda: self.draw_shape("square")).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="♥ 心形", command=lambda: self.draw_shape("heart")).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="💧 水滴", command=lambda: self.draw_shape("drop")).pack(side=tk.LEFT, padx=2)

        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 颜色相关
        ttk.Label(control_frame, text="当前颜色:").pack(side=tk.LEFT, padx=(0, 3))
        self.color_indicator = tk.Canvas(control_frame, width=24, height=24, bg=self.rgb_to_hex(self.current_color))
        self.color_indicator.pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="选色", command=self.choose_color).pack(side=tk.LEFT, padx=2)

        # 导出格式
        ttk.Label(control_frame, text="导出:").pack(side=tk.LEFT, padx=(10, 2))
        self.format_var = tk.StringVar(value="rgb565")
        ttk.Radiobutton(control_frame, text="RGB565", variable=self.format_var, value="rgb565").pack(side=tk.LEFT)
        ttk.Radiobutton(control_frame, text="RGB888", variable=self.format_var, value="rgb888").pack(side=tk.LEFT)
        ttk.Button(control_frame, text="导出C数组", command=self.export_c_array).pack(side=tk.LEFT, padx=5)

        # 项目保存/加载
        ttk.Button(control_frame, text="保存项目", command=self.save_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="加载项目", command=self.load_project).pack(side=tk.LEFT, padx=2)

        # 调色板 (左侧)
        palette_frame = ttk.LabelFrame(self.root, text="调色板", width=130)
        palette_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        palette_frame.pack_propagate(False)
        for name, rgb in DEFAULT_PALETTE:
            btn = tk.Button(palette_frame, bg=self.rgb_to_hex(rgb), width=5, height=1,
                            command=lambda c=rgb: self.set_current_color(c))
            btn.pack(pady=1, padx=2, fill=tk.X)
        ttk.Button(palette_frame, text="自定义", command=self.choose_color).pack(pady=5)

        # 画板区域
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas = tk.Canvas(canvas_frame, bg=CANVAS_BG, highlightthickness=0)
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.paint)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<Button-3>", self.erase)
        self.canvas.bind("<B3-Motion>", self.erase)

        self.status_var = tk.StringVar()
        self.status_var.set(f"就绪 | 画布 {self.width}x{self.height} | 画笔大小 {self.brush_size}")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ---------- 画布管理 ----------
    def set_brush_size(self):
        self.brush_size = self.brush_var.get()
        self.status_var.set(f"画笔大小 = {self.brush_size}")

    def new_icon(self, width, height, init_color=(0, 0, 0)):
        self.width = width
        self.height = height
        self.pixels = [[init_color for _ in range(width)] for _ in range(height)]
        self.redraw_canvas()
        self.status_var.set(f"新画布 {width}x{height} | 画笔大小 {self.brush_size}")

    def new_from_size(self):
        try:
            w = int(self.width_entry.get())
            h = int(self.height_entry.get())
            if 1 <= w <= 256 and 1 <= h <= 256:
                self.new_icon(w, h)
            else:
                raise ValueError
        except:
            messagebox.showerror("错误", "宽度和高度需为 1~256 的整数")

    def redraw_canvas(self):
        self.canvas.delete("all")
        self.rect_ids = []
        canvas_w = self.width * self.pixel_size
        canvas_h = self.height * self.pixel_size
        self.canvas.config(scrollregion=(0, 0, canvas_w, canvas_h))
        for y in range(self.height):
            row = []
            for x in range(self.width):
                x1 = x * self.pixel_size
                y1 = y * self.pixel_size
                x2 = x1 + self.pixel_size
                y2 = y1 + self.pixel_size
                color = self.rgb_to_hex(self.pixels[y][x])
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=GRID_COLOR, width=1)
                row.append(rect)
            self.rect_ids.append(row)

    def update_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = color
            self.canvas.itemconfig(self.rect_ids[y][x], fill=self.rgb_to_hex(color))

    def draw_brush(self, cx, cy, color, erase=False):
        half = self.brush_size // 2
        for dy in range(-half, half + 1):
            for dx in range(-half, half + 1):
                x = cx + dx
                y = cy + dy
                if erase:
                    self.update_pixel(x, y, (0, 0, 0))
                else:
                    self.update_pixel(x, y, color)

    def get_pixel_coord(self, event):
        x = int(self.canvas.canvasx(event.x) // self.pixel_size)
        y = int(self.canvas.canvasy(event.y) // self.pixel_size)
        return x, y

    def paint(self, event):
        x, y = self.get_pixel_coord(event)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.draw_brush(x, y, self.current_color, erase=False)

    def erase(self, event):
        x, y = self.get_pixel_coord(event)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.draw_brush(x, y, (0, 0, 0), erase=True)

    def clear_all(self):
        for y in range(self.height):
            for x in range(self.width):
                self.update_pixel(x, y, (0, 0, 0))

    def fill_all(self):
        for y in range(self.height):
            for x in range(self.width):
                self.update_pixel(x, y, self.current_color)

    def set_current_color(self, rgb):
        self.current_color = rgb
        self.color_indicator.config(bg=self.rgb_to_hex(rgb))

    def choose_color(self):
        color = colorchooser.askcolor(color=self.current_color, title="选择颜色")
        if color:
            self.set_current_color((int(color[0][0]), int(color[0][1]), int(color[0][2])))

    def rgb_to_hex(self, rgb):
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    # ---------- 形状生成 ----------
    def draw_shape(self, shape_type):
        self.clear_all()
        cx, cy = self.width // 2, self.height // 2
        size = min(self.width, self.height) // 3

        if shape_type == "circle":
            r = max(2, size)
            for y in range(self.height):
                for x in range(self.width):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                        self.update_pixel(x, y, self.current_color)
        elif shape_type == "square":
            half = max(1, size)
            x0, y0 = cx - half, cy - half
            x1, y1 = cx + half, cy + half
            for y in range(max(0, y0), min(self.height, y1 + 1)):
                for x in range(max(0, x0), min(self.width, x1 + 1)):
                    self.update_pixel(x, y, self.current_color)
        elif shape_type == "heart":
            scale = size * 0.8
            for y in range(self.height):
                for x in range(self.width):
                    nx = (x - cx) / scale
                    ny = (y - cy) / scale
                    val = (nx * nx + ny * ny - 1) ** 3 - nx * nx * ny ** 3
                    if val <= 0:
                        self.update_pixel(x, y, self.current_color)
        elif shape_type == "drop":
            radius = size * 0.6
            length = size * 1.4
            for y in range(self.height):
                for x in range(self.width):
                    dx = x - cx
                    dy = y - cy
                    if dy <= 0:
                        if dx * dx + dy * dy <= radius * radius:
                            self.update_pixel(x, y, self.current_color)
                    else:
                        t = dy / length
                        if t > 1:
                            continue
                        half = radius * (1 - t * t)
                        if abs(dx) <= half:
                            self.update_pixel(x, y, self.current_color)
        self.status_var.set(f"已绘制 {shape_type}")

    # ---------- 辅助绘图 ----------
    def _draw_line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if 0 <= x0 < self.width and 0 <= y0 < self.height:
                self.update_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    # ---------- 导出 C 数组 ----------
    def export_c_array(self):
        fmt = self.format_var.get()
        if fmt == "rgb565":
            data_type = "uint16_t"
            data = []
            for y in range(self.height):
                for x in range(self.width):
                    r, g, b = self.pixels[y][x]
                    val = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
                    data.append(f"0x{val:04X}")
        else:
            data_type = "uint8_t"
            data = []
            for y in range(self.height):
                for x in range(self.width):
                    r, g, b = self.pixels[y][x]
                    data.extend([f"0x{r:02X}", f"0x{g:02X}", f"0x{b:02X}"])
        per_line = 12
        lines = []
        for i in range(0, len(data), per_line):
            lines.append("    " + ", ".join(data[i:i + per_line]))
        array_text = ",\n".join(lines)
        c_code = f"""// 图标数据 - {self.width}x{self.height} - 格式 {fmt.upper()}
const {data_type} icon_data[] = {{
{array_text}
}};

typedef struct {{
    uint16_t width;
    uint16_t height;
    const {data_type}* data;
}} Icon;

const Icon my_icon = {{
    .width = {self.width},
    .height = {self.height},
    .data = icon_data
}};
"""
        dialog = tk.Toplevel(self.root)
        dialog.title("导出 C 数组")
        dialog.geometry("700x500")
        text_area = tk.Text(dialog, wrap=tk.NONE)
        text_area.insert(tk.END, c_code)
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=text_area.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text_area.config(yscrollcommand=scroll.set)

        def save():
            path = filedialog.asksaveasfilename(defaultextension=".h",
                                                filetypes=[("C Header", "*.h"), ("C Source", "*.c")])
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(c_code)
                messagebox.showinfo("成功", f"已保存至 {path}")

        ttk.Button(dialog, text="保存到文件", command=save).pack(pady=5)
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=5)

    # ---------- 项目保存/加载 ----------
    def save_project(self):
        path = filedialog.asksaveasfilename(defaultextension=".pix", filetypes=[("Pixel Editor", "*.pix")])
        if path:
            data = {"width": self.width, "height": self.height,
                    "pixels": [[list(rgb) for rgb in row] for row in self.pixels]}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            messagebox.showinfo("成功", "项目已保存")

    def load_project(self):
        path = filedialog.askopenfilename(filetypes=[("Pixel Editor", "*.pix")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.width = data["width"]
            self.height = data["height"]
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(self.width))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(self.height))
            self.pixels = [[tuple(rgb) for rgb in row] for row in data["pixels"]]
            self.redraw_canvas()
            messagebox.showinfo("成功", "项目已加载")


if __name__ == "__main__":
    root = tk.Tk()
    app = PixelEditor(root)
    root.mainloop()