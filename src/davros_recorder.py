#!/usr/bin/env python2
import cv2
import math
import yaml
import os
import time

from videocv import Videocv

class DavrosRecorder():
    """
    Records test data using the Davros vison robot.
    """
    def __init__(self):

        self.dirname = os.path.dirname(__file__)
        relative_path = "../config/recorder.yaml"
        config_path = os.path.join(self.dirname, relative_path)

        with open(config_path, 'r') as stream:
            self.config = yaml.load(stream)

        if self.config['recorder']['motor_control']:
            from connector import Connector

            self.conn = Connector(2, "/dev/ttyACM0", 2000000)

            self.conn.writeTorque(1, True)
            self.conn.writeTorque(2, True)

        self.rows = self.config['recorder']['rows']
        self.checkpoints = self.config['recorder']['checkpoints']

        source = self.config['recorder']['input']

        self.data_location = os.path.join(self.dirname, self.config['recorder']['output_path'])

        self.output_path = os.path.join(self.data_location, "record_{}/".format(str(int(time.time()))))

        if isinstance(source, basestring):
            root_folder = os.curdir
            source = root_folder + source
        
        self.video_getter = Videocv(source)
        self.video_getter.run()

        self.file_index = []

        self.record()

    def show_img(self, image):
        cv2.imshow("Record", image)

    def make_path(self, path):
        try:  
            os.makedirs(path)
        except OSError:  
            print("Creation of the directory %s failed" % path)
        else:  
            print ("Successfully created the directory %s " % path)

    def deg_to_val(self, angle):
        resolution = 4095
        return resolution - int((angle/(2*math.pi))*resolution)

    def drive(self, motor, value):
        if self.config['recorder']['motor_control']:
            self.conn.writeGoalPosition(1, value)
        else:
            print("Sim mode!!! Enable 'motor_control' in config to turn off.")
        print("Drive Motor {} | Value {}".format(motor, value))

    def save(self, row, checkpoint, value, angle, path, image):
        name = "image_{}.png".format(value)
        local_path = os.path.join("{}/{}/".format(row, checkpoint), name)
        save_path = os.path.join(path, name)
        data = {'row': row,
                'checkpoint': checkpoint,
                'angle': angle,
                'path': local_path}
        self.file_index.append(data)
        cv2.imwrite(save_path, image)

    def save_index(self):
        path = os.path.join(self.output_path, "index.yaml")
        with open(path, 'w') as outfile:
            yaml.dump(self.file_index, outfile, default_flow_style=False)

    def record_pano(self, row, checkpoint, path):
        steps = self.config['recorder']['yaw_steps']
        delta = (2*math.pi)/steps
        for step in range(steps):
            angle = step*delta
            value = self.deg_to_val(angle)
            self.drive(1,value)
            # Sleep until camera is positioned
            if step == 0:
                time.sleep(1)
            time.sleep(0.5)
            image = self.video_getter.frame
            self.show_img(image)
            k = cv2.waitKey(1)
            self.save(row, checkpoint, value, angle, path, image)

    def record(self):
        skipall = False
        for row in range(self.rows):
            print("------------- NEW ROW -------------")
            for checkpoint in range(self.checkpoints):
                if self.video_getter.ended or skipall:
                    break
                checkpoints_path = os.path.join(self.output_path, "{}/{}/".format(row, checkpoint))
                input_str = raw_input("Press enter for next checkpoint!")
                if input_str == "":
                    self.make_path(checkpoints_path)
                    self.record_pano(row, checkpoint, checkpoints_path)
                elif input_str == "s":
                    print("skiped ({}|{})".format(row, checkpoint))
                elif input_str == "e":
                    print("Exit")
                    skipall = True
                self.display_map(row, checkpoint)
        self.save_index()
        self.video_getter.stop()
        cv2.destroyAllWindows()

    def display_map(self, draw_row, draw_checkpoint):
        print(" " * max(0,(int(self.checkpoints/2) * 2 - 2)) + "GOAL 1")
        for row in range(self.rows):
            str_row = ""
            for checkpoint in range(self.checkpoints):
                if row == draw_row and checkpoint == draw_checkpoint:
                    symbol = "|X"
                else:
                    symbol = "|-"
                str_row = str_row + symbol
            print(str_row + "|")
        print(" " * max(0,(int(self.checkpoints/2) * 2 - 2)) + "GOAL 2")
    
    def rerecord_checkpoint(data_set, row, checkpoint):
        index_path = os.path.join(self.data_location, "index.yaml")
        with open(index_path, 'r') as stream:
            index = yaml.load(stream)

        for picture_data in index:
            if picture_data['row'] == row and picture_data['checkpoint'] == checkpoint:
                path = picture_data['path']
                # TODO remove file

        

if __name__ == "__main__":
    DavrosRecorder()