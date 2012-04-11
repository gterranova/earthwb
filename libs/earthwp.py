import os
import urllib, urllib2, re
from time import time, sleep

from win32con import *
from ctypes import *

import wx

import PIL, time, glob, random, os, sys
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont

import path, exif

DATE_FORMAT = '%d/%m/%Y %H:%M'
EARTH_VIEW_URL = "http://www.fourmilab.ch/cgi-bin/Earth?imgsize=520&opt=-l&lat=45.27&ns=North&lon=9.11&ew=East&alt=148351039&img=learth.evif&dynimg=y"
ORTHO_VIEW_URL = "http://static.die.net/earth/rectangular/1280.jpg"
SEARCH_URL = "http://www.codefromthe70s.org/cgi/desktopearthgen.exe?width=%d&height=%d&center=%d&bars=%d&clouds=%d&utc=%.2f"

def setWallPaperFromBmp(pathToBmp):
    """ Given a path to a bmp, set it as the wallpaper """
    result = windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, pathToBmp,
                                                 SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE)
    if not result:
        raise Exception("Unable to set wallpaper.")

def paste_image(im, pathToImage, **args):
    (destx, desty) = im.size
    bmpImage = Image.open(pathToImage)
    (x, y) = bmpImage.size

    (x0, y0) = (0, 0)
    if args.has_key('valign'):
        if args['valign'] == "center":
            y0 = (desty-y)/2
        elif args['valign'] == "bottom":
            y0 = desty-y-25

    if args.has_key('halign'):
        if args['halign'] == "center":
            x0 = (destx-x)/2
        elif args['halign'] == "right":
            x0 = destx-y
            
    im.paste(bmpImage, (x0,y0, x+x0, y+y0))

def resize(img, box, fit, out=''):
    '''Downsample the image.
@param img: Image -  an Image-object
@param box: tuple(x, y) - the bounding box of the result image
@param fix: boolean - crop the image to fill the box
@param out: file-like-object - save the image into the output stream
'''
    #preresize image with factor 2, 4, 8 and fast algorithm
    factor = 1
    while img.size[0]/factor > 2*box[0] and img.size[1]*2/factor > 2*box[1]:
        factor *=2
    if factor > 1:
        img.thumbnail((img.size[0]/factor, img.size[1]/factor), Image.NEAREST)
    #calculate the cropping box and get the cropped part
    if fit:
        x1 = y1 = 0
        x2, y2 = img.size
        wRatio = 1.0 * x2/box[0]
        hRatio = 1.0 * y2/box[1]
        if hRatio > wRatio:
            y1 = y2/2-box[1]*wRatio/2
            y2 = y2/2+box[1]*wRatio/2
        else:
            x1 = x2/2-box[0]*hRatio/2
            x2 = x2/2+box[0]*hRatio/2
        img = img.crop((int(x1),int(y1),int(x2),int(y2)))
    #Resize the image with best quality algorithm ANTI-ALIAS
    img.thumbnail(box, Image.ANTIALIAS)

    #save it into a file-like object
    if not out == '':
        img.save(out, "JPEG", quality=75)
        
    return img

def exif_getdate(filename):
    """ Rename <old_filename> with the using the date/time created or
modified for the new file name"""

    created_time = os.path.getctime(filename)
    modify_time = os.path.getmtime(filename)

#    f = open(filename, 'rb')
    try:
        tags=exif.parse(filename)
    except UnboundLocalError:
        print "No EXIF data available for ", file
        tags = {}
        exif_time = 0
    try:
        tags['DateTimeOriginal']
        exif_time = str(tags['DateTimeOriginal'])
        exif_time = int(time.mktime(time.strptime(exif_time,
"%Y:%m:%d %H:%M:%S")))
    except (KeyError,ValueError):
        print 'No EXIF DateTimeOriginal for ', file
        exif_time = 0

    if created_time < modify_time:
        local_time = time.localtime(created_time)
    else:
        local_time = time.localtime(modify_time)

    if exif_time:
        if exif_time < local_time:
            local_time = time.localtime(exif_time)

    date_time_name = time.strftime(DATE_FORMAT, local_time)

    #print 'Created Time  = ', created_time
    #print 'Modified Time = ', modify_time
    #print 'EXIF Time     = ', exif_time
    #print 'Time Used     = ', local_time
    return date_time_name

# Generate Polaroid-looking images
def make_polaroid(infile, outfile, text=''):
    base = (265,271)    #size of polaroid background
    polaroid = Image.open('graphics/polaroid-1.png')
    polaroid = ImageOps.fit(polaroid, base, Image.ANTIALIAS, 0, (0.5,0.5))
 
    target = (238,194); # size of empty target area on polaroid background
    img = Image.open(infile)    
    img = resize(img, target, True, '')
    img = ImageOps.fit(img, target, Image.ANTIALIAS, 0, (0.5,0.5))
 
    #enhance the image a bit
#    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
 
    #draw the text, if any
    if not text == '':
        font = ImageFont.truetype("graphics/GHOSTWRITER.TTF", 18)
        text_size = ImageDraw.Draw(polaroid).textsize(text, font=font)
        fontxy = (base[0]/2 - text_size[0]/2, 230)
        ImageDraw.Draw(polaroid).text(fontxy, text, font=font, fill=(40,40,40))
 
    #copy the image onto the polaroid background
    imgcorner = (15,20) #paste image onto polaroid
    polaroid.paste(img, imgcorner)
 
    #copy the whole thing onto a larger background and rotate randomly
    angle = random.randint(-10,10)
    blank = Image.new(polaroid.mode, (380,380))
    blank.paste(polaroid, (blank.size[0]/2-polaroid.size[0]/2, blank.size[1]/2-polaroid.size[1]/2))
    blank = blank.rotate(angle, Image.BICUBIC)
 
    blank.save(outfile)
    
def setWallPaper(pathToImage, **args):
    """ Given a path to an image, convert it to bmp format and set it as the wallpaper"""
    newPath = os.getcwd()
    newPath = os.path.join(newPath, 'pywallpaper.bmp')

    newImage = Image.new("RGB", (1280,1024))
    paste_image(newImage, pathToImage, **args)
    paste_image(newImage, pathToImage, **args)

    newImage.save(newPath, "BMP")    
    setWallPaperFromBmp(newPath)

def get_mqotd():
    f = opener.open('http://feeds.feedburner.com/quotationspage/mqotd')
    data = f.read()
    f.close()
    authors = extract(data,"<title>","</title>")
    quotes = extract(data,"<description>\"","\"")
    ret = []
    for i in range(0, len(quotes)):
        ret.append( {'author': authors[2+i], 'quote': quotes[i] } )
        
    return ret
    
def draw_word_wrap(draw, text, max_width=130, font=ImageFont.load_default()):
    '''Draw the given ``text`` to the x and y position of the image, using
    the minimum length word-wrapping algorithm to restrict the text to
    a pixel width of ``max_width.``
    '''
##    draw = ImageDraw(img)
    text_size_x, text_size_y = draw.textsize(text, font=font)
    remaining = max_width
    space_width, space_height = draw.textsize(' ', font=font)
    # use this list as a stack, push/popping each line
    output_text = []
    # split on whitespace...    
    for word in text.split(None):
        word_width, word_height = draw.textsize(word, font=font)
        if word_width + space_width > remaining:
            output_text.append(word)
            remaining = max_width - word_width
        else:
            if not output_text:
                output_text.append(word)
            else:
                output = output_text.pop()
                output += ' %s' % word
                output_text.append(output)
            remaining = remaining - (word_width + space_width)
    return output_text

def extract(text, sub1, sub2):
    """extract a substring between two substrings sub1 and sub2 in text"""   
    ret = []
    a1 = text.split(sub1)
    if (len(a1)>1):
        for t1 in a1[1:]:
            a2 = t1.split(sub2)
            if len(a2)>1:
                #ret.append(sub1 + a2[0] + sub2)
                ret.append(a2[0])      
        return ret
    return []

##    def getWallpaper(self, filename):

##        while 1:
##            f = self.opener.open(SEARCH_URL % (1024, 640, 4, 1, 1, time()))
##
##            fout = file (filename, 'wb')
##            
##            while 1:
##                chunk = f.read(100000)
##                if not chunk: break
##                fout.write (chunk)
##            fout.close()
##            f.close()
##            setWallPaper(filename)

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 GTB5 (.NET CLR 3.5.30729)')]
urllib2.install_opener(opener)

def readPyValFromConfig(conf, name):
    value = conf.Read(name).replace('\r\n', '\n')+'\n'
    print eval(value)
    try:
        return eval(value)
    
    except:
        print "'"+value+"'"
        raise
    
class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, pos=(100, 100))
       
        self.tbicon = wx.TaskBarIcon()
        ##self.tbicon.SetIcon(res.cs_icon.GetIcon(), "Earth Wallpaper")
        self.tbicon.SetIcon(wx.Icon('graphics/monitor-wallpaper.png', wx.BITMAP_TYPE_PNG), "Earth Wallpaper")

        # Bind some events to it
        wx.EVT_TASKBAR_LEFT_DCLICK(self.tbicon, self.OnMenuCheck) # left click        
        wx.EVT_TASKBAR_RIGHT_UP(self.tbicon, self.ShowMenu) # single left click
        wx.EVT_CLOSE(self,self.OnClose) # triggered when the app is closed, which deletes the icon from tray

        # build the menu that we'll show when someone right-clicks
        self.menu = wx.Menu() # the menu object

        self.menu.Append(103, 'About...') # About
        wx.EVT_MENU(self, 103, self.OnMenuShowAboutBox) # Bind a function to it

        self.menu.Append(104, 'Close') # Close
        wx.EVT_MENU(self, 104, self.OnMenuClose) # Bind a function to it
   

        self.quotes = get_mqotd()

        cfg = None
        configFile = os.path.abspath('settings.cfg')
        if not os.path.exists(configFile):
            f = file ("configFile", 'wb')
            f.close()
            cfg = wx.FileConfig(localFilename=configFile, style= wx.CONFIG_USE_LOCAL_FILE)
            cfg.Write("PHOTO_PATH", "['']")
        else:
            cfg = wx.FileConfig(localFilename=configFile, style= wx.CONFIG_USE_LOCAL_FILE)
        PHOTO_PATH = readPyValFromConfig(cfg, "PHOTO_PATH")
        DATE_FORMAT = cfg.Read("DATE_FORMAT", '%d/%m/%Y %H:%M')
        print PHOTO_PATH        
        self.filelist = []
        for base in PHOTO_PATH:
            if base != '':
                srcpath = path.path(base)
                for thispath in srcpath.walkfiles():
                    thatpath = srcpath.relpathto(thispath)
                    ext = thatpath.lower()[-4:]
                    if ext in ['.jpg']:        
                        self.filelist.append(os.path.join(base, thatpath))
                    
        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(600*1000)
        self.OnTimer(evt=True)

    def OnClose(self, evt):
        self.Show(False)
        pass
        
    def ShowMenu(self, event):
        self.PopupMenu(self.menu) # show the popup menu

    def OnMenuCheck(self, event):
        self.OnTimer(None)
       
    def OnMenuShowAboutBox(self, evt):
        # First we create and fill the info object
        info = wx.AboutDialogInfo()
        info.Name = "Earth Wallpaper"
        info.Version = "1.0"
        info.Copyright = "Copyright (c) 2009, Gianpaolo Terranova"
        info.Description = "Change Wallpaper"
        info.WebSite = ("http://www.terranovanet.it", "Author's website")
        info.Developers = [ "Gianpaolo Terranova" ]
        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)
        
    def OnMenuClose(self, evt):
        self.tbicon.RemoveIcon() # remove the systemtray icon when the program closes
        self.Unbind(wx.EVT_TIMER)
        self.timer.Stop()
        self.timer = None
        wx.GetApp().ExitMainLoop()        

    def OnTimer(self, evt):
        if 0:
            f = opener.open(ORTHO_VIEW_URL)
            fout = file ("cache/ortho.jpg", 'wb')
            while 1:
                chunk = f.read(100000)
                if not chunk: break
                fout.write (chunk)
            fout.close()
            f.close()
            
        if evt != None:
            f = opener.open(EARTH_VIEW_URL)
            fout = file ("cache/earth.jpg", 'wb')
            while 1:
                chunk = f.read(100000)
                if not chunk: break
                fout.write (chunk)
            fout.close()
            f.close()


        quote = random.choice(self.quotes)
       
        newImage = Image.new("RGB", (1280,1024))
        if 0:
            paste_image(newImage, "cache/ortho.jpg", valign='bottom', halign='center')
            
        paste_image(newImage, "cache/earth.jpg", valign='center', halign='center')

        if len(self.filelist) > 0:
            filename = random.choice(self.filelist)
            text = exif_getdate(filename)
            make_polaroid(filename, "cache/polaroid.jpg", text)
            paste_image(newImage, "cache/polaroid.jpg", valign='bottom', halign='right')        


        draw = ImageDraw.Draw(newImage)
        font = ImageFont.truetype("graphics/GHOSTWRITER.TTF", 20)
        lines = draw_word_wrap(draw, '"'+quote['quote']+'"', max_width=600, font=font)

        ypos = 800
        for text in lines:
            text_size_x, text_size_y = draw.textsize(text, font=font)
            fontxy = ((1280 - text_size_x)/2, ypos)
            draw.text(fontxy, text, font=font, fill=(255, 255, 255))
            ypos += text_size_y

        text_size_x, text_size_y = draw.textsize(quote['author'], font=font)
        fontxy = ((1280-600)/2+600-text_size_x, ypos+10)
        draw.text(fontxy, quote['author'], font=font, fill=(255, 255, 255))
        
        newPath = os.getcwd()
        newPath = os.path.join(newPath, 'pywallpaper.bmp')
        newImage.save("pywallpaper.bmp", "BMP")    

        setWallPaperFromBmp(newPath)
        
class MyApp(wx.App): 
    def OnInit(self):
        self.frame = MyFrame(None, -1, "Earth Wallpaper")     
        self.frame.Show(False)
        self.SetTopWindow(self.frame)
        return True
    
def main():
    app = MyApp(redirect=False)
    app.MainLoop()
  
if __name__ == "__main__":
    main()

    


    
