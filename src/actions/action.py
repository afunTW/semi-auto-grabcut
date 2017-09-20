"""
Based on src.view.template.MothViewerTemplate() to bind the action and widget
"""
import logging
import sys

import cv2

sys.path.append('../..')
from src import tkconfig
from src.actions.keyboard import MothKeyboardHandler
from src.actions.detector import TemplateDetector
from src.support.profiling import func_profiling

LOGGER = logging.getLogger(__name__)
STATE_DETECTED = 'detected'

class MothActionsTemplate(MothKeyboardHandler):
    def __init__(self):
        super().__init__()
        self.panel_image_state = []

        # default binding
        self.root.bind(tkconfig.KEY_UP, self.switch_to_previous_image)
        self.root.bind(tkconfig.KEY_DOWN, self.switch_to_next_image)

        # default binding: detector
        self.checkbtn_manual_detect.configure(command=self._invoke_manual_detect)
        self.checkbtn_template_detect.configure(command=self._invoke_template_detect)
        self._sync_detection()

    # unique the element in list
    def _unique(self, l):
        return list(set(l))

    # render manual detector option
    def _invoke_manual_detect(self):
        if self.checkbtn_manual_detect.instate(['selected']):
            self.val_template_detect.set(False)
            self._sync_detection()
        elif self.checkbtn_manual_detect.instate(['!selected']):
            pass

    # render template detector option
    def _invoke_template_detect(self):
        if self.checkbtn_template_detect.instate(['selected']):
            self.val_manual_detect.set(False)
            self._sync_detection()
        elif self.checkbtn_template_detect.instate(['!selected']):
            pass

    # detect and clear image when detect option was selected
    def _sync_detection(self):
        is_manual = self.checkbtn_manual_detect.instate(['selected'])
        is_template = self.checkbtn_template_detect.instate(['selected'])

        if (is_manual or is_template) and STATE_DETECTED not in self.panel_image_state:
            if self.image_template is not None:
                if self.detector is None:
                    self.detector = TemplateDetector(self.image_path_template, self.current_image_path)

                target_h, target_w, _ = self.image_panel.shape
                x, y, w, h = self.detector.detect_template()
                self.image_panel[y:y+h, x:x+w, :] = 255

                possible_rects = self.detector.detect_rectangle((0, y, target_w, target_h-y))
                for rect in possible_rects:
                    _x, _y, _w, _h = rect
                    self.image_panel[_y:_y+_h, _x:_x+_w, :] = 255

                # # visualize template
                # cv2.rectangle(self.image_panel, (x, y), (x+w, y+h), (0,0,255),2)
                # for rect in possible_rects:
                #     _x, _y, _w, _h = rect
                #     cv2.rectangle(self.image_panel, (_x, _y), (_x+_w, _y+_h), (255,0,0),2)

                self._update_image()

        self.root.after(100, self._sync_detection)

if __name__ == '__main__':
    """testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )
    from glob import glob
    from inspect import currentframe, getframeinfo
    from os import path
    _FILE = path.abspath(getframeinfo(currentframe()).filename)
    TEMPLATE_IMG = path.abspath('../../image/10mm.png')
    SAMPLE = path.abspath('../../image/sample/')
    SAMPLE_IMGS = sorted([i for i in glob(path.join(SAMPLE, '*.jpg'))])

    action = MothActionsTemplate()
    action.input_template(TEMPLATE_IMG)
    action.input_image(*SAMPLE_IMGS)
    action.mainloop()
