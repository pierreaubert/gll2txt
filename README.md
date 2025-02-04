# gll2txt
Process GLL files and extract data into text files

Note that the level of quality is *alpha*.

# Ideas

Since exporting data in the EASE software is a manual process, extracting lots of information from a GLL file is an annoying process.
The program run the automation for you and extract quickly:

- 72 measurements (36 horizontals and 36 verticals every 10 degrees)
- sensitity and max spl

# How it works?

This is a python script running on Windows.

- Ease software is currently 1.1.52.241. If you change the version, you may have to adapt the script.
- Use a recent version of Python (>3.12). It should work with older versions but that's untested.
- The Ease app may crash when running too fast. The script is designed to be relaunched and will pick up after the previous crash.

There is some tests but not enough. It works in Windows 11 running in a ARM VM running on a Mac. I do not have a Windows machine to test it better.

# How to use?

Installation is easy:
```
pip3 install -U -r requirements.txt
```

and you are good to go.

Now just start the app:
```
python3 .\app.py
```

A Windows binary will come soon.

# History

The first version of this from 2022 used to be written with Microsoft PowerAutomate. I didnt pay the license for the pro version and I was not able to export a copy of the script to others. In 2025, I took a few hours to port the script to Python and opensource it. It is faster and more reliable. Since it is also much simpler, it is easier to debug and adapt to new version of EASE software.

# On gen AI

I wrote the windows automation manually but the app itself has been written with an AI assistant and Windsurf as an editor. AI did incredible progress in 2024 but we are not yet there:
- you cannot trust anything written by the tool: it can create a mess very easily.
- code quality is crap, very verbose with little factorisation
- isolation of features and UI is not understood
- need to babysit all the time: new code breaks test, does not pass ruff --check, is inconsistent etc
- I have 0 confidence it is working properly: it works well enough for a prototype and can get the job done with a few iterations.

Conclusion: ok for prototyping

Hope you enjoy it!
