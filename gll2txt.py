#!/usr/bin/env python3

from pprint import pp
import os
import time
import zipfile

import pywinauto as win
from pywinauto.timings import Timings

# constant
debug = True
ease_full = "C:\\Program Files (x86)\\AFMG\\EASE GLLViewer\\EASE GLLViewer.exe"
output_dir = "C:\\Users\\pierre\\Documents"



def dump(widget) -> None:
    """Small debug layer"""
    if not debug:
        return
    print("======================================================================")
    print(widget.element_info)
    try:
        properties = widget.get_properties()
        print("- properties ---------------------------------------------------------")
        pp(properties)
    except AttributeError:
        pass
    try:
        children = widget.get_children()
        print("- children -----------------------------------------------------------")
        for child in children:
            dump(child)
    except AttributeError:
        pass
    if isinstance(widget, dict):
        print("- keys if dict--------------------------------------------------------")
        keys = widget.keys()
        for key in keys:
            dump(widget[key])
    try:
        items = widget.item_texts()
        print("- item texts ---------------------------------------------------------")
        print(items)
    except Exception:
        pass
    try:
        items = widget.print_control_identifier()
        print("- control identifiers ------------------------------------------------")
        print(items)
    except Exception:
        pass


def load_gll(app, gll_file: str):
    openGLLFile = app.OpenGLLFile
    openGLLFile.wait("visible")
    openGLLFile.set_focus()
    openGLLFile.type_keys(gll_file, with_spaces=True)
    openGLLFile.type_keys("{ENTER}")


def set_parameters_balloon(parameters):
    if debug:
        alloon = parameters["Balloon Parameters"]
        # dump(balloon)

    resolution = parameters["Resolution :ComboBox"]
    angles = {a: i for i, a in enumerate(resolution.item_texts())}
    resolution.select(angles["Intermediate (5°)"])

    distance = parameters["Distance [m] :ComboBox"]
    dump(distance)
    meters = {a: i for i, a in enumerate(distance.item_texts())}
    distance.select(meters["10"])


def set_parameters_air_properties(parameters):
    if debug:
        air_properties = parameters["Air Properties"]
        dump(air_properties)

    enable_air_attenuation = parameters["Enable Air Attenuation"]
    dump(enable_air_attenuation)

    # not a checkbox
    enable_air_attenuation.click()


def set_parameters_input_signal(parameters):
    if debug:
        input_signal = parameters["Input Signal"]
        dump(input_signal)

    aes2 = parameters["AES2 Broadband (Pink Noise)Button"]
    dump(aes2)
    aes2.check_by_click()


def set_parameters(app):
    parameters = app.CalculationParameters

    set_parameters_balloon(parameters)
    set_parameters_air_properties(parameters)
    set_parameters_input_signal(parameters)

    ok_button = parameters["&OKButton"]
    ok_button.click()


def get_meridians() -> list[str]:
    return ["{}°".format(k) for k in range(0, 360, 90)]


def get_parallels() -> list[str]:
    return ["{}°".format(k) for k in range(0, 190, 10)]


def build_speakerdir(output_dir: str, speaker_name: str) -> str:
    dir = "{0}\\{1}".format(output_dir, speaker_name)
    if not os.path.exists(dir):
        os.mkdir(path=dir, mode=0o755)
    return dir


def build_outputfilename(
    output_dir: str, speaker_name: str, meridian: str, parallel: str
) -> str:
    return "{0}\\{1}\\{1} -M{2}-P{3}.txt".format(
        output_dir, speaker_name, meridian[:-1], parallel[:-1]
    )


def build_zipfilename(output_dir: str, speaker_name: str) -> str:
    return "{}\\{}.zip".format(output_dir, speaker_name)


def extract_spl(
    app : pywinauto.Application,
    view,
    output_dir,
    speaker_name,
):
    if not os.path.exists(output_dir):
        os.mkdir(path=output_dir, mode=0o644)

    # go to graphs -> frequency spectrum
    view.type_keys("^+F")
    time.sleep(1)

    # got the 2 boxes
    wm = view["Meridian : ComboBox"]
    wp = view["Parallel : Combobox"]
    dump(wm)
    dump(wp)

    # angles we want for a spinorama
    meridians = get_meridians()
    parallels = get_parallels()

    # export window
    export = app["Export Graph Data"]

    for m in meridians:
        for p in parallels:
            output_file = build_outputfilename(output_dir, speaker_name, m, p)
            if os.path.exists(output_file):
                print(
                    "Skipping medidian {} and parallel {} for {}".format(
                        m, p, speaker_name
                    )
                )
                continue
            # select m and p
            wm.select(m)
            wp.select(p)
            # go to File -> Send Table To -> File
            app.wait_cpu_usage_lower(threshold=5)
            view.type_keys("%ftf")
            export.wait("visible")
            # copy filename
            export.type_keys("%n{BACKSPACE}")
            export.type_keys(output_file, with_spaces=True)
            export.type_keys("{ENTER}")
            export.wait_not("visible")
            print("Saved medidian {} and parallel {} for {}".format(m, p, speaker_name))
            # to prevent the windows app from crashing
            app.wait_cpu_usage_lower(threshold=5)


def check_all_spl(
    output_dir: str,
    speaker_name: str,
) -> bool:
    meridians = get_meridians()
    parallels = get_parallels()

    for m in meridians:
        for p in parallels:
            f = build_outputfilename(output_dir, speaker_name, m, p)
            if not os.path.exists(f):
                return False
    return True


def generate_zip(
    output_dir: str,
    speaker_name: str,
) -> bool:
    if not check_all_spl(output_dir, speaker_name):
        print("Error not all SPL files generated")
        return False
    zfname = build_zipfilename(output_dir, speaker_name)
    if os.path.exists(zfname):
        print("Nothing to do {} already exist!".format(zfname))
        return True
    with zipfile.ZipFile(zfname, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        meridians = get_meridians()
        parallels = get_parallels()
        for m in meridians:
            for p in parallels:
                f = build_outputfilename(output_dir, speaker_name, m, p)
                zf.write(f)
    return True


def extract_speaker(
    output_dir,
    speaker_name,
    gll_file,
):
    build_speakerdir(output_dir, speaker_name)
    if not check_all_spl(output_dir, speaker_name):
        app = win.Application(backend="win32").start(ease_full)
        time.sleep(1)
        load_gll(app, gll_file)
        time.sleep(1)
        dump(app)
        view = app["ViewGLL: NXW 44-A [{}]".format(gll_file)]
        view.type_keys("{F5}")
        set_parameters(app)
        time.sleep(1)
        extract_spl(app, view, output_dir, speaker_name)
        app.close()

    if generate_zip(output_dir, speaker_name):
        print("Success for {}!".format(speaker_name))
    else:
        print("Failed for {}!".format(speaker_name))


if __name__ == "__main__":
    to_be_processed = (
        # name of speaker,        name of gll file
        ("RCF NXW 44-A", "Z:\\GLL\\RCF\\GLL-NXW 44-A.gll"),
        ("RCF NX 945-A", "Z:\\GLL\\RCF\\GLL-NX 945-A.gll"),
        ("RCF NX 932-A", "Z:\\GLL\\RCF\\GLL-NX 932-A.gll"),
    )

    # Timings.slow()
    for speaker_name, gll_file in to_be_processed:
        extract_speaker(output_dir, speaker_name, gll_file)
