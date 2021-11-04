import copy
import csv
import json
import os
import random


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

    def __init_member(self):
        self.__data = []
        self.__trial_size = 0

        self.__idx = 0
        self.__subject_name = ""

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

        # set subject name
        self.__subject_name = subject_name

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
                    self.__data.append([int(gain), int(loss), choice])

        # check trial size read
        size = len(self.__data)
        if size != self.__trial_size and size != self.__trial_size * 2:
            msg = "Invalid trial size!\n"
            msg += "Trial size must be {} or {}, but now {}".format(
                self.__trial_size,
                self.__trial_size * 2,
                size,
            )
            raise Exception(msg)

    def choose_trial_randomly(self):
        self.__idx = random.randint(1, len(self.__data))
        self.__idx -= 1

    def get_choosen_trial(self) -> list[int, int, str]:
        return copy.deepcopy(self.__data[self.__idx])

    def save_choosen_trial(self):
        file_name = "output/result/{}.csv".format(self.__subject_name)
        with open(file_name, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["gain", "loss", "choice"])
            writer.writerow(self.get_choosen_trial())


def main():
    # create output dir
    try:
        os.makedirs("output/result")
    except Exception:
        pass

    subject_name = input("Input subject name >> ")

    result = Result()
    result.read(subject_name)
    result.choose_trial_randomly()

    result.save_choosen_trial()
    print(result.get_choosen_trial())


if __name__ == "__main__":
    main()
