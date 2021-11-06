from tkinter import *
from tkinter import ttk
from libs.crawler import Crawler
from ttkbootstrap import Style
import threading
import os


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class GUI:
    def __init__(self):
        style = Style(theme="journal")
        Style.configure(style, 'TButton', font=('Helvetica', 11, 'bold'))
        self.root = style.master
        self.root.title("Google Map Businesses Extractor")
        self.root.state("zoomed")
        self.root.iconbitmap(os.path.join(os.getcwd(), resource_path("icon.ico")))
        # Frames
        self.left_frame = ttk.Labelframe(self.root, text="Browser", width=500, borderwidth=2, style="light.TLabelframe", padding=20)
        self.right_frame = ttk.Labelframe(self.root, text="Results", width=700, borderwidth=2,  style="light.TLabelframe")
        self.left_frame.pack(side=LEFT, expand=True, fill=BOTH, padx=10, pady=10)
        self.right_frame.pack(side=LEFT, expand=True, fill=BOTH, padx=10, pady=10)
        # Table
        self.table = ttk.Treeview(self.right_frame, style="info.Treeview")
        self.table['show'] = 'headings'
        self.table_style()
        self.table_scroll()
        self.create_table()
        self.table.pack(padx=10, pady=10, expand=True, fill=BOTH)
        # Search Field
        self.output_format_title = ttk.Label(self.left_frame, text="Result Output Format", font=('Helvetica', 11, 'bold'))
        self.output_format_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10)
        output = StringVar()
        output.set("Text")
        self.output_format1 = ttk.Radiobutton(self.left_frame, text='Text', value="Text", variable=output, style='info.TRadiobutton')
        self.output_format1.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=4)
        # self.output_format1 = ttk.Radiobutton(self.left_frame, text='Excel', value="Excel", variable=output, style='info.TRadiobutton')
        # self.output_format1.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=4)
        # self.output_format1 = ttk.Radiobutton(self.left_frame, text='JSON', value="JSON", variable=output, style='info.TRadiobutton')
        # self.output_format1.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=4)

        self.search_title = ttk.Label(self.left_frame, text="Search Your Query", font=('Helvetica', 11, 'bold'))
        self.search_title.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=10)
        self.search_input = ttk.Entry(self.left_frame, width=50, style="info.TEntry")
        self.search_input.grid(row=5, column=0, padx=10)
        self.search_button = ttk.Button(self.left_frame, text="Search", command=self.get_query, style="success.TButton")
        self.search_button.grid(row=5, column=1)

    def get_query(self):
        query = self.search_input.get()
        if len(query.strip()) is 0:
            return False
        self.search_button.grid_remove()
        self.search_button = ttk.Button(self.left_frame, text="Search", command=self.get_query, style="success.TButton", state=DISABLED)
        self.search_button.grid(row=5, column=1)
        self.search_on_browser(query)

    def table_scroll(self):
        table_scroll_y = ttk.Scrollbar(self.right_frame)
        table_scroll_y.configure(command=self.table.yview)
        table_scroll_x = ttk.Scrollbar(self.right_frame, orient='horizontal')
        table_scroll_x.configure(command=self.table.xview)
        self.table.configure(xscrollcommand=table_scroll_x.set, yscrollcommand=table_scroll_y.set)
        table_scroll_y.pack(side=RIGHT, fill=Y)
        table_scroll_x.pack(side=BOTTOM, fill=X)

    def table_style(self):
        style = ttk.Style(self.table)
        style.configure("Treeview.Heading", font=('Helvetica', 11, 'bold'))

    def create_table(self):
        self.table['columns'] = (
            'name', 'category', 'rating', 'address', 'website', 'phone_no', 'plus_code', 'image_link', 'review_count',
            'latitude', 'longitude', 'photo_tags', 'working_hours')
        self.table.column("name", anchor=CENTER)
        self.table.column("category", anchor=CENTER)
        self.table.column("rating", anchor=CENTER)
        self.table.column("address", anchor=CENTER)
        self.table.column("website", anchor=CENTER)
        self.table.column("phone_no", anchor=CENTER)
        self.table.column("plus_code", anchor=CENTER)
        self.table.column("image_link", anchor=CENTER)
        self.table.column("review_count", anchor=CENTER)
        self.table.column("photo_tags", anchor=CENTER)
        self.table.column("working_hours", anchor=CENTER)
        self.table.column("latitude", anchor=CENTER)
        self.table.column("longitude", anchor=CENTER)
        self.table.heading("name", text="Name", anchor=CENTER)
        self.table.heading("category", text="Category", anchor=CENTER)
        self.table.heading("rating", text="Rating", anchor=CENTER)
        self.table.heading("address", text="Address", anchor=CENTER)
        self.table.heading("website", text="Website", anchor=CENTER)
        self.table.heading("phone_no", text="Phone No.", anchor=CENTER)
        self.table.heading("plus_code", text="Plus Code", anchor=CENTER)
        self.table.heading("image_link", text="Image", anchor=CENTER)
        self.table.heading("review_count", text="Reviews", anchor=CENTER)
        self.table.heading("latitude", text="Latitude", anchor=CENTER)
        self.table.heading("longitude", text="Longitude", anchor=CENTER)
        self.table.heading("photo_tags", text="Photo Tags", anchor=CENTER)
        self.table.heading("working_hours", text="Working Hours", anchor=CENTER)

    def search_on_browser(self, query):
        crawler = Crawler(query, self)
        thread_1 = threading.Thread(target=crawler.crawl)
        thread_1.start()

    def add_label(self, title):
        label = ttk.Label(self.left_frame, text=title, style="success.TLabel", font=('Helvetica', 11, 'bold'))
        label.grid(sticky="w", padx=10, pady=5)
        return label

    def insert_row(self, i, obj):
        self.table.insert('', i, text="", values=(
            obj["name"], obj["category"], obj["rating"], obj["address"], obj["website"], obj["phone"], obj["plus_code"],
            obj["main_image"], obj["review_count"], obj["location"]["latitude"], obj["location"]["longitude"],
            obj["photo_tags"], "Done"))
