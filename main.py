import requests
import configparser
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image, ImageDraw, EpsImagePlugin
from atproto import Client, client_utils
from io import BytesIO
from pathlib import Path

# Variables
bskyBlue = "#1083fe"

brushSize = 4
eraseRange = 8

xPrevious = 0
yPrevious = 0
LMBWasReleased = TRUE

# Get data from config.ini
config = configparser.ConfigParser(allow_no_value=True)
config.read("config.ini")
handle = (config["Login"]["bsky_handle"].encode('ascii', 'ignore')).decode("utf-8")
password = (config["Login"]["app_password"].encode('ascii', 'ignore')).decode("utf-8")
configLang = (config["Misc"]["language"].encode('ascii', 'ignore')).decode("utf-8")

if configLang == "":
    langs = ['en', 'ja']
else:
    langs = [configLang]

# Bluesky setup
client = Client()
loggedIn = FALSE
postBtnBG = "#f1f3f5"
postBtnFG = "black"
pfpOriginal = Image.open("assets/notLoggedIn.png").resize((18, 18))

try: 
    account = client.login(handle, password)
except:
    messagebox.showerror("Unable to log in", "SkyDraw couldn't log in to your Bluesky account :(")
else:
    loggedIn = TRUE
    avatar = requests.get(account.avatar)
    pfpOriginal = Image.open(BytesIO(avatar.content)).resize((18, 18))
    postBtnBG = bskyBlue
    postBtnFG = "white"

# PIL canvas setup
canvasPath = Path("canvas/")
canvasPath.mkdir(exist_ok=True)
imgPath = "canvas/canvas.png"

# Update brush and eraser size
def update_size(event):
    global brushSize, eraseRange
    brushSize = int(brushSizeSlider.get())
    eraseRange = int(eraseRangeSlider.get())

# Save canvas as PNG
def save_as_png():
    canvas.postscript(file="canvas/canvas.eps", pagewidth=511)
    img = Image.open("canvas/canvas.eps")
    img.save(imgPath, "png")

# Clear canvas
def clear_canvas():
    canvas.delete("all")

# Post to Bluesky
def post_to_bsky():
    save_as_png()

    if loggedIn:
        postText = client_utils.TextBuilder()
        postText.text(captionInput.get() + " ")
        postText.tag("#SkyDraw", "SkyDraw")

        with open(imgPath, 'rb') as f:
            img_data = f.read()

        try:
            client.send_image(text=postText, image=img_data, image_alt="", langs=langs)
        except:
            messagebox.showerror("Unable to post", "Couldn't post for some reason???")
        else:
            captionInput.delete(0, END)
            clear_canvas()
    
    else:
        messagebox.showerror("Unable to post", "SkyDraw is not logged in to your Bluesky account.")

# Window setup
window = Tk()
window.title("SkyDraw")
window.minsize(512, 580)
window.iconbitmap("assets/icon.ico")

pfpTk = ImageTk.PhotoImage(pfpOriginal)

topSpace = Frame(width=512, height=512)
canvas = Canvas(topSpace, width=512, height=512, bg="white", highlightthickness=0)
row1 = Frame(window, width=512)
row2 = Frame(window, width=512)
brushSizeSlider = Scale(row1, from_=1, to=64, orient=HORIZONTAL, command=update_size)
eraseRangeSlider = Scale(row1, from_=1, to=64, orient=HORIZONTAL, command=update_size)
captionInput = Entry(row2)
clearButton = Button(row2, text="Clear Canvas", command=clear_canvas)
postButton = Button(row2, text="Post to Bluesky ", image=pfpTk, compound="right", fg=postBtnFG, bg=postBtnBG, command=post_to_bsky)

# Place and pack elements
topSpace.pack(side=TOP, fill="both", expand=TRUE)
canvas.place(relx=0.5, rely=0.5, anchor="c")

row2.pack(side=BOTTOM, fill="x")
row1.pack(side=BOTTOM, fill="x")
Label(row1, text="Brush Size: ").pack(side=LEFT)
brushSizeSlider.pack(side=LEFT, fill="x", expand=TRUE)
Label(row1, text="   Erase Range: ").pack(side=LEFT)
eraseRangeSlider.pack(side=LEFT, fill="x", expand=TRUE)
Label(row2, text="Caption: ").pack(side=LEFT)
captionInput.pack(side=LEFT, fill="x", expand=TRUE)
postButton.pack(side=RIGHT)
clearButton.pack(side=RIGHT)

# Set sliders to default values
brushSizeSlider.set(brushSize)
eraseRangeSlider.set(eraseRange)

# Change post button color when hovering over it
def post_hover(event):
    if loggedIn:
        postButton["bg"] = "#0168d5"
def post_not_hover(event):
    if loggedIn:
        postButton["bg"] = bskyBlue
postButton.bind("<Enter>", post_hover)
postButton.bind("<Leave>", post_not_hover)

# Drawing on canvas
def draw(event):
    global xPrevious, yPrevious, LMBWasReleased

    x = event.x
    y = event.y

    if LMBWasReleased:
        xPrevious = x
        yPrevious = y
    
    canvas.create_line(xPrevious, yPrevious, x, y, width=brushSize, fill=bskyBlue, capstyle="round", joinstyle="round")
    LMBWasReleased = FALSE
    xPrevious = x
    yPrevious = y

def LMB_released(event):
    global LMBWasReleased
    LMBWasReleased = TRUE   

def erase(event):
    x = event.x
    y = event.y

    inRange = canvas.find_overlapping(x-eraseRange, y-eraseRange, x+eraseRange, y+eraseRange)
    for stroke in inRange:
        canvas.delete(stroke)

# Draw bindings
canvas.bind("<B1-Motion>", draw)
window.bind("<ButtonRelease-1>", LMB_released)
canvas.bind("<B3-Motion>", erase)

# Run program
window.mainloop()