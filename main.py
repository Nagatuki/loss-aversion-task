from flask import *
from datetime import datetime as dt

import csv
import json
import os
import random


class Task:
    def __init__(self):
        self.task_pos = 0
        self.task_list: list[tuple[int, int]] = []

    def init_task_list(self):
        gain_min, gain_max, gain_step = 0, 0, 0
        loss_min, loss_max, loss_step = 0, 0, 0

        with open("setting.csv") as f:
            reader = csv.reader(f)
            data = [row for row in reader]
            row = [int(col) for col in data[1]]
            gain_min, gain_max, gain_step = row[0], row[1], row[2]
            loss_min, loss_max, loss_step = row[3], row[4], row[5]

        # create task list
        gain_list = [val for val in range(gain_min, gain_max + 1, gain_step)]
        loss_list = [val for val in range(loss_min, loss_max + 1, loss_step)]

        pre_trial_list = []
        for gain in gain_list:
            for loss in loss_list:
                pre_trial_list.append((gain, loss))
                # pre_trial_list.append((gain, loss))  # それぞれ2回出てくる

        self.trial_num = 0
        self.trial_list = []

        size = len(pre_trial_list)
        while size > 0:
            pos = random.randint(0, size - 1)
            choose_trial = pre_trial_list.pop(pos)
            self.trial_list.append(choose_trial)
            size = len(pre_trial_list)

    def set_trial_list(self, trial_list: list[tuple[int, int]]):
        self.trial_list = trial_list

    def get_trial_list(self) -> list[tuple[int, int]]:
        return self.trial_list

    def get_trial(self) -> tuple[int, int]:
        if self.trial_num >= len(self.trial_list):
            return (0, 0)

        return self.trial_list[self.trial_num]

    def next(self):
        num = self.trial_num + 1
        self.trial_num = min(num, len(self.trial_list))

    def is_finish(self) -> bool:
        return self.trial_num >= len(self.trial_list)

    def get_current_num(self) -> int:
        return self.trial_num

    def set_current_num(self, num: int):
        self.trial_num = num


class TaskResult:
    def __init__(self) -> None:
        self.subjects = {}

        start_time_dt = dt.now()
        self.start_time = start_time_dt.strftime("%Y-%m-%d-%H-%M-%S")

        # create output dir
        try:
            os.makedirs("output/{}".format(self.start_time))
        except Exception:
            pass

    def set_result(
        self, id: str, name: str, num: int, gain: str, loss: str, choice: str
    ):
        if id not in self.subjects:
            self.subjects[id] = {}
            self.subjects[id]["name"] = name
            self.subjects[id]["result"] = []

        self.subjects[id]["result"].append((num, gain, loss, choice))

    def save(self, id: str):
        # output result as csv
        name = self.subjects[id]["name"]
        result = self.subjects[id]["result"]
        with open(
            "output/{}/{}_{}_result.csv".format(self.start_time, name, id),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f)
            for each in result:
                writer.writerow(each)

    def save_all(self):
        for key in self.subjects.keys():
            self.save(key)


class Subject:
    def __init__(self):
        self.id = ""
        self.name = ""
        self.task: Task = Task()

    def init_from_dict(self, subject_dict: dict):
        self.id = subject_dict["id"]
        self.name = subject_dict["name"]

        if "task" in subject_dict:
            self.task.set_current_num(subject_dict["task"]["current_num"])
            self.task.set_trial_list(subject_dict["task"]["task"])
        else:
            self.task.init_task_list()

    def to_dict(self) -> dict:
        ret_dict = dict()
        ret_dict["id"] = self.id
        ret_dict["name"] = self.name
        ret_dict["task"] = {
            "current_num": self.task.get_current_num(),
            "task": self.task.get_trial_list(),
        }
        return ret_dict

    def is_same_id(self, id: str) -> bool:
        return self.id == id

    def is_same_name(self, name: str) -> bool:
        return self.name == name

    def get_id(self) -> str:
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_task(self) -> Task:
        return self.task


class SubjectList:
    def __init__(self):
        self.subject_list: list[Subject] = []

    def load(self):
        json_open = open("subject_list.json", "r")
        subject_list_json_dict = json.load(json_open)

        for subject_json_dict in subject_list_json_dict["subjects"]:
            subject = Subject()
            subject.init_from_dict(subject_json_dict)
            self.subject_list.append(subject)

    def save(self):
        subject_list_json_dict = {
            "subjects": [subject.to_dict() for subject in self.subject_list]
        }

        json_open = open("subject_list.json", "w")
        json.dump(subject_list_json_dict, json_open, indent=4)

    def is_valid_id(self, id: str) -> bool:
        for subject in self.subject_list:
            if subject.is_same_id(id):
                return True
        return False

    def get_subject(self, id: str) -> Subject:
        for subject in self.subject_list:
            if subject.is_same_id(id):
                return subject
        return None

    def add_subject(self, id: str, name: str):
        new_dict = {"id": id, name: name}
        new_subject = Subject
        new_subject.init_from_dict(new_dict)
        self.subject_list.append(new_subject)


subject_list = SubjectList()
subject_list.load()
subject_list.save()
task_result = TaskResult()
app = Flask(__name__)


@app.route("/")
def main():
    return render_template("index.html")


@app.route("/login", methods=["GET"])
def login():
    id = request.args.get("id")

    # id validation
    if not subject_list.is_valid_id(id):
        return render_template("error.html")

    return render_template("description.html", id=id)


@app.route("/task_<id>")
def task(id):
    # id validation
    if not subject_list.is_valid_id(id):
        return render_template("error.html")

    # get task
    subject = subject_list.get_subject(id)
    subject_name = subject.get_name()
    task = subject.get_task()

    # choice
    choice = request.args.get("choice")
    last_trial_num = request.args.get("trial")

    if choice == "accept" or choice == "reject":
        trial_num = task.get_current_num()

        # trial check: avoid bugs related to reload
        if int(last_trial_num) == trial_num:
            trial = task.get_trial()
            task_result.set_result(
                id, subject_name, trial_num + 1, trial[0], trial[1], choice
            )
            task_result.save(id)

            # next trial
            task.next()
            subject_list.save()

    # all trials has been done
    if task.is_finish():
        return render_template("finish.html")

    # if next trial exist
    gain, loss = task.get_trial()
    trial_num = task.get_current_num()
    return render_template("task.html", trial=trial_num, id=id, gain=gain, loss=loss)


if __name__ == "__main__":
    # デバッグモード、localhost:8888 で スレッドオフで実行
    app.run(debug=True, host="0.0.0.0", port=8888, threaded=True)
