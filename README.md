# gll2txt
Process GLL files and extract data into text files

# Ideas

Since exporting data is manual, GLL files are annoying to manipulate.
The program run the automation for you and extract:

- 72 measurements (36 horizontals and 36 verticals every 10 degrees)
- more to come

# How it works?

This is a python script running on Windows. It is brittle:

- Ease software is currently 1.1.52.241. If you change the version, you may have to adapt the script.
- Use a recent version of Python (>3.12). It should work but untested with very old version too.
- The Ease app crashed when running too fast. The script is designed to be relaunched and will pick up after the previous crash.

There is no test yet. It works in Windows 11 running in a ARM VM running on a Mac. I do not have a Windows machine to test it better.

# How to use?

Installation is easy:
```
pip3 install -U -r requirements.txt
```

and you are good.

Now just start the app:
```
python3 .\app.py
```

A binary will come soon.

# History

The first version of this from 2022 used to be written with PowerAutomate. I didnt pay the license for the pro version and I was not able to export a copy of the script to others.
In 2025, I took a few hours to port the script to Python and opensource it.

Hope you enjoy it.
