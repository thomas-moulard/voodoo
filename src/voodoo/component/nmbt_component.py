import logging, os, time, unittest

import nmbt as _nmbt

def make_nmbt_init_data(environment_path, bank, image, tracker_count):
    arg = _nmbt.NmbtInitData()
    arg.defaultDirectory = environment_path
    arg.imageBank = bank
    arg.cameraName = image # FIXME: oops, wrong field name.
    arg.maxTrackers = tracker_count
    return arg

def make_nmbt_tracker_init_data(tracker_id, model_name, env_tracker_id):
    arg = _nmbt.NmbtTrackerInitData()
    arg.tracker_id = tracker_id
    arg.model_name = model_name
    arg.env_tracker_id = env_tracker_id
    return arg

class Nmbt:
    def __init__(self, genom):
        self.genom = genom
        self.logger = logging.getLogger('voodoo.component.nmbt')

    def __enter__(self):
        import voodoo.middleware.genom as genom
        self.start()

        # Wait for the component to start.
        while not genom.module_ready('nmbt'):
            time.sleep(0.1)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
        return self

    def start(self):
        self.genom.startComponent('nmbt')

    def stop(self):
        self.genom.stopComponent('nmbt')

    def init(self, environment_path, bank, image, tracker_count):
        self.logger.info("initialize module")
        arg = make_nmbt_init_data(environment_path, bank, image, tracker_count)
        _nmbt.Init(arg)

    def init_tracker_from_file(self, tracker_id, model_name, env_tracker_id):
        self.logger.info("initialize tracker from file")
        arg = make_nmbt_tracker_init_data(tracker_id, model_name, env_tracker_id)
        _nmbt.InitTrackerFomrFile(arg)


class basicTest(unittest.TestCase):
    def test(self):
        import voodoo.component.viam_component as viam
        import voodoo.middleware.genom as genom

        environment_path = os.getenv("HOME") \
            + "/profiles/default-i386-linux-fedora-12/install/unstable/share/hpp-environment"
        bank = 'b'
        camera = 'c'
        image = 'i'
        rectification = 'rectification'
        calibration_file = "/tmp/bottom-left.data"
        video_sequence = "file:/home/tmoulard/odo-ok/image%04d.ppm"
        tracker_count = 5

        print "START"
        with genom.Genom () as g:
            print "Genom started..."
            with viam.Viam(g) as v:
                print "Viam started..."
                with Nmbt(g) as nmbt:
                    print "Nmbt started..."
                    try:
                        v.driver_load("file")
                        v.camera_create(camera, video_sequence)
                        v.bank_create(bank,
                                      viam.ImageUpdate.DOUBLE_BUFFERING,
                                      viam.Active.ENABLE)
                        v.bank_add_camera(bank, camera, image)
                        v.camera_set_hw_mode(camera,
                                             viam.HwSize._640x480,
                                             viam.HwFmt.MONO8,
                                             viam.HwCrop.FIXED,
                                             viam.HwFps._30,
                                             viam.HwTrigger.INTERNAL)
                        v.calibration_io(bank, viam.IO.LOAD, calibration_file)
                        v.push_geo_filter(rectification, image,
                                          viam.Filter.RECTIFY,
                                          viam.FilterMethod.SOFTWARE,
                                          viam.FilterAutomode.MANUAL,
                                          0., 0., 1., 1., 1., 1)

                        v.init()
                        v.configure(bank)
                        v.display(bank, image, viam.OnOff.ON, viam.OnOff.ON,
                                  0, 0)
                        v.acquire(bank, 1)

                        nmbt.init(environment_path, bank, image, tracker_count)

                    except RuntimeError as e:
                        print "EXCEPTION: %s" % str(e)
                    except Exception as e:
                        print "UNKNOWN EXCEPTION: %s" % str(e)
                    except:
                        print "UNKNOWN EXCEPTION"
                    finally:
                        print "END TEST"
        print "END"

__all__ = ["Nmbt"]

if __name__ == "__main__":
    import doctest
    logging.basicConfig (level=logging.DEBUG)
    unittest.main()
