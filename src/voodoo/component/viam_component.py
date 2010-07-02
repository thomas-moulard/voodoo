import logging, os, time, unittest

import viam as _viam

import voodoo.util

ImageUpdate = voodoo.util.enum (('', 'SINGLE_BUFFERING', 'DOUBLE_BUFFERING'))
Active = voodoo.util.enum (('DISABLE', 'ENABLE'))

HwCrop = voodoo.util.enum (('FIXED', 'CROP'))
HwSize = voodoo.util.enum (('INVALID',
                            '_160x120',
                            '_320x240',
                            '_512x384',
                            '_640x480',
                            '_800x600',
                            '_1024x768',
                            '_1280x960',
                            '_1600x1200'))

HwFmt = voodoo.util.enum (('INVALID',
                           'MONO8', 'MONO16',
                           'YUV411', 'YUV422', 'YUV444',
                           'RGB888'))

HwFps = voodoo.util.enum (('INVALID',
                           '_1_875', '_3_75', '_7_5',
                           '_15', '_30', '_60', '_120', '_240'))

HwTrigger = voodoo.util.enum (('INVALID', 'INTERNAL',
                               'MODE0_HIGH', 'MODE0_LOW',
                               'MODE1_LOW', 'MODE1_HIGH'))

IO = voodoo.util.enum (('LOAD', 'SAVE'))

OnOff = voodoo.util.enum (('OFF', 'ON'))

# /!\ FIXME: this is only valid if viam-libs is compiled with opencv support !!
# Filters id changes if support is disabled.
Filter = voodoo.util.enum ((
        'NONE',
        'FORMAT',
        'SUBSAMPLE',
        'SCALE',
        'DISTORT',
        'RECTIFY',
        'BRIGHTNESS',
        'EXPOSURE',
        'SHARPNESS',
        'GAIN',
        'SHUTTER',
        'WHITE_BALANCE',
        'HUE',
        'SATURATION',
        'GAMMA',
        'TEMPERATURE',
        'ZOOM',
        'FOCUS',
        'LOG'
        ))

FilterMethod = voodoo.util.enum ((
        'INVALID',
        'OFF',
        'HARDWARE',
        '',
        'SOFTWARE'))

FilterAutomode = voodoo.util.enum ((
        'INVALID',
        'MANUAL',
        'HARDWARE_AUTO',
        '',
        'HARDWARE_ONE_PUSH',
        '', '', '',
        'SOFTWARE_AUTO',
        '', '', '', '', '', '', '',
        'SOFTWARE_ONE_PUSH'))

def make_viam_id(str):
    res = _viam.ViamId()
    res.id = str
    return res

def make_viam_camera_create(name, uid):
    res = _viam.ViamCameraCreate()
    res.name = make_viam_id(name)
    res.uid = uid
    return res

def make_viam_bank_create(name, image_update, active):
    res = _viam.ViamBankCreate()
    res.name = make_viam_id(name)
    res.buffering = image_update
    res.tags = active
    return res

def make_viam_bank_add_camera(bank, camera, name):
    res = _viam.ViamBankAddCamera()
    res.bank = make_viam_id(bank)
    res.camera = make_viam_id(camera)
    res.name = make_viam_id(name)
    return res

def make_viam_hwmode_t(size, format, crop, fps, trigger):
    res = _viam.viam_hwmode_t()
    res.size = size
    res.format = format
    res.crop = crop
    res.fps = fps
    res.trigger = trigger
    return res

def make_viam_hw_mode(camera, mode):
    res = _viam.ViamHWMode ()
    res.camera = make_viam_id (camera)
    res.mode = mode
    return res

def make_viam_calibration_io(bank, op, file):
    res = _viam.ViamCalibrationIO()
    res.bank = make_viam_id(bank)
    res.op = op
    res.file = make_viam_id(file)
    return res

def make_viam_geo_filter(filter, image, type, method, automode,
                         left, top, right, bottom, toWidth, toHeight):
    res = _viam.ViamGeoFilter()
    res.filter = make_viam_id(filter)
    res.image = make_viam_id(image)
    res.type = type
    res.method = method
    res.automode = automode
    (res.left, res.top, res.right, res.bottom) = (left, top, right, bottom)
    (res.toWidth, res.toHeight) = (toWidth, toHeight)
    return res

def make_viam_acquire(bank, n):
    res = _viam.ViamAcquire()
    res.bank = make_viam_id(bank)
    res.n = n
    return res

def make_viam_display(bank, image, enable, vtag, width, height):
    res = _viam.ViamDisplay()
    res.bank = make_viam_id(bank)
    res.image = make_viam_id(image)
    res.enable = enable
    res.vtag = vtag
    res.width = width
    res.height = height
    return res


class Viam:
    def __init__(self, genom):
        self.genom = genom
        self.logger = logging.getLogger('voodoo.component.viam')

    def __enter__(self):
        import voodoo.middleware.genom as genom

        self.start()

        # Wait for the component to start.
        while not genom.module_ready('viam'):
            time.sleep(0.1)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
        return self

    def start(self):
        self.genom.startComponent('viam')

    def stop(self):
        self.genom.stopComponent('viam')

    def driver_load(self, driver):
        self.logger.info("loading driver %s" % driver)
        _viam.DriverLoad(make_viam_id(driver))

    def camera_create(self, name, uid):
        self.logger.info("creating camera %s with uid %s" % (name, uid))
        arg = make_viam_camera_create(name, uid)
        _viam.CameraCreate(arg)

    def bank_create(self, name, image_update, active):
        self.logger.info("creating bank %s (%s %s)" % (name, image_update, active))
        arg = make_viam_bank_create(name, image_update, active)
        _viam.BankCreate(arg)

    def bank_add_camera(self, bank, camera, name):
        self.logger.info("add camera %s to bank %s using name %s" % (camera, bank, name))
        arg = make_viam_bank_add_camera(bank, camera, name)
        _viam.BankAddCamera(arg)


    def camera_set_hw_mode(self, camera, size, format, crop, fps, trigger):
        self.logger.info("set hardware mode for camera %s (%s, %s, %s, %s, %s)"
                         % (camera, size, format, crop, fps, trigger))
        mode = make_viam_hwmode_t(size, format, crop, fps, trigger)
        arg = make_viam_hw_mode(camera, mode)
        _viam.CameraSetHWMode(arg)

    def calibration_io(self, bank, op, file):
        self.logger.info("set calibration I/O for bank %s (action = %s, file = %s)"
                         % (bank, op, file))
        arg = make_viam_calibration_io(bank, op, file)
        _viam.CalibrationIO(arg)

    def push_geo_filter(self, filter, image, type, method, automode,
                        left, top, right, bottom, toWidth, toHeight):
        self.logger.info("push geo filter")
        arg = make_viam_geo_filter(filter, image, type, method, automode,
                                   left, top, right, bottom, toWidth, toHeight)
        _viam.PushGeoFilter(arg)

    def init(self):
        self.logger.info("init")
        _viam.Init()

    def configure(self, bank):
        self.logger.info("configure")
        arg = make_viam_id(bank)
        _viam.Configure(arg)

    def acquire(self, bank, n):
        self.logger.info("acquire %s image(s) on bank %s" % (n, bank))
        arg = make_viam_acquire(bank, n)
        _viam.Acquire(arg)

    def display(self, bank, image, enable, vtag, width, height):
        self.logger.info("display")
        arg = make_viam_display(bank, image, enable, vtag, width, height)
        _viam.Display(arg)



class basicTest(unittest.TestCase):
    def test(self):
        import voodoo.middleware.genom as genom

        bank = 'b'
        camera = 'c'
        image = 'i'
        rectification = 'rectification'
        calibration_file = "/tmp/bottom-left.data"
        video_sequence = "file:/home/tmoulard/odo-ok/image%04d.ppm"

        print "START"
        with genom.Genom () as g:
            print "Genom started..."
            with Viam(g) as v:
                print "Viam started..."
                try:
                    v.driver_load("file")
                    v.camera_create(camera, video_sequence)
                    v.bank_create(bank, ImageUpdate.DOUBLE_BUFFERING, Active.ENABLE)
                    v.bank_add_camera(bank, camera, image)
                    v.camera_set_hw_mode(camera,
                                         HwSize._640x480,
                                         HwFmt.MONO8,
                                         HwCrop.FIXED,
                                         HwFps._30,
                                         HwTrigger.INTERNAL)
                    v.calibration_io(bank, IO.LOAD, calibration_file)
                    v.push_geo_filter(rectification, image,
                                      Filter.RECTIFY,
                                      FilterMethod.SOFTWARE,
                                      FilterAutomode.MANUAL,
                                      0., 0., 1., 1., 1., 1)

                    v.init()
                    v.configure(bank)
                    v.display(bank, image, OnOff.ON, OnOff.ON, 0, 0)
                    v.acquire(bank, 1)

                except RuntimeError as e:
                    print "EXCEPTION: %s" % str(e)
                except Exception as e:
                    print "UNKNOWN EXCEPTION: %s" % str(e)
                except:
                    print "UNKNOWN EXCEPTION"
                finally:
                    print "END TEST"
        print "END"

__all__ = ["Viam"]

if __name__ == "__main__":
    import doctest
    logging.basicConfig (level=logging.DEBUG)
    #doctest.testmod (verbose = True)
    unittest.main()
