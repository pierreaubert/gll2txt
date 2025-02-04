"""Extract speaker from GLL files"""

import logging
import os
import time
import zipfile

import pywinauto as win

from logger import log_message

# constants
debug = False
ease_full = "C:\\Program Files (x86)\\AFMG\\EASE GLLViewer\\EASE GLLViewer.exe"
output_dir = "C:\\Users\\pierre\\Documents"


def dump(widget) -> None:
    """Small debug layer"""
    if not debug:
        return
    log_message(
        logging.DEBUG,
        "======================================================================",
    )
    log_message(logging.DEBUG, widget.element_info)
    try:
        properties = widget.get_properties()
        log_message(
            logging.DEBUG,
            "- properties ---------------------------------------------------------",
        )
        print(properties)
    except AttributeError:
        pass
    try:
        children = widget.get_children()
        log_message(
            logging.DEBUG,
            "- children -----------------------------------------------------------",
        )
        for child in children:
            dump(child)
    except AttributeError:
        pass
    if isinstance(widget, dict):
        log_message(
            logging.DEBUG,
            "- keys if dict--------------------------------------------------------",
        )
        keys = widget.keys()
        for key in keys:
            dump(widget[key])
    try:
        items = widget.item_texts()
        log_message(
            logging.DEBUG,
            "- item texts ---------------------------------------------------------",
        )
        log_message(logging.DEBUG, items)
    except Exception:
        pass
    try:
        items = widget.print_control_identifier()
        log_message(
            logging.DEBUG,
            "- control identifiers ------------------------------------------------",
        )
        log_message(logging.DEBUG, items)
    except Exception:
        pass


def load_gll(app, gll_file: str):
    openGLLFile = app.OpenGLLFile
    openGLLFile.wait("visible")
    openGLLFile.set_focus()
    openGLLFile.type_keys(gll_file, with_spaces=True)
    openGLLFile.type_keys("{ENTER}")


def load_config(app, view, config_file: str | None):
    if config_file is None:
        return
    view.wait("visible")
    view.type_keys("%fc")
    openConfigFile = app.OpenGLLConfigurationFile
    openConfigFile.wait("visible")
    openConfigFile.set_focus()
    openConfigFile.type_keys(config_file, with_spaces=True)
    openConfigFile.type_keys("{ENTER}")


def set_parameters_balloon(parameters):
    if debug:
        balloon = parameters["Balloon Parameters"]
        dump(balloon)

    resolution = parameters["Resolution :ComboBox"]
    angles = {a: i for i, a in enumerate(resolution.item_texts())}
    resolution.select(angles["Intermediate (5°)"])

    distance = parameters["Distance [m] :ComboBox"]
    if debug:
        dump(distance)
    meters = {a: i for i, a in enumerate(distance.item_texts())}
    distance.select(meters["10"])


def set_parameters_air_properties(parameters):
    if debug:
        air_properties = parameters["Air Properties"]
        dump(air_properties)

    enable_air_attenuation = parameters["Enable Air Attenuation"]
    if debug:
        dump(enable_air_attenuation)

    # not a checkbox
    enable_air_attenuation.click()


def set_parameters_input_signal(parameters):
    if debug:
        input_signal = parameters["Input Signal"]
        dump(input_signal)

    aes2 = parameters["AES2 Broadband (Pink Noise)Button"]
    if debug:
        dump(aes2)
    aes2.check_by_click()


def set_parameters(app):
    parameters = app.CalculationParameters
    parameters.wait("visible")
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
    os.makedirs(output_dir, mode=0o755, exist_ok=True)
    dir = "{}\\{}".format(output_dir, speaker_name)
    os.makedirs(dir, mode=0o755, exist_ok=True)
    return dir.replace("/", "\\")


def build_spl_filename(
    output_dir: str, speaker_name: str, meridian: str, parallel: str
) -> str:
    return "{0}\\{1}\\{1} -M{2}-P{3}.txt".format(
        output_dir, speaker_name, meridian[:-1], parallel[:-1]
    ).replace("/", "\\")


def build_sensitivity_filename(output_dir: str, speaker_name: str) -> str:
    return "{0}\\{1}\\{1} - sensitivity.txt".format(output_dir, speaker_name).replace(
        "/", "\\"
    )


def build_maxspl_filename(output_dir: str, speaker_name: str) -> str:
    return "{0}\\{1}\\{1} - maxSPL.txt".format(output_dir, speaker_name).replace(
        "/", "\\"
    )


def build_zipfilename(output_dir: str, speaker_name: str) -> str:
    return "{}\\{}.zip".format(output_dir, speaker_name).replace("/", "\\")


def extract_spl(
    app,
    view,
    output_dir,
    speaker_name,
):
    # go to graphs -> frequency spectrum
    app.wait_cpu_usage_lower(threshold=5)
    view.wait("visible")
    view.type_keys("^+F")
    time.sleep(1)

    # got the 2 boxes
    wm = view["Meridian : ComboBox"]
    wp = view["Parallel : Combobox"]
    if debug:
        dump(wm)
        dump(wp)

    # angles we want for a spinorama
    meridians = get_meridians()
    parallels = get_parallels()

    # export window
    export = app["Export Graph Data"]

    for m in meridians:
        for p in parallels:
            output_file = build_spl_filename(output_dir, speaker_name, m, p)
            if os.path.exists(output_file):
                log_message(
                    logging.INFO,
                    "Skipping medidian {} and parallel {} for {}".format(
                        m, p, speaker_name
                    ),
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
            log_message(
                logging.INFO,
                "Saved medidian {} and parallel {} for {}".format(m, p, speaker_name),
            )
            # to prevent the windows app from crashing
            app.wait_cpu_usage_lower(threshold=5)


def extract_sensitivity(
    app,
    view,
    output_dir,
    speaker_name,
):
    # go to graphs -> frequency spectrum
    app.wait_cpu_usage_lower(threshold=5)
    view.wait("visible")
    view.type_keys("^+S")

    export = app["Export Graph Data"]

    # go to File -> Send Table To -> File
    app.wait_cpu_usage_lower(threshold=5)
    view.type_keys("%ftf")
    export.wait("visible")
    # copy filename
    export.type_keys("%n{BACKSPACE}")
    sensitivity_file = build_sensitivity_filename(output_dir, speaker_name)
    export.type_keys(sensitivity_file, with_spaces=True)
    export.type_keys("{ENTER}")
    export.wait_not("visible")
    app.wait_cpu_usage_lower(threshold=5)


def extract_maxspl(
    app,
    view,
    output_dir,
    speaker_name,
):
    # go to graphs -> frequency spectrum
    app.wait_cpu_usage_lower(threshold=5)
    view.wait("visible")
    view.type_keys("^+M")

    export = app["Export Graph Data"]

    # go to File -> Send Table To -> File
    app.wait_cpu_usage_lower(threshold=5)
    view.type_keys("%ftf")
    export.wait("visible")
    # copy filename
    export.type_keys("%n{BACKSPACE}")
    maxspl_file = build_maxspl_filename(output_dir, speaker_name)
    export.type_keys(maxspl_file, with_spaces=True)
    export.type_keys("{ENTER}")
    export.wait_not("visible")
    app.wait_cpu_usage_lower(threshold=5)


def check_all_files(
    output_dir: str,
    speaker_name: str,
) -> bool:
    meridians = get_meridians()
    parallels = get_parallels()

    for m in meridians:
        for p in parallels:
            f = build_spl_filename(output_dir, speaker_name, m, p)
            if not os.path.exists(f):
                return False

    if not os.path.exists(build_sensitivity_filename(output_dir, speaker_name)):
        return False

    return True


def generate_zip(
    output_dir: str,
    speaker_name: str,
) -> bool:
    if not check_all_files(output_dir, speaker_name):
        log_message(logging.ERROR, "Not all files have been generated")
        return False
    zfname = build_zipfilename(output_dir, speaker_name)
    if os.path.exists(zfname):
        log_message(logging.INFO, "Nothing to do {} already exist!".format(zfname))
        return True
    with zipfile.ZipFile(zfname, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        meridians = get_meridians()
        parallels = get_parallels()
        for m in meridians:
            for p in parallels:
                f = build_spl_filename(output_dir, speaker_name, m, p)
                zf.write(f)
        s = build_sensitivity_filename(output_dir, speaker_name)
        zf.write(s)
        m = build_maxspl_filename(output_dir, speaker_name)
        zf.write(m)
    return True


def extract_speaker(
    output_dir: str, speaker_name: str, gll_file: str, config_file: str | None
) -> bool:
    log_message(logging.INFO, f"Processing speaker: {speaker_name}")
    log_message(logging.INFO, f"GLL File: {gll_file}")
    # Create speaker directory
    speakerdir = build_speakerdir(output_dir, speaker_name)
    log_message(logging.INFO, f"Output directory: {speakerdir}")

    # Rest of the function remains the same, but use log_message instead of print
    if not check_all_files(output_dir, speaker_name):
        app = win.Application(backend="win32").start(ease_full)
        load_gll(app, gll_file)
        view = app["ViewGLL: NXW 44-A [{}]".format(gll_file)]
        load_config(app, view, config_file)
        view.type_keys("{F5}")
        set_parameters(app)
        extract_spl(app, view, output_dir, speaker_name)
        extract_sensitivity(app, view, output_dir, speaker_name)
        extract_maxspl(app, view, output_dir, speaker_name)
        view.close()

    if generate_zip(output_dir, speaker_name):
        log_message(logging.INFO, "Success for {}!".format(speaker_name))
        return True

    log_message(logging.WARNING, "Failed for {}!".format(speaker_name))
    return False


if __name__ == "__main__":
    to_be_processed = (
        # name of speaker,        name of gll file        name of config file
        ("RCF NXW 44-A", "Z:\\GLL\\RCF\\GLL-NXW 44-A.gll", None),
        ("RCF NX 945-A", "Z:\\GLL\\RCF\\GLL-NX 945-A.gll", None),
        ("RCF NX 932-A", "Z:\\GLL\\RCF\\GLL-NX 932-A.gll", None),
        (
            "Alcons Audio LR7",
            "Z:\\GLL\\Alcons Audio\\LR7-V1_32.gll",
            "Z:\\GLL\\Alcons Audio\\Alcons Audio LR7 - single.xglc",
        ),
    )

    # Timings.slow()
    for speaker_name, gll_file, config_file in to_be_processed:
        extract_speaker(output_dir, speaker_name, gll_file, config_file)
