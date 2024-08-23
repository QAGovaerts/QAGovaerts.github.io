---
title: Copying LaTeX equations with OCR
date: 2024-08-22 19:00:00 +0200
categories: [student]
tags: [latex, docker, ocr, student, bettertouchtool, macos] # TAG names should always be lowercase
---

I often like making summaries for my university courses in LaTeX. One of the big time consumers when writing these summaries is copying over the equations from the textbooks. So I went looking for a way to automate this process, so I no longer had to type over each equation.

After some searching online, I found the [pix2tex LaTeX OCR](https://github.com/lukas-blecher/LaTeX-OCR) Python library that does exactly what I was looking for. It takes a screenshot from an equation as input and outputs the LaTeX code for the equation.


## A quick web demo test

I first tested the library by spinning up a quick demo container

```shell
docker run --rm -it -p 8501:8501 --entrypoint python lukasblecher/pix2tex:api pix2tex/api/run.py
```

This launches a simple web interface at [http://localhost:8501](http://localhost:8501) where you can drag and drop images of equations in a box, and it gives you the LaTeX code of the equation. After trying a bunch of equations this way, I found that it worked well and reliable enough for me. This is all fun and games, but this is not a solution that I like to use, it takes way to many clicks before I get the LaTeX code. I saw that the intended use of the Docker container is to work as an API instead of a web interface so it is time to script some stuff together.


## A complete workflow with BetterTouchTool

After some playing around with different automation tools I got the following, somewhat cumbersome, workflow working. I have BetterTouchTool (BTT) listening to a keyboard shortcut (⇧+⌘+8 in my case, but it can be any trigger). BTT then launches the built-in macOS screenshot tool that allows me to take a screenshot from the selection of the screen containing the equation I want to copy. When the screenshot is taken BTT copies it to the clipboard and launches a Python program. This Python program talks to the pix2tex API that is running in a Docker container on my home server. It sends the screenshot to the pix2tex LaTeX OCR service and when it gets the LaTeX code back, it copies it to the clipboard and sends a notification that the code is ready to be pasted. 

> [BetterTouchTool](https://folivora.ai/) is a great, feature packed app that allows you to customize various input devices on your Mac. I mainly use it to define custom keyboard shortcuts and trackpad gestures running all kinds of actions in different apps, but it houses a lot more functionalities.
{: .prompt-tip }


### The pix2tex API Docker container

The place where the magic happens is in the pix2tex Docker container. I run it with a very straightforward Docker compose script with Portainer on my home server. The most important part to note here is the port `8502` on which the API is listening.

```yaml
services:
    pix2texAPI:
        container_name: pix2texAPI
        ports:
            - 8502:8502
        image: lukasblecher/pix2tex:api
```
{: file='docker-compose.yaml'}


### The Python script

The Python script was for me the easiest way to get the image from the clipboard to the pix2tex API. But I'm sure there are a lot of other programming languages that can do just the same.

```python
import requests
from PIL import ImageGrab
from io import BytesIO
import clipboard
from pync import Notifier


# URL the API is listening on
URL = "http://my-server-IP:8502/predict/"

# Get the image from the clipboard
image = ImageGrab.grabclipboard()

# If there's an image in the clipboard
if image is not None:
    # Save the image to a BytesIO object
    image_io = BytesIO()
    image.save(image_io, format='PNG')
    image_io.seek(0)  # Rewind the file pointer to the beginning

    # Send the image to the server
    files = {'file': ('screenshot.png', image_io, 'image/png')}
    response = requests.post(URL, files=files)

    # If the server returns an error
    if response.status_code != 200:
        # Notify the user that there was an error
        Notifier.notify("There was an error.", title="LaTeX ORC failed", sound="funk", sender="com.apple.Terminal")
    else:
        # Copy the response
        clipboard.copy(response.text.strip('"').replace("\\\\", "\\"))

        # Notify the user that the LaTeX has been copied to the clipboard
        Notifier.notify("Copied LaTeX to clipboard.", title="LaTeX ORC successful", sound="funk", sender="com.apple.Terminal")
else:
    # Notify the user that there's no image in the clipboard
    Notifier.notify("No image in clipboard.", title="LaTeX ORC failed", sound="funk", sender="com.apple.Terminal")
```
{: file='LaTeXOCR.py'}

The code is really straightforward. First I define the URL the API is listening on. In my case it is the internal IP address of my home server followed by `:8502/predict/`. Note the port `8502` we defined previously in the Docker compose stack. The script then grabs the screenshot that BTT copied to the clipboard. If there is an image in the clipboard, it sends it to the API and when the request gets back successful, it copies the response LaTeX code to the clipboard. At last, it notifies the user. For the notifications I use the [pync](https://pypi.org/project/pync/) Python library which is a Python wrapper for the macOS notification center. For the sound you can choose any of the sound names listed in `/System/Library/Sounds`. The `sender="com.apple.Terminal"` is just there so that a nice terminal icon will show up in the notification.


### The BetterTouchTool action

In BTT I defined a global custom shortcut (⇧+⌘+8 in my case, but it can be any trigger). For this trigger I selected the capture screenshot action

![BTT capture screenshot action](/assets/img/posts/2024-08-22-copying_latex_equations_with_ocr/BetterTouchTool_screenshot_action.png){: width="300"}
_BTT capture screenshot action_

In the screenshot action configuration window I set the capture mode to "Interactively". I can leave the other options unchecked except for the last one saying "Only copy to clipboard". I checked this because I don't need to save these screenshots anywhere, I only want them on the clipboard where my Python script can grab them. 

![BTT capture screenshot action settings](/assets/img/posts/2024-08-22-copying_latex_equations_with_ocr/BetterTouchTool_screenshot_action_settings.png){: width=600"}
_BTT capture screenshot action settings_

The only thing left now is to actually run this python script after the screenshot is taken. I did this by selecting "Run terminal command" in the option "After capture:". As terminal command I typed `python3 /path_to/LaTeXOCR.py` where `path_to` is the absolute path to the place where the Python script is stored.

![BTT capture screenshot action terminal command](/assets/img/posts/2024-08-22-copying_latex_equations_with_ocr/BetterTouchTool_terminal_command.png){: width=600"}
_BTT capture screenshot action terminal command_

With this configured everything runs flawlessly. Now I can copy-paste the equations really easily by simply taking a screenshot and waiting a second for the result to come back.


## Conclusion

This stupid simple (but at the same time probably unnecessary complex) workflow allowed me to save a lot of time when writing summaries. Especially when they involve a lot of equations. The pix2tex library has surprised me in its accuracy. It mostly performs really well. The cases I noted that it had the most difficulty is when the equations in the textbooks are written in another font than the default LaTeX font. I also experienced that it seems to randomly decide when to use `\big( ... \big)` (or one of its variants) and when to use `\left( ... \right)`. It always makes sure that the correct brackets are matched with the correct size prefix, but I like the `\left( ... \right)` approach more since it scales dynamically. Lastly I also noted that it seems to not have an understanding of matrices and struggles when there are multiple fractions inside other fractions (equations with a lot of layers in other words). There is some part in the documentation about training the model pix2tex uses yourself, so maybe that is something to play with in the future if I want to try to change to model to my preferences.
