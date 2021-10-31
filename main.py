from sklearn.linear_model import LogisticRegression

import csv
import json
import os


def read_subject_id(subject_name: str) -> list[str]:
    json_open = open("subject_list.json", "r")
    subject_list_json_dict = json.load(json_open)

    id_list = []

    for subject_json_dict in subject_list_json_dict["subjects"]:
        id = subject_json_dict["id"]
        name = subject_json_dict["name"]

        if name == subject_name:
            id_list.append(id)

    if len(id_list) == 0:
        raise Exception("Subject is not found in subject list!")

    return id_list


class Result:
    def __init__(self):
        self.__init_member()
        self.__lr = LogisticRegression()

    def __init_member(self):
        self.__x = []
        self.__y = []
        self.__trial_size = 0

    def __init_trial_size(self):
        with open("setting.csv") as f:
            reader = csv.reader(f)
            rows = [row for row in reader]
            data = [int(col) for col in rows[1]]
            gain_min, gain_max, gain_step = data[0], data[1], data[2]
            loss_min, loss_max, loss_step = data[3], data[4], data[5]

            gain_size = (gain_max - gain_min) // gain_step + 1
            loss_size = (loss_max - loss_min) // loss_step + 1
            self.__trial_size = gain_size * loss_size

    def read(self, subject_name: str):
        # init
        self.__init_member()
        self.__init_trial_size()

        # get file name
        file_name_list = []
        id_list = read_subject_id(subject_name)
        for id in id_list:
            file_name = "{}_{}_result.csv".format(id, subject_name)
            file_name_list.append(file_name)

        # get file path
        file_path_list = []
        dir_name_list = os.listdir("output")
        for dir_name in dir_name_list:
            for file_name in file_name_list:
                file_path = "output/{}/{}".format(dir_name, file_name)
                if os.path.isfile(file_path):
                    file_path_list.append(file_path)

        # read data
        for file_path in file_path_list:
            with open(file_path) as f:
                reader = csv.reader(f)
                for num, gain, loss, choice in reader:
                    self.__x.append([int(gain), int(loss)])
                    self.__y.append(1 if choice == "accept" else 0)

        # check trial size read
        size = len(self.__x)
        if size != self.__trial_size and size != self.__trial_size * 2:
            msg = "Invalid trial size!\n"
            msg += "Trial size must be {} or {}, but now {}".format(
                self.__trial_size,
                self.__trial_size * 2,
                size,
            )
            raise Exception(msg)

    def fit(self):
        self.__lr.fit(self.__x, self.__y)

    def get_coef(self):
        return self.__lr.coef_

    def get_beta_gain(self):
        return self.__lr.coef_[0, 0]

    def get_beta_loss(self):
        return self.__lr.coef_[0][1]

    def get_lambda(self):
        beta_gain = self.get_beta_gain()
        beta_loss = self.get_beta_loss()
        return -beta_loss / beta_gain


def main():
    subject_name = input("Input subject name >> ")
    result = Result()
    result.read(subject_name)
    result.fit()
    print("Beta gain =", result.get_beta_gain())
    print("Beta loss =", result.get_beta_loss())
    print("Lambda =", result.get_lambda())


if __name__ == "__main__":
    main()
