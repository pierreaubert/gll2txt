"""Extract speaker from GLL files"""

import logging
import os
import sys
import time
import zipfile

try:
    import pywinauto as win  # noqa: F401
    from pywinauto.application import Application, WindowSpecification
    from pywinauto.controls.win32_controls import ComboBoxWrapper, ListBoxWrapper
except ModuleNotFoundError:
    pass


from logger import log_message

# constants
debug = False
default_ease_full = "C:\\Program Files (x86)\\AFMG\\EASE GLLViewer\\EASE GLLViewer.exe"
default_gll_output_dir = "C:\\Users\\pierre\\Documents\\GLL"


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

    if isinstance(widget, ComboBoxWrapper) or isinstance(widget, ListBoxWrapper):
        try:
            items = widget.item_texts()
            log_message(
                logging.DEBUG,
                "- item texts ---------------------------------------------------------",
            )
            log_message(logging.DEBUG, items)
        except Exception:
            pass

    if isinstance(widget, WindowSpecification):
        try:
            items = widget.print_control_identifier()
            log_message(
                logging.DEBUG,
                "- control identifiers ------------------------------------------------",
            )
            log_message(logging.DEBUG, items)
        except Exception:
            pass


def process_type_keys(input_keys: str) -> str:
    return input_keys.replace("+", "{+}")


def load_gll(app, gll_file: str):
    open_gll_file = app["OpenGLLFile"]
    open_gll_file.wait("visible")
    open_gll_file.set_focus()
    open_gll_file.type_keys(process_type_keys(gll_file), with_spaces=True)
    open_gll_file.type_keys("{ENTER}")


def load_config(app, view, config_file: str | None):
    if config_file is None:
        return
    view.wait("visible")
    view.type_keys("%fc")
    open_config_file = app["OpenGLLConfigurationFile"]
    open_config_file.wait("visible")
    open_config_file.set_focus()
    open_config_file.type_keys(
        process_type_keys(config_file).replace("/", "\\"), with_spaces=True
    )
    open_config_file.type_keys("{ENTER}")


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


def build_speaker_dir(
    output_dir: str, speaker_name: str, config_file: str | None
) -> str:
    dir = "{}\\{}".format(output_dir, speaker_name)
    if config_file is not None:
        dir = "{}-{}".format(dir, os.path.basename(config_file)[:-5])
    dir = dir.replace("/", "\\")
    os.makedirs(dir, mode=0o755, exist_ok=True)
    return dir


def build_spl_filename(
    output_dir: str,
    speaker_name: str,
    config_file: str | None,
    meridian: str,
    parallel: str,
) -> str:
    speaker_dir = build_speaker_dir(output_dir, speaker_name, config_file)
    return "{0}\\{1} -M{2}-P{3}.txt".format(
        speaker_dir, os.path.basename(speaker_dir), meridian[:-1], parallel[:-1]
    ).replace("/", "\\")


def build_sensitivity_filename(
    output_dir: str, speaker_name: str, config_file: str | None
) -> str:
    return "{0}\\{1} -sensitivity.txt".format(
        build_speaker_dir(output_dir, speaker_name, config_file),
        speaker_name,
    ).replace("/", "\\")


def build_maxspl_filename(
    output_dir: str, speaker_name: str, config_file: str | None
) -> str:
    return "{0}\\{1} -maxSPL.txt".format(
        build_speaker_dir(output_dir, speaker_name, config_file), speaker_name
    ).replace("/", "\\")


def build_zipfilename(
    output_dir: str, speaker_name: str, config_file: str | None
) -> str:
    speaker_dir = build_speaker_dir(output_dir, speaker_name, config_file)
    zipname = "{}\\{}".format(speaker_dir, speaker_name)
    if config_file is not None:
        config_suffix = os.path.basename(config_file)[:-5]
        zipname += "-" + config_suffix
    zipname += ".zip"
    return zipname.replace("/", "\\")


def extract_spl(
    app,
    view,
    output_dir,
    speaker_name,
    config_file,
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
            output_file = build_spl_filename(
                output_dir, speaker_name, config_file, m, p
            )
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
            export.type_keys(process_type_keys(output_file), with_spaces=True)
            export.type_keys("{ENTER}")
            export.wait_not("visible")
            log_message(
                logging.INFO,
                "Saved medidian {} and parallel {} for {}".format(m, p, speaker_name),
            )
            # to prevent the windows app from crashing
            app.wait_cpu_usage_lower(threshold=5)


def app_close(app):
    if app is not None:
        app.kill()


def view_close(view):
    pass
    # if view is not None:
    #    view.close()


def extract_sensitivity(app, view, output_dir, speaker_name, config_file):
    sensitivity_file = build_sensitivity_filename(output_dir, speaker_name, config_file)
    if os.path.exists(sensitivity_file):
        log_message(
            logging.DEBUG,
            "Skipping sensitivity for {} because it already exists".format(
                speaker_name
            ),
        )
        return
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
    export.type_keys(process_type_keys(sensitivity_file), with_spaces=True)
    export.type_keys("{ENTER}")
    export.wait_not("visible")
    app.wait_cpu_usage_lower(threshold=5)


def extract_maxspl(app, view, output_dir, speaker_name, config_file):
    maxspl_file = build_maxspl_filename(output_dir, speaker_name, config_file)
    if os.path.exists(maxspl_file):
        log_message(
            logging.DEBUG,
            "Skipping maxspl for {} because it already exists".format(speaker_name),
        )
        return
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
    export.type_keys(process_type_keys(maxspl_file), with_spaces=True)
    export.type_keys("{ENTER}")
    export.wait_not("visible")
    app.wait_cpu_usage_lower(threshold=5)


def check_all_files(
    output_dir: str, speaker_name: str, config_file: str | None
) -> bool:
    meridians = get_meridians()
    parallels = get_parallels()

    for m in meridians:
        for p in parallels:
            f = build_spl_filename(output_dir, speaker_name, config_file, m, p)
            if not os.path.exists(f):
                return False

    if not os.path.exists(
        build_sensitivity_filename(output_dir, speaker_name, config_file)
    ):
        return False

    if not os.path.exists(build_maxspl_filename(output_dir, speaker_name, config_file)):
        return False

    return True


def check_zip_file(output_dir: str, speaker_name: str, config_file: str | None) -> bool:
    zfname = build_zipfilename(output_dir, speaker_name, config_file)
    if os.path.exists(zfname):
        return True
    return False


def check_work(output_dir: str, speaker_name: str, config_file: str | None) -> bool:
    all_files = check_all_files(output_dir, speaker_name, config_file)
    zip_file = check_zip_file(output_dir, speaker_name, config_file)
    return all_files and zip_file


def generate_zip(output_dir: str, speaker_name: str, config_file: str | None) -> bool:
    if not check_all_files(output_dir, speaker_name, config_file):
        log_message(logging.ERROR, "Not all files have been generated")
        return False
    zfname = build_zipfilename(output_dir, speaker_name, config_file)
    if os.path.exists(zfname):
        return True
    with zipfile.ZipFile(zfname, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        meridians = get_meridians()
        parallels = get_parallels()
        for m in meridians:
            for p in parallels:
                f = build_spl_filename(output_dir, speaker_name, config_file, m, p)
                zf.write(f)
        s = build_sensitivity_filename(output_dir, speaker_name, config_file)
        zf.write(s)
        m = build_maxspl_filename(output_dir, speaker_name, config_file)
        zf.write(m)
    return True


def extract_speaker(
    output_dir: str, speaker_name: str, gll_file: str, config_file: str | None
) -> bool:
    """Extract all the data for a speaker.

    Args:
        output_dir: Directory where to save the extracted data
        speaker_name: Name of the speaker
        gll_file: Path to the GLL file
        config_file: Optional path to a config file

    Returns:
        bool: True if extraction was successful, False otherwise
    """
    if check_work(output_dir, speaker_name, config_file):
        log_message(logging.DEBUG, "Processing done for {}!".format(speaker_name))
        return True
    app = None
    try:
        app = Application(backend="win32").start(default_ease_full)
        log_message(logging.DEBUG, "Connected to EASE GLLViewer")
    except Exception as e:
        log_message(logging.ERROR, f"Could not connect to EASE GLLViewer: {str(e)}")
        return False

    view = None
    try:
        load_gll(app, gll_file)
        time.sleep(1)

        # Find the appropriate view
        view = app.window()

        if view is None:
            log_message(logging.WARNING, "Failed for {}!".format(speaker_name))
            app_close(app)
            return False

        # Verify we have the right window
        load_config(app, view, config_file)
        time.sleep(1)
        view.type_keys("{F5}")
        set_parameters(app)
        time.sleep(1)
        extract_spl(app, view, output_dir, speaker_name, config_file)
        extract_sensitivity(app, view, output_dir, speaker_name, config_file)
        extract_maxspl(app, view, output_dir, speaker_name, config_file)
        view_close(view)
        if generate_zip(output_dir, speaker_name, config_file):
            log_message(logging.DEBUG, "Success for {}!".format(speaker_name))
        app_close(app)
        return True
    except Exception as e:
        log_message(logging.ERROR, f"Error extracting speaker data: {str(e)}")

    view_close(view)
    app_close(app)
    return False


def main():
    to_be_processed = (
        # name of speaker,        name of gll file        name of config file
        (
            "Meyer Sound UP-4slim",
            "C:\\Users\\pierre\\Documents\\GLL\\Meyer Sound\\up-4slim.gll",
            None,
        ),
        (
            "RCF NXW 44-A",
            "C:\\Users\\pierre\\Documents\\GLL\\RCF\\GLL-NXW 44-A.gll",
            None,
        ),
        (
            "RCF NX 945-A",
            "C:\\Users\\pierre\\Documents\\GLL\\RCF\\GLL-NX 945-A.gll",
            None,
        ),
        (
            "RCF NX 932-A",
            "C:\\Users\\pierre\\Documents\\GLL\\RCF\\GLL-NX 932-A.gll",
            None,
        ),
        (
            "Alcons Audio LR7",
            "C:\\Users\\pierre\\Documents\\GLL\\Alcons Audio\\LR7-V1_32.gll",
            "C:\\Users\\pierre\\Documents\\GLL\\Alcons Audio\\Alcons Audio LR7 - single.xglc",
        ),
    )

    # Timings.slow()
    for speaker_name, gll_file, config_file in to_be_processed:
        extract_speaker(default_gll_output_dir, speaker_name, gll_file, config_file)


if __name__ == "__main__":
    sys.exit(main())
