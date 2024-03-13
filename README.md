# SCIM Python Sync App Workshop
The purpose of this project is to provide a jumping off point for developing a python application
which is cabable of both sending and recieving SCIM messages with the goal of eventuall keeping
two cloud service providers in sync.

This project is part of a learning exercise.

## Environment
There are a couple ways to set up this workshop.

### Virtual Environment
If you prefer venv, you could set up with `requirements.txt`
While using virtual enviroment, you need to start jupyter notebook from the venv python module.
You can do that with

```
    $ python -m jupyter notebook
```
Or with the `run_notebook.sh`
```
    $ virtualenv env
    $ source env/bin/activate
    $ python -m pip install -r requirements.txt
    $ ./run_notebook.sh
```

### non-virtual python
If you already have jupter notebook installed and does not mind install module to your local python instance.
You can uses `requirements.txt` to install/update the requirement and start notebook from your terminal
```
    $ python3 -m pip install -r requirements.txt
    $ jupter notebook
```

### vs code
If you are vs code user, while open the notebook file in vs code. You can selete your python instance and select requirements.txt.
You can also run notebook directly from vscode.

