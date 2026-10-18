# Python Foundations: exercise workbooks

Exercise workbooks for Simmer's [Python Foundations](https://www.teamsimmer.com) course, part of the Complete Python for Data Analysts program.

Open a workbook from its link in the course. In Colab, choose **File → Save a copy in Drive** and work in your copy.

| Lesson | Workbook | Open |
|--------|----------|------|
| 8 | Rebuild your channel grouping in a notebook | [Open in Colab](https://colab.research.google.com/github/team-simmer/python-foundations/blob/main/lesson-08/8.1-channel-grouping.ipynb) |
| 8 | Load February's sessions both ways | [Open in Colab](https://colab.research.google.com/github/team-simmer/python-foundations/blob/main/lesson-08/8.2-load-sessions.ipynb) |
| 8 | Total social referrals by site | [Open in Colab](https://colab.research.google.com/github/team-simmer/python-foundations/blob/main/lesson-08/8.3-site-names.ipynb) |
| 8 | Build a channel report notebook from scratch | [Open in Colab](https://colab.research.google.com/github/team-simmer/python-foundations/blob/main/lesson-08/8-channel-report.ipynb) |
| 11 | Fix a colleague's summer sale notebook | [Open in Colab](https://colab.research.google.com/github/team-simmer/python-foundations/blob/main/lesson-11/11.1-summer-sale.ipynb) |
| 11 | Turn a colleague's notebook into a reusable report | [Open in Colab](https://colab.research.google.com/github/team-simmer/python-foundations/blob/main/lesson-11/11.2-campaign-report.ipynb) |
| 11 | Rescue a broken report | [Open in Colab](https://colab.research.google.com/github/team-simmer/python-foundations/blob/main/lesson-11/11-black-friday-report.ipynb) |
| 12 | Run the toolkit on 1,000 landing pages | [Open in Colab](https://colab.research.google.com/github/team-simmer/python-foundations/blob/main/lesson-12/12.4-landing-pages.ipynb) |

## Workbooks for your own computer

Lesson 10's workbooks run in JupyterLab and VS Code, in a uv project on your computer. Download each one, with its data, by running [get_files.py](lesson-10/get_files.py) with uv in the project's folder, as the topic page shows. It never replaces a file that's already there.

| Lesson | Workbook | Exercise name |
|--------|----------|---------------|
| 10 | Move your February notebook to your computer | `10.1` |
| 10 | Connect a notebook to your project's kernel | `10.2` |
| 10 | Compare two months of campaigns in VS Code | `10.3` |
| 10 | Get a provided notebook running in both tools | `final` |

## Check scripts

Lesson 9 happens on your own computer. Each exercise ends with a check that you run with uv from its URL, in the exercise's folder. The command is on the topic page. Read a script before you run it: the checks only read your project and run your script, and they don't change anything.

| Lesson | Exercise | Script |
|--------|----------|--------|
| 9 | Install uv and Python 3.13 on your computer | [check_python.py](lesson-09/check_python.py) |
| 9 | Turn your UTM parser into a script | [check_parse_utm.py](lesson-09/check_parse_utm.py) |
| 9 | Move your referral report into a project | [check_project.py](lesson-09/check_project.py) |
| 9 | Set up a project from a brief | [check_setup.py](lesson-09/check_setup.py) |

`tests/` and the Lesson checks workflow test the checks and the lesson 10 workbooks on Windows and macOS on every change and every Monday.

The workbooks and checks are built from the course's source files. Please don't send pull requests here.
