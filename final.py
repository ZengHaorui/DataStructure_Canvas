import tkinter as tk
from tkinter import ttk, simpledialog, Menu, filedialog
from collections import deque
import copy
import json
import uuid


COLORS = {
	'background':	'#F5F5F5',
	'data_cell':	'#E8F5E9',
	'pointer_cell': '#FFF3E0',
	'struct_block': '#E0F7FA',
	'stack_queue':  '#FCE4EC',
	'highlight':	'#FFA726',
	'arrow':		'#616161'
}

class BaseElement:
	def __init__(self, canvas, x, y, name="", width=120, height=60):
		self.canvas = canvas
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.name = name
		self.id = None
		self.text_id = None
		self.selected = False
		self.parent = None
		self.pointers = []
		self.uuid = str(uuid.uuid4())

	def to_dict(self):
		return {
			"type": self.__class__.__name__,
			"uuid": self.uuid,
			"x": self.x,
			"y": self.y,
			"name": self.name,
			"width": self.width,
			"height": self.height,
			"parent_uuid": self.parent.uuid if self.parent else None
		}

	@classmethod
	def from_dict(cls, data, canvas):
		element = cls(canvas, data['x'], data['y'], data['name'], data['width'], data['height'])
		element.uuid = data['uuid']
		return element
	def contains(self, x, y):
		return (self.x < x < self.x + self.width and
				self.y < y < self.y + self.height)
				
	def draw(self):
		pass

	def move(self, dx, dy):
		for pointer in self.pointers:
			pointer.update_arrow()
		
		self.x += dx
		self.y += dy
		self.canvas.move(self.id, dx, dy)
		self.canvas.move(self.text_id, dx, dy)

	def set_highlight(self, state):
		self.selected = state
		self.canvas.itemconfig(self.id, outline=COLORS['highlight'] if state else 'black')

	def show_context_menu(self, event):
		menu = Menu(self.canvas, tearoff=0)
		menu.add_command(label="Rename", command=self.rename)
		menu.add_command(label="Copy", command=self.copy)
		menu.add_command(label="Delete", command=self.delete)
		if self.parent and isinstance(self.parent, Volume):
			menu.add_command(label="Move Out", command=self.move_out)
		menu.post(event.x_root, event.y_root)

	def move_out(self):
		self.canvas.lift(self.id)
		self.canvas.lift(self.text_id)
		if self.parent:
			self.parent.remove_element(self)
			self.x = self.parent.x + self.parent.width + 20
			self.y = self.parent.y
			self.parent = None
		print(self.name)
		self.draw()


	def rename(self):
		new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=self.name)
		if new_name:
			self.name = new_name
			self.update_text()

	def copy(self):
		new_obj = self.__class__(self.canvas, self.x+20, self.y+20)
		new_obj.name = self.name
		new_obj.width = self.width
		new_obj.height = self.height
		if isinstance(self, DataCell):
			new_obj.value = self.value
		new_obj.draw()
		#self.elements.append(StackQueue(self.canvas, 700, 100, "Queue", False))
		global app
		app.elements.append(new_obj)
		return new_obj
		
	def delete(self):
		try:
			self.on_delete()
		except:
			pass 
			
		for pointer in self.pointers.copy():
			if pointer.arrow:
				self.canvas.delete(pointer.arrow)
				pointer.arrow = None
		
		self.canvas.delete(self.id)
		self.canvas.delete(self.text_id)
		
		if self.parent and hasattr(self.parent, 'remove_element'):
			try:
				self.parent.remove_element(self)
			except:
				pass

	def update_text(self):
		self.canvas.itemconfig(self.text_id, text=self.name)

	def update_arrows(self):
		for pointer in self.pointers:
			pointer.update_arrow()




class Volume(BaseElement):
	
	def to_dict(self):
		data = super().to_dict()
		data["elements"] = [child.to_dict() for child in self.elements]
		return data

	@classmethod
	def from_dict(cls, data, canvas):
		volume = cls(canvas, data['x'], data['y'], data['name'], data['width'], data['height'])
		volume.uuid = data['uuid']
		return volume
	
	def __init__(self, canvas, x, y, name="", width=120, height=60):
		super().__init__(canvas, x, y, name, width, height)
		self.elements = []
		#self.children = []

	def copy(self):
		new_obj = self.__class__(self.canvas, self.x+20, self.y+20)
		new_obj.name = self.name
		new_obj.width = self.width
		new_obj.height = self.height
		if isinstance(self, DataCell):
			new_obj.value = self.value
		
		for ele in self.elements:
			
			new_obj.add_element(ele.copy())
			#self.elements.remove(self.selected_element)
		#new_obj.children=self.children
		'''
				if target_struct:
			target_struct.add_element(self.selected_element)
			if self.selected_element in self.elements:
				
				
		
		'''
		new_obj.draw()
		global app
		app.elements.append(new_obj)
		return new_obj


	def add_element(self, element):

		if element.parent != None:
			return
			
		element.parent = self
		self.elements.append(element)
		self.update_size()

	def remove_element(self, element):
		if element in self.elements:
			self.elements.remove(element)
			element.parent = None
			self.update_size()
			self.canvas.lift(element.id)
			self.canvas.lift(element.text_id)
			try:
				self.canvas.lift(element.dot)
			except:
				pass

	def update_size(self):
		self.rearrange_elements()
		self.draw()

	def delete(self):
		for elem in self.elements.copy():
			elem.delete()
		super().delete()

	def move(self, dx, dy):
		super().move(dx, dy)
		for elem in self.elements:
			elem.move(dx, dy)

	def rearrange_elements(self):
		pass
	# 其他现有方法保持不变...




class DataCell(BaseElement):
	def __init__(self, canvas, x, y, name="Data", value=""):
		super().__init__(canvas, x, y, name)
		self.value = value
		self.draw()

	def draw(self):
		if self.id:
			self.canvas.delete(self.id)
			self.canvas.delete(self.text_id)
		
		self.id = self.canvas.create_rectangle(
			self.x, self.y, self.x+120, self.y+60,
			fill=COLORS['data_cell'], outline='black', width=2)
		self.text_id = self.canvas.create_text(
			self.x+10, self.y+10, anchor=tk.NW,
			text=f"{self.name}\nValue: {self.value}", font=('Arial', 10))

	def edit_value(self):
		new_value = simpledialog.askstring("Edit Value", "Enter new value:", initialvalue=self.value)
		if new_value is not None:
			self.value = new_value
			self.update_text()

	def show_context_menu(self, event):
		menu = Menu(self.canvas, tearoff=0)
		menu.add_command(label="Rename & Change Value", command=self.rename_and_edit_value)
		menu.add_command(label="Copy", command=self.copy)
		menu.add_command(label="Delete", command=self.delete)
		if self.parent and isinstance(self.parent, Volume):
			menu.add_command(label="Move Out", command=self.move_out)
		menu.post(event.x_root, event.y_root)

	def rename_and_edit_value(self):
		dialog = tk.Toplevel(self.canvas)
		dialog.title("Rename & Change Value")
		
		tk.Label(dialog, text="Name:").grid(row=0, column=0, padx=5, pady=5)
		name_entry = tk.Entry(dialog)
		name_entry.insert(0, self.name)
		name_entry.grid(row=0, column=1, padx=5, pady=5)
		
		tk.Label(dialog, text="Value:").grid(row=1, column=0, padx=5, pady=5)
		value_entry = tk.Entry(dialog)
		value_entry.insert(0, self.value)
		value_entry.grid(row=1, column=1, padx=5, pady=5)
		value_entry.focus_set()
		
		def apply():
			self.name = name_entry.get()
			self.value = value_entry.get()
			self.update_text()
			dialog.destroy()
		
		tk.Button(dialog, text="OK", command=apply).grid(row=2, column=1, pady=5)
		
		dialog.transient(self.canvas.master)
		dialog.grab_set()
		self.canvas.master.wait_window(dialog)

	def update_text(self):
		self.canvas.itemconfig(self.text_id, text=f"{self.name}\nValue: {self.value}")

	
	def to_dict(self):
		data = super().to_dict()
		data["value"] = self.value
		return data

	@classmethod
	def from_dict(cls, data, canvas):
		cell = cls(canvas, data['x'], data['y'], data['name'])
		cell.uuid = data['uuid']
		cell.value = data['value']
		return cell

	# 其他现有方法保持不变...

class PointerCell(BaseElement):
	def __init__(self, canvas, x, y, name="Pointer"):
		super().__init__(canvas, x, y, name)
		self.target = None
		self.arrow = None
		self.draw()

	def on_delete(self):
		self.canvas.delete(self.dot)
		
	def draw(self):
		if self.id:
			self.canvas.delete(self.id)
			self.canvas.delete(self.text_id)
			self.canvas.delete(self.dot)
		
		self.id = self.canvas.create_rectangle(
			self.x, self.y, self.x+120, self.y+60,
			fill=COLORS['pointer_cell'], outline='black', width=2)
		self.dot = self.canvas.create_oval(
			self.x+60-5, self.y+30-5,
			self.x+60+5, self.y+30+5,
			fill='red', outline='black')
		self.text_id = self.canvas.create_text(
			self.x+10, self.y+10, anchor=tk.NW,
			text=self.name, font=('Arial', 10))

	def create_arrow(self, target):
		if self.target:
			self.target.pointers.remove(self)
		self.target = target
		target.pointers.append(self)
		self.update_arrow()

	def update_arrow(self):
		if self.arrow:
			self.canvas.delete(self.arrow)
		if not self.target:
			return
	
		start_x = self.x + 60
		start_y = self.y + 30
		
		
		
		
		target_center_x = self.target.x + self.target.width/2
		target_center_y = self.target.y + self.target.height/2
	
		dx = target_center_x - start_x
		dy = target_center_y - start_y
		
		if  self.target.contains(start_x,start_y):
			if abs(dx) > abs(dy):
				edge_x = self.target.x if dx > 0 else self.target.x + self.target.width
				end_x = edge_x
				ratio = (edge_x - start_x) / dx if dx != 0 else 0
				end_y = start_y + dy * ratio
			else:
				edge_y = self.target.y if dy > 0 else self.target.y + self.target.height
				end_y = edge_y
				ratio = (edge_y - start_y) / dy if dy != 0 else 0
				end_x = start_x + dx * ratio
		else:
			end_x=target_center_x
			end_y=target_center_y
			ratio=1.0
			while( self.target.contains(end_x,end_y) and ratio>0 ):
				ratio=ratio-0.02
				end_y = start_y + dy * ratio
				end_x = start_x + dx * ratio
		
		
		self.arrow = self.canvas.create_line(
			start_x, start_y, end_x, end_y,
			arrow=tk.LAST, fill=COLORS['arrow'], width=2)

	def move(self, dx, dy):
		super().move(dx, dy)
		self.canvas.move(self.dot, dx, dy)
		self.update_arrow()
		
	def to_dict(self):
		data = super().to_dict()
		data["target_uuid"] = self.target.uuid if self.target else None
		return data

	@classmethod
	def from_dict(cls, data, canvas):
		pointer = cls(canvas, data['x'], data['y'], data['name'])
		pointer.uuid = data['uuid']
		return pointer



class StructBlock(Volume):
	def __init__(self, canvas, x, y, name="Struct"):
		super().__init__(canvas, x, y, name, 230, 120)
		self.draw()

	def draw(self):
		self.width = max(200, 120 * len(self.elements) + 80)
		if self.id:
			self.canvas.delete(self.id)
			self.canvas.delete(self.text_id)
		
		self.id = self.canvas.create_rectangle(
			self.x, self.y, self.x+self.width, self.y+120,
			fill=COLORS['struct_block'], outline='black', width=2)
		self.text_id = self.canvas.create_text(
			self.x+10, self.y+10, anchor=tk.NW,
			text=self.name, font=('Arial', 12))
		self.rearrange_elements()

	def rearrange_elements(self):
		x_offset = 20
		y_offset = 40
		for i, elem in enumerate(self.elements):
			elem.x = self.x + x_offset + i * (elem.width + 10)
			elem.y = self.y + y_offset
			elem.draw()
			elem.update_arrows()
	
	@classmethod
	def from_dict(cls, data, canvas):
		struct = cls(canvas, data['x'], data['y'], data['name'])
		struct.uuid = data['uuid']
		struct.width = data.get('width', 230)
		struct.height = data.get('height', 120)
		return struct


class StackQueue(Volume):
	def __init__(self, canvas, x, y, name="Stack", is_stack=True):
		super().__init__(canvas, x, y, name, 150, 100)
		self.is_stack = is_stack
		self.draw()

	def draw(self):
		self.height = max(100, 90 + len(self.elements) * 65)
		if self.id:
			self.canvas.delete(self.id)
			self.canvas.delete(self.text_id)
		
		self.id = self.canvas.create_rectangle(
			self.x, self.y, self.x+150, self.y+self.height,
			fill=COLORS['stack_queue'], outline='black', width=2)
		self.text_id = self.canvas.create_text(
			self.x+10, self.y+10, anchor=tk.NW,
			text=f"{self.name}\nElements: {len(self.elements)}", font=('Arial', 12))
		self.rearrange_elements()

	def rearrange_elements(self):
		y_offset = 80
		le = len(self.elements)
		for i, elem in enumerate(self.elements):
			elem.x = self.x + (150 - elem.width)/2
			elem.y = self.y + y_offset + (le-i-1 if self.is_stack else i) * (elem.height + 5)
			elem.draw()
			elem.update_arrows()

	def remove_element(self):
		if not self.elements:
			return None
		elem = self.elements.pop() if self.is_stack else self.elements.pop(0)
		elem.parent = None
		self.update_size()
		return elem
	
	def to_dict(self):
		data = super().to_dict()
		data["is_stack"] = self.is_stack
		return data

	@classmethod
	def from_dict(cls, data, canvas):
		is_stack = data.get("is_stack", True)
		name = data.get("name", "Stack" if is_stack else "Queue")
		sq = cls(canvas, data['x'], data['y'], name, is_stack)
		sq.uuid = data['uuid']
		sq.width = data.get('width', 150)
		sq.height = data.get('height', 100)
		return sq





class DataStructureCanvas:

	def __init__(self, root):
		self.root = root
		self.root.title("Data Structure Whiteboard")
		self.root.geometry("1200x800")
		
		self.canvas = tk.Canvas(root, bg=COLORS['background'])
		self.canvas.pack(fill=tk.BOTH, expand=True)
		
		self.elements = []
		self.selected_element = None
		self.drag_start = None
		self.clipboard = None
		self.dragging_pointer = False
		self.right_click_pos = (0, 0)
		
		self.setup_bindings()
		self.create_context_menu()
		self.create_control_panel()
		self.show_grid = False
		self.grid_lines = []

		self.canvas.bind("<Configure>", self.draw_grid)  # 绑定画布大小改变事件
		
	def draw_grid(self, event=None):
		# 先删除旧网格
		for line in self.grid_lines:
			self.canvas.delete(line)
		self.grid_lines.clear()

		if not self.show_grid:
			return

		# 绘制新网格
		width = self.canvas.winfo_width()
		height = self.canvas.winfo_height()
		
		# 绘制垂直网格线
		for x in range(0, width, 30):
			line = self.canvas.create_line(x, 0, x, height, fill='#DDDDDD')
			self.canvas.lower(line)
			self.grid_lines.append(line)
		
		# 绘制水平网格线
		for y in range(0, height, 30):
			line = self.canvas.create_line(0, y, width, y, fill='#DDDDDD')
			self.canvas.lower(line)
			self.grid_lines.append(line)

	def toggle_grid(self):
		self.show_grid = not self.show_grid
		self.draw_grid()		
		
	def get_all_elements(self):
		all_elements = []
		for elem in self.elements:
			all_elements.append(elem)
			if isinstance(elem, Volume):
				all_elements.extend(elem.elements)
		return all_elements

	def refresh_all(self):
		for elem in self.elements:
			elem.draw()
		for elem in self.elements:
			if isinstance(elem, Volume):
				for child in elem.elements:
					child.draw()
		for item in self.canvas.find_all():
			if self.canvas.type(item) == 'line' and self.canvas.itemcget(item, 'arrow') != 'none':
				self.canvas.lift(item)
		
		#self.replace_rectangles()

	def setup_bindings(self):
		self.canvas.bind("<Button-1>", self.on_click)
		self.canvas.bind("<B1-Motion>", self.on_drag)
		self.canvas.bind("<ButtonRelease-1>", self.on_release)
		self.canvas.bind("<Double-Button-1>", self.on_double_click)
		self.canvas.bind("<Button-3>", self.on_right_click)

	def create_context_menu(self):
		self.blank_menu = Menu(self.canvas, tearoff=0)
		self.blank_menu.add_command(label="Paste", command=self.paste_element)
		self.blank_menu.add_command(label="Clear Canvas", command=self.clear_canvas)
		
		self.element_menu = Menu(self.canvas, tearoff=0)
		self.element_menu.add_command(label="Rename", command=lambda: self.selected_element.rename())
		self.element_menu.add_command(label="_Copy", command=lambda: self.selected_element.copy())
		self.element_menu.add_command(label="Delete", command=lambda: self.selected_element.delete())

	

	def on_click(self, event):

		self.drag_start = (event.x, event.y)
		if isinstance(self.selected_element, PointerCell):
			if self.canvas.find_withtag("current") == (self.selected_element.dot,):
				self.dragging_pointer = True
				return
		
		for elem in reversed(self.get_all_elements()):
			if elem.contains(event.x, event.y):
				if self.selected_element:
					self.selected_element.set_highlight(False)
				self.selected_element = elem
				elem.set_highlight(True)
				return
		
		if self.selected_element:
			self.selected_element.set_highlight(False)
			self.selected_element = None

	def on_drag(self, event):
				
		if self.dragging_pointer and isinstance(self.selected_element, PointerCell):
			for elem in self.get_all_elements():
				if elem != self.selected_element and elem.contains(event.x, event.y):
					self.selected_element.create_arrow(elem)
					return
			if self.selected_element.arrow:
				self.canvas.delete(self.selected_element.arrow)
				self.selected_element.arrow = None
				if self.selected_element.target:
					self.selected_element.target.pointers.remove(self.selected_element)
					self.selected_element.target = None
			return
		
		if self.selected_element and self.selected_element.parent is not None:
			return
		
		if self.selected_element:
			dx = event.x - self.drag_start[0]
			dy = event.y - self.drag_start[1]
			self.selected_element.move(dx, dy)
			self.drag_start = (event.x, event.y)

	def on_release(self, event):
		
		tmp=self.dragging_pointer
		
		self.dragging_pointer = False
		if not self.selected_element or self.dragging_pointer:
			return
		
		target_struct = None
		for elem in self.elements:
			if elem != self.selected_element and elem.contains(event.x, event.y) and isinstance(elem, Volume):
				target_struct = elem
				break
		
		if target_struct and not tmp:
			
			target_struct.add_element(self.selected_element)
			if self.selected_element in self.elements:
				self.elements.remove(self.selected_element)
				
		elif self.selected_element.parent and not tmp:
			try:
				self.selected_element.parent.remove_element(self.selected_element)
				self.elements.append(self.selected_element)
				self.selected_element.move(20,40)
			except:
				pass

	def on_double_click(self, event):
		for elem in reversed(self.get_all_elements()):
			if elem.contains(event.x, event.y):
				if isinstance(elem, DataCell):
					elem.rename_and_edit_value()
				elif isinstance(elem, StackQueue):
					popped = elem.remove_element()
					if popped:
						popped.x = elem.x + elem.width + 20
						popped.y = elem.y
						self.elements.append(popped)
						popped.draw()
				else:
					elem.rename()
				break

	def on_right_click(self, event):
		for elem in self.elements:
			if elem.contains(event.x, event.y):
				self.selected_element = elem
				elem.show_context_menu(event)
				return
		self.blank_menu.post(event.x_root, event.y_root)

	def paste_element(self):
		if self.clipboard:
			new_elem = copy.deepcopy(self.clipboard)
			new_elem.x = self.drag_start[0]
			new_elem.y = self.drag_start[1]
			new_elem.draw()
			self.elements.append(new_elem)

	def clear_canvas(self):
		for elem in self.elements.copy():
			elem.delete()
		self.elements.clear()

	def create_data_cell(self):
		self.elements.append(DataCell(self.canvas, 100, 100))

	def create_pointer_cell(self):
		self.elements.append(PointerCell(self.canvas, 200, 100))

	def create_struct_block(self):
		self.elements.append(StructBlock(self.canvas, 300, 100))

	def create_stack(self):
		self.elements.append(StackQueue(self.canvas, 500, 100))

	def create_queue(self):
		self.elements.append(StackQueue(self.canvas, 700, 100, "Queue", False))
	def save_to_file(self, filename):
		def collect_elements(elements):
			data = []
			for elem in elements:
				elem_data = elem.to_dict()
				if isinstance(elem, Volume):
					elem_data["elements"] = collect_elements(elem.elements)
				data.append(elem_data)
			return data
		
		elements_data = collect_elements(self.elements)
		with open(filename, 'w') as f:
			json.dump(elements_data, f, indent=2)

	def load_from_file(self, filename):
		self.clear_canvas()
		with open(filename, 'r') as f:
			elements_data = json.load(f)

		uuid_map = {}
		all_elements = []
		
		tmp={}
		
		def create_element(data):
			elem_type = data.get('type')
			if elem_type == 'DataCell':
				elem = DataCell.from_dict(data, self.canvas)
			elif elem_type == 'PointerCell':
				elem = PointerCell.from_dict(data, self.canvas)
				tmp[data.get('uuid')]=data.get('target_uuid')
			elif elem_type == 'StructBlock':
				elem = StructBlock.from_dict(data, self.canvas)
			elif elem_type == 'StackQueue':
				elem = StackQueue.from_dict(data, self.canvas)
			elif elem_type == 'Volume':
				elem = Volume.from_dict(data, self.canvas)
			else:
				return None
			uuid_map[data['uuid']] = elem
			all_elements.append(elem)
			if 'elements' in data:
				for child_data in data['elements']:
					child = create_element(child_data)
					if child:
						elem.add_element(child)
			return elem

		for data in elements_data:
			create_element(data)

		for elem in all_elements:
			if isinstance(elem, PointerCell):
				
				target_uuid = tmp[ elem.uuid ]
				#print(target_uuid)
				if target_uuid:
					#print(elem.name+' -> '+uuid_map.get(target_uuid).name)
					elem.create_arrow(uuid_map.get(target_uuid))
					

		self.elements = [elem for elem in all_elements if not elem.parent]
		self.refresh_all()

	def save(self):
		filename = filedialog.asksaveasfilename(
			defaultextension=".json",
			filetypes=[("JSON Files", "*.json")]
		)
		if filename:
			self.save_to_file(filename)

	def load(self):
		filename = filedialog.askopenfilename(
			filetypes=[("JSON Files", "*.json")]
		)
		if filename:
			self.load_from_file(filename)

	def create_control_panel(self):
		control_frame = ttk.Frame(self.root)
		control_frame.pack(side=tk.TOP, fill=tk.X)
		
		ttk.Button(control_frame, text="Data Cell", command=self.create_data_cell).pack(side=tk.LEFT)
		ttk.Button(control_frame, text="Pointer Cell", command=self.create_pointer_cell).pack(side=tk.LEFT)
		ttk.Button(control_frame, text="Struct Block", command=self.create_struct_block).pack(side=tk.LEFT)
		ttk.Button(control_frame, text="Stack", command=self.create_stack).pack(side=tk.LEFT)
		ttk.Button(control_frame, text="Queue", command=self.create_queue).pack(side=tk.LEFT)
		
		# 新增保存和载入按钮
		ttk.Button(control_frame, text="Save", command=self.save).pack(side=tk.RIGHT)
		ttk.Button(control_frame, text="Load", command=self.load).pack(side=tk.RIGHT)
		
		
		
		control_frame1 = ttk.Frame(self.root)
		control_frame1.pack(side=tk.TOP, fill=tk.X)
		ttk.Button(control_frame1, text="Clear", command=self.clear_canvas).pack(side=tk.RIGHT)
		ttk.Button(control_frame1, text="Refresh", command=self.refresh_all).pack(side=tk.RIGHT)
		ttk.Button(control_frame1, text="Toggle Grid", command=self.toggle_grid).pack(side=tk.RIGHT)

		ttk.Button(control_frame1, text="Copy", command=  lambda:self.safe("copy")   ).pack(side=tk.RIGHT)
		ttk.Button(control_frame1, text="Delete", command=lambda:self.safe("delete") ).pack(side=tk.RIGHT)
		

	def safe(self,func):
		try:
			if(func=='copy'):
				self.selected_element.copy()
			else:
				self.selected_element.delete()
		except:
			pass
	
	
	
	def create_rounded_rectangle(self, x1, y1, x2, y2, **kwargs):
		self.radius=5
		points = [
		 x1+self.radius, y1,
		 x1+self.radius, y1,
		 x2-self.radius, y1,
		 x2-self.radius, y1,
		 x2, y1,
		 x2, y1+self.radius,
		 x2, y1+self.radius,
		 x2, y2-self.radius,
		 x2, y2-self.radius,
		 x2, y2,
		 x2-self.radius, y2,
		 x2-self.radius, y2,
		 x1+self.radius, y2,
		 x1+self.radius, y2,
		 x1, y2,
		 x1, y2-self.radius,
		 x1, y2-self.radius,
		 x1, y1+self.radius,
		 x1, y1+self.radius,
		 x1, y1
	]
		return self.canvas.create_polygon(points, smooth=True,**kwargs)

	def replace_rectangles(self):
	
	# 分阶段处理保证元素ID不会冲突
		rect_data = []
	
	# 第一阶段：收集矩形数据
		for item in self.canvas.find_all():
			if self.canvas.type(item) == "rectangle":
				coords = self.canvas.coords(item)
				config = {
			  'fill': self.canvas.itemcget(item, 'fill'),
			  'outline': self.canvas.itemcget(item, 'outline'),
			  'width': self.canvas.itemcget(item, 'width'),
			  'tags': self.canvas.gettags(item)
		 }
				rect_data.append((item, coords, config))
	
	# 第二阶段：替换元素
		for item, coords, config in rect_data:
			x1, y1, x2, y2 = coords
			self.canvas.delete(item)  # 删除原矩形
		 
		 # 创建新圆角矩形并继承属性
			new_item = self.create_rounded_rectangle(
			x1, y1, x2, y2,
			fill=config['fill'],
			outline=config['outline'],
			width=config['width']
			)
		 
		 # 继承原始标签
			if config['tags']:
				self.canvas.itemconfig(new_item, tags=config['tags'])


if __name__ == "__main__":
	root = tk.Tk()
	app = DataStructureCanvas(root)
	root.mainloop()